from VideoReader import VideoReader
import time

video_path = "../Videos/2.mp4"

start_time = time.time()
video = VideoReader(video_path)
end_time = time.time()

execution_time = end_time - start_time
print(f"Execution time: {execution_time} seconds")

