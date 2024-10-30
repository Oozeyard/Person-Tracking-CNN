from ultralytics import YOLO
from VideoReader import VideoReader
import cv2
import os

# Load the model
model = YOLO("Models/yolo11n.pt")


video_path = "../Videos/video_test_1.mp4"

video = VideoReader(video_path)

frames = []

for i in range(video.get_frame_count()):
    frame = video.get_frame(i)
    results = model.track(frame, classes=0, verbose=False)
    frames.append(results[0].plot())

video.to_video(frames, "output.mp4")

# results = model(video.get_frame(0))

# # Display the image
# results[0].show() 