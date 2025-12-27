import streamlit as st
import time
import os
import logging
import warnings
import requests
import json

from dotenv import load_dotenv
from supabase import create_client
import pandas
import numpy
import statsapi
from concurrent.futures import ThreadPoolExecutor

# ESPN API for team logos
ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams"

st.set_page_config("MLB Game Schedule Analyzer", layout="wide")

# Title
st.markdown("<h1 style='text-align: center;'>MLB Game Schedule Analyzer</h1>", unsafe_allow_html=True)


# Filters schedule to regular season games only 
# (removes Spring Training, Post-Season, etc)
def team_regular_season_schedule(team_schedule):
    new_team_schedule = []
    for game in team_schedule:
        if game["game_type"] == "R":
            new_team_schedule.append(game)

    return new_team_schedule


# Fetches all 30 team schedules,
# returns dict: {team_name: [games...]}
@st.cache_data(ttl=86400, show_spinner=False)
def fetch_all_schedules():

    team_ids = []

    # Get all team IDs first
    all_teams = statsapi.get('teams', {'sportId': 1})  # sportId 1 = MLB
    team_ids = [(team['name'], team['id']) for team in all_teams['teams']]

    # Fetch all_season_schedule
    all_season_schedule = statsapi.schedule(season=2026)

    regular_season_schedule = {}

    for name, tid in team_ids:
        # Filter: keep only games where this team is home OR away
        team_games = [game for game in all_season_schedule if game['away_id'] == tid or game['home_id'] == tid]
        # Sort games chronologically by datetime
        team_games_sorted = sorted(team_games, key=lambda game: game['game_datetime'])
        # Filter to regular season only, then store under team name
        regular_season_schedule[name] = team_regular_season_schedule(team_games_sorted)

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
    logos = []

    # Loop through all teams and add in their logos
    for team in teams:
        # Transparent logos (href 4 on ESPNs API list)
        logos.append(team["team"]["logos"][4]["href"])
    
    return logos
        

# Load schedules and logos in parallel for faster startup
with st.spinner("Loading..."):
    with ThreadPoolExecutor(max_workers=2) as executor:
        schedules_future = executor.submit(fetch_all_schedules)
        logos_future = executor.submit(fetch_all_team_logos)
        
        all_schedules = schedules_future.result()
        team_logos = logos_future.result()


# Shows the links collected from ESPNs API
st.write(team_logos)


# In the sidebar
with st.sidebar:
    with st.container():
        st.markdown("### 🔍 Team Search")
        # Dropdown options (team names) pulled from schedule data (sorted A-Z)
        teamName = st.selectbox("What team schedule would you like to look up?", options=sorted(all_schedules.keys()),index=None, placeholder="Pick a team")

        if teamName:
            # team_name to be used to look up schedule
            team_schedule = all_schedules[teamName]

            st.write(team_schedule[:5])  # Show first 5

            # Team logo displayed
            


