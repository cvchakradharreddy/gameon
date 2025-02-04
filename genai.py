import google.generativeai as genai
from google.cloud import speech
import streamlit as st
from util import get_video
import os
import time

system_instruction = """
You are an intelligent chatbot that helps users find and watch MLB home run videos. You can handle three types of requests:

1. **Casual Conversation:** Greet the user and suggest what you can do (e.g., "Hi there! I can help you find MLB home run videos from 2016, 2017, and 2024.  Just ask!").

2. **Video Search:**  When a user asks for specific home run videos (e.g., "Show me home runs from the season 2017," "Find all Aaron Judge home runs"), interpret their request and generate the appropriate function call.  Available functions are provided separately via the `tools` parameter.  Adhere to these rules:

    * **Season Availability:** Only videos from 2016, 2017, and 2024 are available. If a user requests other seasons, inform them of this limitation (e.g., "Sorry, videos for that season aren't available. We currently have 2016, 2017, and 2024 seasons.").
    * **Response Formatting:** When responding with the number of videos found, follow these rules:
        * More than 10: "The top 10 videos are loaded for your viewing."
        * 10 or fewer: "The [number] videos found are loaded for your viewing." (e.g., "The 7 videos found are loaded for your viewing.")
    * **No Results:** If no videos match the search, use a baseball-related idiom (e.g., "Strike three! No home runs found for that query.").

3. **Key Moment Search in Selected Video:** When a user asks to find a specific key moment in a *selected* video (e.g., "Find the grand slam in this video," "Show me the walk-off home run"), you will receive the video file as part of the request. Available functions are provided separately via the `tools` parameter. Follow these steps:

    * **Video Analysis:** Analyze the provided video file to identify key moments.
    * **Matching Key Moments:** Search for key moments that closely match the user's request.
    * **Function Call (if found):** If a match is found, return *two* things:
        * The timestamp of the key moment.
        * A function call to control video playback.
    * **Message (if not found):** If no matching key moment is found, return the message: "I couldn't find that specific moment in the video."

**General Instructions:**

* For multi-turn conversations where function call results are provided, incorporate those results into your reasoning and final response. Do not repeat previous turns or function call requests. Assume provided results are accurate.
* If multiple function calls are required, request them one at a time, waiting for each result before requesting the next.
* If user input needs to be passed to a function, include it in the function's arguments.
* Do not repeat yourself. Be concise and natural in your responses.

"""

summary_prompt = """
Summarize the following video in 3 to 5 sentences. Focus on the key points, interesting facts, and insights. Provide the summary directly, without any introductory phrases like "Here is a summary..." or similar.

In addition to the summary, provide the following information in the response:

- Entities: Relevant people, teams, and places identified in the video.
- People excitement: A list of start timestamps with corresponding excitement scores (1 to 10).
- Key moments: A list of start timestamps with descriptions of key moments.

If you cannot determine an excitement score or a key moment, do not include that entry. Only include entries where you can provide both the timestamp *and* the corresponding data (excitement score or key moment description).
"""

api_key = os.getenv("API_Key")
genai.configure(api_key = api_key)

chat_session = None

mlb_hr = genai.protos.Schema(
    type = genai.protos.Type.OBJECT,
    properties = {
        "season": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            description="The season of the home run."
        ),
        "play_id": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            description="The play ID of the home run."
        ),
        "title": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            description="The title of the home run."
        ),
        "ExitVelocity": genai.protos.Schema(
            type=genai.protos.Type.NUMBER,
            description="The exit velocity of the home run."
        ),
        "LaunchAngle": genai.protos.Schema(
            type=genai.protos.Type.NUMBER,
            description="The launch angle of the home run."
        ),
        "HitDistance": genai.protos.Schema(
            type=genai.protos.Type.NUMBER,
            description="The hit distance of the home run."
        ),
        "video": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            description="The video of the home run."
        )
    }
)

get_mlb_homeruns = genai.protos.FunctionDeclaration(
    name="get_mlb_homeruns",
    description="This function returns MLB home runs. It can filter by player name, season, or both.",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "player_name": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="The name of the player."
            ),
            "season": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="The season of the home run."
            )
        }
    ),
    response=genai.protos.Schema(
        type=genai.protos.Type.ARRAY,
        items=mlb_hr
    )
)

play_video_at = genai.protos.FunctionDeclaration(
    name="play_video_at",
    description="This function plays video at a timestamp that matches the key moment requested",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "timestamp": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="The timestamp in the video(Format: 'MM:SS')."
            )
        }
    )
)

video_insights = genai.protos.Schema(
    type = genai.protos.Type.OBJECT,
    properties = {
        "summary": genai.protos.Schema(
            type=genai.protos.Type.STRING,
            description="The summary of the video."
        ),
        "entities": genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "persons": genai.protos.Schema(
                    type=genai.protos.Type.ARRAY,
                    items=genai.protos.Schema(type=genai.protos.Type.STRING)
                ),
                "teams": genai.protos.Schema(
                    type=genai.protos.Type.ARRAY,
                    items=genai.protos.Schema(type=genai.protos.Type.STRING)
                ),
                "places": genai.protos.Schema(
                    type=genai.protos.Type.ARRAY,
                    items=genai.protos.Schema(type=genai.protos.Type.STRING)
                )
            }
        ),
        "people_excitement": genai.protos.Schema(
            type=genai.protos.Type.ARRAY,
            items=genai.protos.Schema(
                type = genai.protos.Type.OBJECT,
                properties = {
                    "timestamp": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="The timestamp in HH:MM:SS format."
                    ),
                    "excitement_score": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="The excitement score between 1 to 10."
                     )
                }
            )
        ),
        "key_moments": genai.protos.Schema(
            type=genai.protos.Type.ARRAY,
            items=genai.protos.Schema(
                type = genai.protos.Type.OBJECT,
                properties = {
                    "timestamp": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="The timestamp in HH:MM:SS format."
                    ),
                    "key_moment": genai.protos.Schema(
                        type=genai.protos.Type.STRING,
                        description="The short description of the key moment."
                    )
                }
            )
        )
    },
    required=["summary", "entities", "people_excitement", "key_moments"]
)

model = genai.GenerativeModel("gemini-1.5-flash",
                              system_instruction=system_instruction,
                              tools=[get_mlb_homeruns, play_video_at])

def generate_content(prompt):
    return model.generate_content(prompt)

def get_chat_session():
    global chat_session
    if chat_session is None:
        chat_session = model.start_chat()
    return chat_session

def get_response(prompt, url=None):
    chat = get_chat_session()
    if url:
        video = get_genai_video(url)
        response = chat.send_message([video, prompt])
    else:
        response = chat.send_message(prompt)
    return response

def send_response(responses):
    response_parts = [
        genai.protos.Part(function_response=genai.protos.FunctionResponse(name=fn, response={"result": val}))
        for fn, val in responses.items()
    ]
    chat = get_chat_session()
    return chat.send_message(response_parts)

def get_genai_video(url):
    buffer = get_video(url)
    video_name = os.path.basename(url)
    base_name = os.path.splitext(video_name)[0]
    file_name = base_name[:40].lower()
    try:
        video_file = genai.get_file(f"files/{file_name}")
    except Exception as e:
        video_file = genai.upload_file(buffer, name=f"files/{file_name}", mime_type="video/mp4")
    # Videos need to be processed before you can use them.
    while video_file.state.name == "PROCESSING":
        time.sleep(0.1)
        video_file = genai.get_file(video_file.name)
    return video_file

def get_video_insights(url):
    video_file = get_genai_video(url)
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=genai.GenerationConfig(
                                          response_mime_type="application/json",
                                          response_schema=video_insights
                                      ))
    response = model.generate_content([video_file, summary_prompt])
    return response.text
    
def transcribe_audio(audio_file):
    """Transcribes audio to text and sends it to Gemini."""

    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(content=audio_file.getvalue())
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # Adjust encoding if needed
        language_code="en-US",  # Set language code
    )

    response = client.recognize(config=config, audio=audio)

    transcript = ""
    for result in response.results:
        for alternative in result.alternatives:
            transcript += alternative.transcript

    return transcript