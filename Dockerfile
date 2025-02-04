FROM python:3.10
EXPOSE 8080
WORKDIR /app
COPY chart.py ./
COPY data.py ./
COPY functions.py ./
COPY genai_gcp.py ./genai.py
COPY google_storage_gcp.py ./google_storage.py
COPY main.py ./
COPY Major_League_Baseball_logo.svg ./
COPY model.py ./
COPY requirements.txt ./
COPY util.py ./
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0
RUN pip install -r requirements.txt
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0"]