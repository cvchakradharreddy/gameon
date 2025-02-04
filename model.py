import genai as ai
import streamlit as st
import functions as fn
import util as util

def process_message(message):
    output = response_generator(message)
    return output

def response_generator(prompt):
    output = "Sorry, I am unable to process your request at the moment."
    if st.session_state["selected_video"]:
        response = ai.get_response(prompt, st.session_state["selected_video"]['video'])
    else:
        response = ai.get_response(prompt)
    for part in response.candidates[0].content.parts:
        if "function_call" in part:
            function = part.function_call
            function_response = fn.execute_function(function.name, function.args)
            output = ai.send_response({
                function.name: function_response
            }).candidates[0].content.parts[0].text
        if "text" in part:
            output = part.text
    return output

st.cache_data(show_spinner=False)
def generate_insights(video_url):
    response = ai.get_video_insights(video_url)
    return util.process_llm_response(response)

def select_video(video):
    st.session_state["selected_video"] = video

def content(url, start_time=0, subtitles=None, autoplay=True):
    print("start_time_model", start_time)
    st.video(url, start_time=start_time, subtitles=subtitles, autoplay=autoplay)

def process_audio(audio):
    return ai.transcribe_audio(audio)