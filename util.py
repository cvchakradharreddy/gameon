from moviepy.video.io.VideoFileClip import VideoFileClip
from PIL import Image
import io, os
from io import BufferedReader
import google_storage as gs
import streamlit as st
import time
import requests
import datetime
import json
import pandas as pd
import cv2

@st.cache_data(show_spinner=False)
def get_thumbnail_bytes(video_path, time_in_seconds=1):
    # Extract video filename (without extension)
    video_name = os.path.basename(video_path)
    base_name = os.path.splitext(video_name)[0]

    # Define the thumbnail filename (same name as video but with .jpg extension)
    thumbnail_name = f"{base_name}.jpg"

    #Check if the thumbnail already exists in the GCS bucket
    blob = gs.get_bucket().blob(thumbnail_name)
    
    if blob.exists():
        # If thumbnail exists, return it as BytesIO object
        #print(f"Thumbnail {thumbnail_name} already exists in the bucket.")
        img_byte_arr = io.BytesIO()
        blob.download_to_file(img_byte_arr)
        img_byte_arr.seek(0)
        return img_byte_arr
    else:
        # If thumbnail doesn't exist, generate and upload it
        #print(f"Thumbnail {thumbnail_name} does not exist. Generating new thumbnail...")

        # Load the video clip
        video = VideoFileClip(video_path)

        # Get a frame at the specified time (in seconds)
        frame = video.get_frame(time_in_seconds)

        # Convert the frame (which is a NumPy array) into a PIL Image
        image = Image.fromarray(frame)

        # Create a BytesIO buffer to hold the image data in memory
        img_byte_arr = io.BytesIO()

        # Save the image to the buffer as a JPEG
        image.save(img_byte_arr, format='JPEG')

        # Make sure to reset the buffer position to the beginning
        img_byte_arr.seek(0)

        # Upload the thumbnail to the GCS bucket
        blob.upload_from_file(img_byte_arr, content_type="image/jpeg")
        #print(f"Thumbnail {thumbnail_name} uploaded to the bucket.")

        # Return the BytesIO object containing the image
        return img_byte_arr


def stream_data(message):
    for word in message.split(" "):
        yield word + " "
        time.sleep(0.05)

@st.cache_data(show_spinner=False)
def get_video(url):
    response = requests.get(url, stream=True) # stream=True is important for large files
    response.raise_for_status() # Check for HTTP errors
    buffer = io.BytesIO(response.content) 
    return buffer 

def format_timestamp(timestamp_str):
    """Formats a timestamp string to HH:MM:SS or returns None if invalid."""
    try:
        # Attempt to parse the string directly (handles various formats)
        time_obj = datetime.datetime.strptime(timestamp_str, "%H:%M:%S")
        return timestamp_str  # If successful, return the original string
    except ValueError:
        try:
            time_obj = datetime.datetime.strptime(timestamp_str, "%M:%S")
            return "00:" + timestamp_str # Add leading zeros for consistency
        except ValueError:
            try:
                seconds = float(timestamp_str)
                td = datetime.timedelta(seconds=seconds)
                hours = td.seconds // 3600
                minutes = (td.seconds // 60) % 60
                seconds_only = td.seconds % 60
                return f"{hours:02d}:{minutes:02d}:{seconds_only:02d}"
            except ValueError:
                return None  # Or handle the error as you see fit


def process_llm_response(llm_response_text):
    try:
        json_data = json.loads(llm_response_text)

        chart_data = []

        for key in ["key_moments", "people_excitement"]:  # Process both similarly
            if key in json_data:
                for item in json_data[key]:
                    formatted_ts = format_timestamp(item.get("timestamp"))
                    if formatted_ts:  # Only add if timestamp is valid
                        event_type = "Highlight" if key == "key_moments" else "Excitement"
                        value = int(item.get("excitement_score")) if key == "people_excitement" and "excitement_score" in item else None # Get value or None
                        event_text = item.get("key_moment") if key == "key_moments" else "Excitement" # Get event text
                        chart_data.append({
                            "Time": formatted_ts,
                            "Event": event_text,
                            "Type": event_type,
                            "Value": value
                        })

        df_chart = pd.DataFrame(chart_data)
        return df_chart, json_data

    except json.JSONDecodeError as e:
        print(f"Invalid JSON from LLM: {e}")
        return None, None

st.cache_data(show_spinner=False)
def get_video_duration_old(url):
        clip = VideoFileClip(url)  # Directly use the buffer
        return clip.duration

def get_video_duration(video_url):
    # Open the video stream from the URL
    video = cv2.VideoCapture(video_url)

    # Check if the video opened successfully
    if not video.isOpened():
        print("Error: Couldn't open the video stream")
    else:
        # Get video duration (using frame count and fps)
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
        
        duration = frame_count / fps
        print(f"Video Duration: {duration} seconds")

    # Don't forget to release the video capture object when done
    video.release()
    return duration

def time_to_seconds(timestamp):
    """Converts a timestamp in HH:MM:SS format to seconds."""
    try:
        hours, minutes, seconds = map(int, timestamp.split(':'))
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        return total_seconds
    except ValueError:
        return None  # Handle invalid timestamp format