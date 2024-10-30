from VideoReader import VideoReader

video_path = "Vidéos/video_test_1.mp4"

video = VideoReader(video_path)
print(video.get_frame_count())
