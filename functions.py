from data import *
import pandas as pd
import requests
import streamlit as st
import json
import util as util
import model as model

def get_all_mlb_hrs():
    mlb_hrs = pd.DataFrame({'csv_file': mlb_hr_csvs_list})

    # Extract season from the 'csv_file' column using regex
    mlb_hrs['season'] = mlb_hrs['csv_file'].str.extract(r'/datasets/(\d{4})')

    mlb_hrs['hr_data'] = mlb_hrs['csv_file'].apply(pd.read_csv)

    for index, row in mlb_hrs.iterrows():
        hr_df = row['hr_data']
        hr_df['season'] = row['season']

    all_mlb_hrs = (pd.concat(mlb_hrs['hr_data'].tolist(), ignore_index = True)
        [['season', 'play_id', 'title', 'ExitVelocity', 'LaunchAngle', 'HitDistance',
            'video']])
    return all_mlb_hrs

def get_mlb_hr_by_play_id(play_id):
    all_mlb_hrs = get_all_mlb_hrs()
    return all_mlb_hrs[all_mlb_hrs['play_id'] == play_id]

def get_mlb_homeruns(player_name=None, season=None):
    all_mlb_hrs = get_all_mlb_hrs()
    if player_name:
        all_mlb_hrs = all_mlb_hrs[all_mlb_hrs['title'].str.contains(player_name, case=False, na=False)]
    if season:
        all_mlb_hrs = all_mlb_hrs[all_mlb_hrs['season'] == season]
    
    mlb_home_runs = all_mlb_hrs.head(10).to_dict(orient='records')
    st.session_state["top_videos"] = mlb_home_runs
    if mlb_home_runs:
        model.select_video(mlb_home_runs[0])
        st.session_state["update_body"] = True
    else:
        st.session_state["selected_video"] = None
    return mlb_home_runs

def play_video_at(timestamp):
    print("timestamp_functions", timestamp)
    timestamp = util.format_timestamp(timestamp)
    if timestamp:
        st.session_state["selected_video_start"] = util.time_to_seconds(timestamp)
        st.session_state["update_body"] = True
        print("selected_video_start_functions", st.session_state["selected_video_start"])
        return f"Successfully played the video at timestamp:{timestamp} as requested"
    else:
        st.session_state["selected_video"] = None
        return "Unable to play the video as requested"

allowed_functions = {
    "get_mlb_homeruns": get_mlb_homeruns,
    "play_video_at": play_video_at
}

def execute_function(function_name, args):
    return allowed_functions[function_name](**args)

def process_endpoint_url(endpoint_url, pop_key=None):
  json_result = requests.get(endpoint_url).content
  data = json.loads(json_result)

   # if pop_key is provided, pop key and normalize nested fields
  if pop_key:
    df_result = pd.json_normalize(data.pop(pop_key), sep = '_')
  # if pop_key is not provided, normalize entire json
  else:
    df_result = pd.json_normalize(data)

  return df_result

st.cache_data(show_spinner=False)
def get_players_info():
    all_players = process_endpoint_url('https://statsapi.mlb.com/api/v1/sports/1/players', "people")
    return all_players

def get_player_info(name):
    all_players = get_players_info()
    player_info = all_players[all_players["fullName"] == name]
    return player_info.to_dict(orient='records')[0] if not player_info.empty else None

st.cache_data(show_spinner=False)
def get_teams_info():
    all_teams = process_endpoint_url('https://statsapi.mlb.com/api/v1/teams?sportId=1', "teams")
    return all_teams

def get_team_info(name):
    all_teams = get_teams_info()
    team_info = all_teams[all_teams["name"] == name]
    return team_info.to_dict(orient='records')[0] if not team_info.empty else None