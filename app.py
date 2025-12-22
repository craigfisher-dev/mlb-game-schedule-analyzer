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