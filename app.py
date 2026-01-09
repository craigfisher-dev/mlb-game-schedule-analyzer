import streamlit as st
import time
import os
import logging
import warnings
import requests
import json

import calendar
from dotenv import load_dotenv
from supabase import create_client
import pandas
import numpy
import statsapi
from concurrent.futures import ThreadPoolExecutor

# ESPN API for team logos
ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams"

ALLSTAR_LOGO = "https://img.mlbstatic.com/mlb-images/image/upload/t_w372/v1752722808/mlb/bmrn9jjalqrz4ujd3zg7.png"

CURRENT_YEAR = 2026

# Set Sunday as first day of week
calendar.setfirstweekday(calendar.SUNDAY)

st.set_page_config("MLB Game Schedule Analyzer", layout="wide")

# Transforms a teams regular season schedule into 6 lists
# [March/April, May, June, July, August, September]
# Returns list: 
def convert_schedule(regular_season_schedule):
    new_month_schedule = [[], [], [], [], [], []]
    for game in regular_season_schedule:

        # Index 5:7 is the month in the date string
        # Example: 'game_date': '2026-03-27'

        # March/April   
        if game["game_date"][5:7] == "03" or game["game_date"][5:7] == "04":
            new_month_schedule[0].append(game)
        # May
        elif game["game_date"][5:7] == "05":
            new_month_schedule[1].append(game)
        # June
        elif game["game_date"][5:7] == "06" :
            new_month_schedule[2].append(game)
        # July
        elif game["game_date"][5:7] == "07":
            new_month_schedule[3].append(game)
        # August
        elif game["game_date"][5:7] == "08":
            new_month_schedule[4].append(game)
        # September
        elif game["game_date"][5:7] == "09":
            new_month_schedule[5].append(game)

    return new_month_schedule


# Filters schedule to regular season games only 
# (removes Spring Training, Post-Season, etc)
def team_regular_season_schedule(team_schedule):
    new_team_schedule = []
    for game in team_schedule:
        if game["game_type"] == "R":
            new_team_schedule.append(game)

    return new_team_schedule


# Fetches all 30 team schedules,
# Returns dict: {team_name: [games...]}
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_all_schedules():

    team_ids = []

    # Get all team IDs first
    all_teams = statsapi.get('teams', {'sportId': 1})  # sportId 1 = MLB
    team_ids = [(team['name'], team['id']) for team in all_teams['teams']]

    # Fetch all_season_schedule
    all_season_schedule = statsapi.schedule(season=CURRENT_YEAR)

    # Grabs All-Star-Game date
    allstar_date = None
    for game in all_season_schedule:
        if game.get("game_type") == "A":
            allstar_date = game["game_date"]
            break

    regular_season_schedule = {}

    for name, tid in team_ids:
        # Filter: keep only games where this team is home OR away
        team_games = [game for game in all_season_schedule if game['away_id'] == tid or game['home_id'] == tid]
        # Sort games chronologically by datetime
        team_games_sorted = sorted(team_games, key=lambda game: game['game_datetime'])
        # Filter to regular season only, then store under team name
        regular_season_schedule_games = team_regular_season_schedule(team_games_sorted)
        regular_season_schedule[name] = {
                                            "games": regular_season_schedule_games,
                                            "by_month": convert_schedule(regular_season_schedule_games),
                                            "allstar_date": allstar_date or f"{CURRENT_YEAR}-07-14"
                                        }

    return regular_season_schedule

# Returns list of URLs for all MLB team logos (transparent)
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_all_team_logos():
    response = requests.get(ESPN_API_URL)
    if response.status_code != 200:
        print("Failed to fetch ESPN team logos")
        return []
    
    # Turned it to json to be able to access it as a dictionary
    data = response.json()
    teams = data["sports"][0]["leagues"][0]["teams"]
    
    logo_map = {}

    # Loop through all teams and add in their logos
    for team in teams:
        # Transparent logos (href 4 on ESPNs API list)
        team_name = team["team"]["displayName"]
        logo_url = team["team"]["logos"][4]["href"]
        logo_map[team_name] = logo_url
    
    return logo_map
        

# Load schedules and logos in parallel for faster startup
with st.spinner("Loading..."):
    with ThreadPoolExecutor(max_workers=2) as executor:
        schedules_future = executor.submit(fetch_all_schedules)
        logos_future = executor.submit(fetch_all_team_logos)
        
        all_schedules = schedules_future.result()
        team_logo_map = logos_future.result()


# Shows the links collected from ESPNs API
# st.write(team_logos)

# This renders in the sidebar, even though it's not in a "with st.sidebar:" block
# Dropdown options (team names) pulled from schedule data (sorted A-Z)
st.sidebar.markdown("### 🔍 Team Search")
teamName = st.sidebar.selectbox("What team schedule would you like to look up?", options=sorted(all_schedules.keys()),index=None, placeholder="Pick a team")

# Title get replaced when team is selected
if teamName:
    st.markdown(f"<h1 style='text-align: center;'>{teamName} {CURRENT_YEAR} Schedule</h1>", unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align: center;'>MLB Game Schedule Analyzer</h1>", unsafe_allow_html=True)



# Helper function to process_month
def process_month(month_calendar, month_games, teamName, month_num, allstar_date=None):
    left_ptr = 0
    right_ptr = 0
    
    # Flatten to 1D
    month_flat = [day for week in month_calendar for day in week]

    while left_ptr < len(month_flat):
        if month_flat[left_ptr] == 0:
            month_flat[left_ptr] = (-1, None, None)  # Padding day
            left_ptr += 1

        elif right_ptr < len(month_games) and month_flat[left_ptr] == int(month_games[right_ptr]["game_date"][8:10]):
            home_team = month_games[right_ptr]["home_name"]
            away_team = month_games[right_ptr]["away_name"]
            teamPlaying = away_team if teamName == home_team else home_team
            is_home = True if teamName == home_team else False

            day_num = month_flat[left_ptr]
            month_flat[left_ptr] = (day_num, teamPlaying, is_home)  # (day, opponent, is_home)
            
            # Skip any additional games on the same day (doubleheaders)
            current_date = month_games[right_ptr]["game_date"]
            right_ptr += 1
            while right_ptr < len(month_games) and month_games[right_ptr]["game_date"] == current_date:
                right_ptr += 1
            
            left_ptr += 1
        else:
            day_num = month_flat[left_ptr]
            date_str = f"{CURRENT_YEAR}-{month_num:02d}-{day_num:02d}"
            if allstar_date and date_str == allstar_date:
                month_flat[left_ptr] = (day_num, "ALL_STAR", None)
            else:
                month_flat[left_ptr] = (day_num, None, None)  # No game
            left_ptr += 1

    # Reshape back to 2D
    return [month_flat[i:i+7] for i in range(0, len(month_flat), 7)]


def trim_empty_weeks(month_data, trim_start=False, trim_end=False):
    result = month_data[:]
    
    # Trim leading weeks with no games
    if trim_start:
        while result and all(opponent is None for day_num, opponent, is_home in result[0]):
            result = result[1:]
    
    # Trim trailing weeks with no games
    if trim_end:
        while result and all(opponent is None for day_num, opponent, is_home in result[-1]):
            result = result[:-1]
    
    return result

# If a team is chosen then display the teams schedule

# To access a team game 
# month[0-5]
# [0 = March/April, 1 = May, 2 = June, 3 = July, 4 = August, 5 = September]

# all_schedules[teamName]['by_month'][month][game_number]

def print_team_calendar(teamName):
    
    march_april_games = all_schedules[teamName]['by_month'][0]
    
    march_games = [g for g in march_april_games if g["game_date"][5:7] == "03"]
    april_games = [g for g in march_april_games if g["game_date"][5:7] == "04"]
    
    march = calendar.monthcalendar(year=CURRENT_YEAR, month=3)
    april = calendar.monthcalendar(year=CURRENT_YEAR, month=4)
    
    march_processed = process_month(march, march_games, teamName, 3)
    april_processed = process_month(april, april_games, teamName, 4)
    
    # Only trim start of March
    march_processed = trim_empty_weeks(march_processed, trim_start=True)

    # Hide days before first game in the remaining first week
    if march_games and march_processed:
        first_game_day = int(march_games[0]["game_date"][8:10])
        new_first_week = []
        for day_num, opponent, is_home in march_processed[0]:
            if day_num != -1 and day_num < first_game_day:
                new_first_week.append((-1, None, None))
            else:
                new_first_week.append((day_num, opponent, is_home))
        march_processed[0] = new_first_week
    
    # Merge last week of March with first week of April if they share a row
    if march_processed and april_processed:
        last_march_week = march_processed[-1]
        first_april_week = april_processed[0]
        
        merged_week = []
        can_merge = True
        for i in range(7):
            march_day = last_march_week[i]
            april_day = first_april_week[i]
            
            if march_day[0] == -1 and april_day[0] == -1:
                merged_week.append((-1, None, None))
            elif march_day[0] == -1:
                merged_week.append(april_day)
            elif april_day[0] == -1:
                merged_week.append(march_day)
            else:
                can_merge = False
                break
        
        if can_merge:
            march_processed = march_processed[:-1]
            april_processed = april_processed[1:]
            march_april = march_processed + [merged_week] + april_processed
        else:
            march_april = march_processed + april_processed
    else:
        march_april = march_processed + april_processed


    # All star game in July
    allstar_date = all_schedules[teamName]["allstar_date"]

    # Don't trim other months - just process them
    may = process_month(calendar.monthcalendar(CURRENT_YEAR, 5), all_schedules[teamName]['by_month'][1], teamName, 5)
    june = process_month(calendar.monthcalendar(CURRENT_YEAR, 6), all_schedules[teamName]['by_month'][2], teamName, 6)
    july = process_month(calendar.monthcalendar(CURRENT_YEAR, 7), all_schedules[teamName]['by_month'][3], teamName, 7, allstar_date)
    august = process_month(calendar.monthcalendar(CURRENT_YEAR, 8), all_schedules[teamName]['by_month'][4], teamName, 8)
    september = process_month(calendar.monthcalendar(CURRENT_YEAR, 9), all_schedules[teamName]['by_month'][5], teamName, 9)
    
    # Only trim end of September (after season ends)
    september = trim_empty_weeks(september, trim_end=True)

    team_calendar = [march_april, may, june, july, august, september]
    
    return team_calendar

# Testing print_team_calendar
# if teamName:
#     print(print_team_calendar(teamName))



def render_month_calendar_html(month_data):
    html = "<table style='width:100%; table-layout:fixed; text-align:center; border-collapse:collapse; border:none;'>"
    html += "<tr><th style='border:none;'>Sun</th><th style='border:none;'>Mon</th><th style='border:none;'>Tue</th><th style='border:none;'>Wed</th><th style='border:none;'>Thu</th><th style='border:none;'>Fri</th><th style='border:none;'>Sat</th></tr>"
    
    for week in month_data:
        # Skip rows that are all padding
        if all(day[0] == -1 for day in week):
            continue
            
        html += "<tr>"
        for day_num, opponent, home_check in week:
            if day_num == -1:
                # Invisible cell
                html += "<td style='border:none; background:none; height:40px;'></td>"
            elif opponent == "ALL_STAR":
                # All-Star Game
                html += f"""<td style='padding:2px; position:relative; border:1px solid #333; height:40px; background-color:#FFE066;'>
                    <div style='position:absolute; top:2px; left:4px; font-size:10px; color:#888;'>{day_num}</div>
                    <div style='display:flex; justify-content:center; align-items:center; height:100%;'>
                        <img src='{ALLSTAR_LOGO}' width='24' title='All-Star Game'>
                    </div>
                </td>"""
            elif opponent:  # Game day
                logo_url = team_logo_map.get(opponent, "")
                
                # Home = light blue, Away = light gray
                bg_color = "#D7F4F5" if home_check else "#E8E8E8"

                if logo_url:
                    html += f"""<td style='padding:2px; position:relative; border:1px solid #333; height:40px; background-color:{bg_color};'>
                        <div style='position:absolute; top:2px; left:4px; font-size:10px; color:#888;'>{day_num}</div>
                        <div style='display:flex; justify-content:center; align-items:center; height:100%;'>
                            <img src='{logo_url}' width='24' title='{opponent}'>
                        </div>
                    </td>"""
                else:
                    html += f"""<td style='padding:2px; position:relative; border:1px solid #333; height:40px; background-color:{bg_color};'>
                        <div style='position:absolute; top:2px; left:4px; font-size:10px; color:#888;'>{day_num}</div>
                    </td>"""
            else:
                # No game - just show day number
                html += f"""<td style='padding:2px; position:relative; border:1px solid #333; height:40px;'>
                    <div style='position:absolute; top:2px; left:4px; font-size:10px; color:#888;'>{day_num}</div>
                </td>"""
        html += "</tr>"
    
    html += "</table>"
    return html

# In the sidebar
with st.sidebar:
    with st.container():
        if teamName:
            # team_name to be used to look up schedule
            team_schedule = all_schedules[teamName]

            # st.write(team_schedule['games'][:5])  # Show first 5 games
            st.write(team_schedule['by_month'][0][:2])   # Shows the first two games of March/April

            # Team logo displayed
            

# Main Page

# Testing calendar import
# st.write(calendar.monthcalendar(CURRENT_YEAR, 3))

# Calendar is broken up into 2 rows, 3 columns
# [March/April, May, June]
# [July, August, September]

c1, c2, c3  = st.columns(3)
c4, c5, c6  = st.columns(3)

if teamName:
    team_calendar = print_team_calendar(teamName)
    
    if team_calendar:
        with st.container():
            c1.markdown("<h3 style='text-align: center;'>March/April</h3>", unsafe_allow_html=True)
            c1.markdown(render_month_calendar_html(team_calendar[0]), unsafe_allow_html=True)

            c2.markdown("<h3 style='text-align: center;'>May</h3>", unsafe_allow_html=True)
            c2.markdown(render_month_calendar_html(team_calendar[1]), unsafe_allow_html=True)

            c3.markdown("<h3 style='text-align: center;'>June</h3>", unsafe_allow_html=True)
            c3.markdown(render_month_calendar_html(team_calendar[2]), unsafe_allow_html=True)

        with st.container():
            c4.markdown("<h3 style='text-align: center;'>July</h3>", unsafe_allow_html=True)
            c4.markdown(render_month_calendar_html(team_calendar[3]), unsafe_allow_html=True)

            c5.markdown("<h3 style='text-align: center;'>August</h3>", unsafe_allow_html=True)
            c5.markdown(render_month_calendar_html(team_calendar[4]), unsafe_allow_html=True)

            c6.markdown("<h3 style='text-align: center;'>September</h3>", unsafe_allow_html=True)
            c6.markdown(render_month_calendar_html(team_calendar[5]), unsafe_allow_html=True)
    else:
        st.error("Failed to fetch team_calendar")