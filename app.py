import streamlit as st
import time
import os
import logging
import warnings

from dotenv import load_dotenv
from supabase import create_client
import pandas
import numpy
import statsapi
from concurrent.futures import ThreadPoolExecutor

st.set_page_config("MLB Game Schedule Analyzer", layout="wide")

# Title
st.markdown("<h1 style='text-align: center;'>MLB Game Schedule Analyzer</h1>", unsafe_allow_html=True)

teams = ["Arizona Diamondbacks", "Athletics", "Atlanta Braves", "Baltimore Orioles", "Boston Red Sox", "Chicago Cubs", "Chicago White Sox", "Cincinnati Reds", "Cleveland Guardians", "Colorado Rockies", "Detroit Tigers", "Houston Astros", "Kansas City Royals", "Los Angeles Angels", "Los Angeles Dodgers", "Miami Marlins", "Milwaukee Brewers", "Minnesota Twins", "New York Mets", "New York Yankees", "Philadelphia Phillies", "Pittsburgh Pirates", "San Diego Padres", "San Francisco Giants", "Seattle Mariners", "St. Louis Cardinals", "Tampa Bay Rays", "Texas Rangers", "Toronto Blue Jays", "Washington Nationals"]



@st.cache_data(ttl=1800, show_spinner=False)
def fetch_teams_data(teamId):
    return statsapi.schedule(season=2026,team=teamId)

def teamRegularSeasonScheudle(teamScheudle):
    newTeamScheudle = []
    for game in teamScheudle:
        if game["game_type"] == "R":
            newTeamScheudle.append(game)

    return newTeamScheudle


# In the sidebar
with st.sidebar:
    with st.container():
        st.markdown("### 🔍 Team Search")
        teamName = st.selectbox("What team schedule would you like to loop up?", options=teams,index=None, placeholder="Pick a team")
        team = statsapi.lookup_team(teamName)
        # Team id to be used to look up schedule
        teamId = team[0]["id"]
        st.write(teamId)

        # Gets all games for the season preseason, regular season
        teamScheudle = fetch_teams_data(teamId)
        # Filter down to just be regular season
        filteredScheudle = teamRegularSeasonScheudle(teamScheudle)
        
        # Testing to show first 10 games
        # st.write(filteredScheudle[:10])
        

# # Multithreading for API calls
# with ThreadPoolExecutor(max_workers=2) as executor:


