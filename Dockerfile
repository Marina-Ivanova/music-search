FROM python:3.6-slim

COPY . /root

WORKDIR /root

RUN apt-get update -y && apt-get install -y ffmpeg
RUN pip install flask gunicorn numpy scipy flask_wtf pandas librosa
RUN pip install -U scikit-learn

