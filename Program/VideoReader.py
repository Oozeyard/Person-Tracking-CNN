import cv2
import os

####################################################
################ VideoReader Class  ################
####################################################

class VideoReader:
    video = None

    frames = []

    def __init__(self, video_path):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"The video file at {video_path} does not exist.")
        self.video = cv2.VideoCapture(video_path)

        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))

    def extract(self):
        print("Extracting frames from video...")
        success, frame = self.video.read()
        while success:
            self.frames.append(frame)
            success, frame = self.video.read()

    def get_frame(self, index):
        if index < 0 or index >= self.frame_count:
            return None
        return self.frames[index]
    
    def get_frame_count(self):
        return self.frame_count
    
    def get_fps(self):
        return self.fps

    def to_video(self, frames, output_path):
        print("Writing frames to video...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
        for frame in frames:
            out.write(frame)
        out.release()
        print(f"Video saved to {output_path}")
    
        
    