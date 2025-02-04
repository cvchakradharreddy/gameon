import streamlit as st
import functions as fn
from util import *
import model as model 
import chart as chart

st.set_page_config(page_title="MLB Home Runs", page_icon=":baseball:", layout="wide", initial_sidebar_state="expanded")

if "top_videos" not in st.session_state:
    st.session_state["top_videos"] = fn.get_mlb_homeruns()

if "selected_video" not in st.session_state:
    st.session_state["selected_video"] = st.session_state["top_videos"][0] if st.session_state["top_videos"] else None

if "selected_video_start" not in st.session_state:
    st.session_state["selected_video_start"] = 0

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "update_body" not in st.session_state:
    st.session_state["update_body"] = False

@st.fragment
def sidebar():
    with st.container(height=400, border=False):
        st.container(height=100, border=False)
        st.markdown('<p style="text-align: center;"><svg xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://www.w3.org/2000/svg" height="92.56002" width="171.69131" version="1.1" xmlns:cc="http://creativecommons.org/ns#" xmlns:dc="http://purl.org/dc/elements/1.1/" viewBox="0 0 171.69131 92.56002"><path d="M157.40349.00016H14.31505A14.42141,14.42141,0,0,0,4.16912,4.12823,14.26059,14.26059,0,0,0,.00084,14.34117v63.851A14.1534,14.1534,0,0,0,4.15572,88.36491,14.3276,14.3276,0,0,0,14.31505,92.56H157.40349A14.35442,14.35442,0,0,0,171.6909,78.19217V14.32777A14.22038,14.22038,0,0,0,157.5783.00041Q157.49091-.00025,157.40349.00016Z" fill="#fff"/><path d="M166.66483,14.32777a9.19433,9.19433,0,0,0-9.08622-9.30118q-.08755-.001-.17512-.00038h-39.994l22.94562,38.34546,2.11765.268,1.34028,1.75577v1.63515l1.44751.29486,1.34028,1.82279v1.58153l1.50112.26806,1.51451,1.64854V56.292a24.84912,24.84912,0,0,0,6.03127,4.02084c2.02383.77737,2.25167,4.02085,3.47132,5.74981,1.52792,2.51973,3.61876,3.52494,3.17647,4.93224-1.01861,3.76619-4.87862,10.11912-8.47057,10.414H139.618v6.08488H157.4169a9.30157,9.30157,0,0,0,9.26161-9.34134l-.00027-.04063v-63.784" fill="#bf0d3e"/><path d="M68.82429,81.50267H61.94865c0-17.1824,5.80341-26.685,12.75948-28.5748.9516-.17423.4959-4.86522-.71035-6.29932H69.97694c-.64334,0-.26806-1.20625-.26806-1.20625l3.25688-6.95607-.44229-1.9032H60.48774L70.379,29.64718C70.83471,11.406,89.545,9.98525,100.81681,17.58465c6.70141,4.43633,7.21071,13.22858,6.70141,19.30005-.08041.38868-1.74237.134-1.74237.134s-1.13924,6.70141,1.83619,6.70141H120.7602c5.36112-.21445,10.53461,3.41771,10.53461,3.41771l1.25987-4.59716L103.752,5.02622h-89.437a9.382,9.382,0,0,0-6.621,2.68056,9.28811,9.28811,0,0,0-2.68056,6.621V78.19218a9.16749,9.16749,0,0,0,2.68056,6.59418,9.38191,9.38191,0,0,0,6.621,2.74758H72.376c-1.4207-2.43931-3.04244-5.21369-3.53834-6.03126" fill="#041e42"/><path d="M17.907,67.95243a6.35294,6.35294,0,1,1,6.35271,6.35316l-.05338-.00023a6.28592,6.28592,0,0,1-6.29967-6.27214q-.00009-.04039.00034-.08079" fill="#fff"/></svg></p>', unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; font-size: 2.5em'> <span> Hey, </span><span> MLB</span><span> fan! </span>⚾</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center;'> Welcome to MLB Home Runs!</h2>", unsafe_allow_html=True)
    
    speech_on = st.toggle("Prefer speech?")
    if speech_on:
        if audio := st.audio_input("What's your next pitch?", label_visibility="collapsed"):
            print("audio--->", audio)
            prompt = model.process_audio(audio)
            audio = None
            st.session_state["messages"].append({"role": "user", "content": prompt})
            st.session_state["messages"].append({"role": "ai", "content": "PROCESS"})
    else:
        if text_input := st.chat_input("What's your next pitch?"):
            prompt = text_input
            st.session_state["messages"].append({"role": "user", "content": prompt})
            st.session_state["messages"].append({"role": "ai", "content": "PROCESS"})
    
    
    
    with st.container(height=600, border=False):
        if st.session_state["messages"]:
            for message in reversed(st.session_state["messages"]):
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                elif message["role"] == "ai":
                    with st.chat_message("ai"):
                        if message["content"] == "PROCESS":
                            with st.spinner("Processing..."):
                                output = model.process_message(prompt)
                                message["content"] = output
                                st.write(message["content"])
                                if st.session_state["update_body"]:
                                    st.session_state["update_body"] = False
                                    print("ready to rerun")
                                    st.rerun()
                        else:
                            st.write(message["content"])

@st.fragment
def body():
    with st.container():
        col1, col2 = st.columns([80, 20])
        with col1:
            with st.container(border=False):
                selected_video = st.session_state["selected_video"]
                if selected_video:
                    video_url = selected_video['video']
                    with st.spinner("Loading video..."):
                        print("selected_video_start_main",st.session_state["selected_video_start"])
                        model.content(video_url, start_time=st.session_state["selected_video_start"])
                        st.session_state["selected_video_start"] = 0
                    with st.spinner("Generating insights..."):
                        df_chart, insights = model.generate_insights(video_url)
                        duration = get_video_duration(video_url)
                        chart.draw_chart(df_chart, duration)
                        st.subheader("Summary", anchor=False)
                        st.write(insights["summary"])
                        if "entities" in insights and insights["entities"]:
                            with st.container():
                                e_col1, e_col2, e_col3 = st.columns(3)
                                with e_col1:
                                    st.write("**Persons**")
                                    for person in insights["entities"]["persons"]:
                                        if player_info := fn.get_player_info(person):
                                            st.image(f'https://securea.mlb.com/mlb/images/players/head_shot/{player_info["id"]}.jpg', width=100, caption=player_info["fullName"])
                                        else:
                                            st.write(person)
                                with e_col2:
                                    st.write("**Teams**")
                                    for team in insights["entities"]["teams"]:
                                        if team_info := fn.get_team_info(team):
                                            st.image(f'https://www.mlbstatic.com/team-logos/{team_info["id"]}.svg', width=50, caption=team_info["teamName"])
                                        else:
                                            st.write(team)
                                with e_col3:
                                    st.markdown("**Places**")
                                    for place in insights["entities"]["places"]:
                                        st.write(place)
                    with st.spinner("Loading stats"):
                        with st.container():
                            s_cols = st.columns(4)
                            with s_cols[0]:
                                st.markdown("**Season**")
                                st.write(selected_video["season"])
                            with s_cols[1]:
                                st.markdown("**Exit Velocity**")
                                st.write(selected_video["ExitVelocity"])
                            with s_cols[2]:
                                st.markdown("**Launch Angle**")
                                st.write(selected_video["LaunchAngle"])
                            with s_cols[3]:
                                st.markdown("**Hit Distance**")
                                st.write(selected_video["HitDistance"])
                else:
                    st.header("Strike three! no results found. 0️⃣", anchor=False)

        with col2:
            with st.container():
                rest_videos = [video for video in st.session_state["top_videos"] if video["play_id"] != st.session_state["selected_video"]["play_id"]]
                for video in rest_videos:
                    thumbnail = get_thumbnail_bytes(video['video'])
                    st.image(thumbnail, caption=video['title'], use_container_width=True)
                    st.button("Watch Video", key=video['play_id'], use_container_width=True, icon="▶️", on_click=model.select_video, args=(video,), type="tertiary")


with st.sidebar:
    sidebar()              
body()
