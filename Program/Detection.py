from ultralytics import YOLO
from VideoReader import VideoReader
import cv2

# Load the model
model = YOLO("Models/yolo11n.pt")


video_path = "../Vidéos/video_test_1.mp4"

video = VideoReader(video_path)

frame = video.get_frame(0)

results = model(frame)

# Display the image
results[0].show() 