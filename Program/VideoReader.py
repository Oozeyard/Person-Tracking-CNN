import cv2
import os

####################################################
################### Video Class  ###################
####################################################

class VideoReader:
    video = None

    frames = []

    def __init__(self, video_path):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"The video file at {video_path} does not exist.")
        self.video = cv2.VideoCapture(video_path)
        self.extract()

    def extract(self):
        print("Extracting frames from video...")
        success, frame = self.video.read()
        while success:
            self.frames.append(frame)
            success, frame = self.video.read()

    def get_frame(self, index):
        if index < 0 or index >= len(self.frames):
            return None
        return self.frames[index]
    
    def get_frame_count(self):
        return len(self.frames)
    
    def get_fps(self):
        return self.video.get(cv2.CAP_PROP_FPS)

    def to_video(self, frames, output_path):
        print("Writing frames to video...")
        height, width, _ = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.get_fps(), (width, height))
        for frame in frames:
            out.write(frame)
        out.release()
        print(f"Video saved to {output_path}")
    
        
    