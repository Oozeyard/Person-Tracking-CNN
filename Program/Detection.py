from ultralytics import YOLO
from VideoReader import VideoReader
import cv2

class Detection:
    def __init__(self, video, output_path):
        self.model = YOLO("Models/yolo11n.pt")
        self.video = video
        self.output_path = output_path
        
        self.processed_frames = []
    
    def process(self):
        for i in range(self.video.get_frame_count()):
            frame = self.video.get_frame(i)
            results = self.model.track(frame, classes=0, verbose=False, persist=True, tracker="bytetrack.yaml")
            self.blur(frame, results)
            self.processed_frames.append(results[0].plot())
            
            # Update progress bar
            progress = (i + 1) / self.video.get_frame_count()
            print(f"\rProcessing frame [{progress:.2%}]", end="")
    
        self.video.to_video(self.processed_frames, self.output_path)
        
    def blur(self, frame, results):
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                person_region = frame[y1:y2, x1:x2]
                blurred_region = cv2.GaussianBlur(person_region, (75, 75), 0)
                frame[y1:y2, x1:x2] = blurred_region
    
    #def pretreatment(self):
        # # Noises removal
        # frame = cv2.GaussianBlur(frame, (5, 5), 0)

        # # Lightness correction
        # hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # h, s, v = cv2.split(hsv)
        # # Equalize the histogram of the V channel
        # v = cv2.equalizeHist(v)
        # hsv = cv2.merge((h, s, v))
        # frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # # Contrast correction
        # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        # lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        # l, a, b = cv2.split(lab)
        # l = clahe.apply(l)
        # lab = cv2.merge((l, a, b))
        # frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)