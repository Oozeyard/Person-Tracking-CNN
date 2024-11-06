from ultralytics import YOLO
from VideoReader import VideoReader
import cv2

# Load the model
model = YOLO("Models/yolo11n.pt")


video_path = "../Videos/test1.mp4"
output_path = "2out.mp4"

video = VideoReader(video_path)
processed_frames  = []

for i in range(video.frame_count):
    # Get the frame
    frame = video.get_frame(i)


    # 1.Pretreatment
    
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


    # 2.Detection
    results = model.track(frame, classes=0, verbose=False, persist=True, tracker="bytetrack.yaml")

    # Blur person detected
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Coord of bbox
            person_region = frame[y1:y2, x1:x2]     # Extract the region of the person  
            
            # Apply blur in the region
            blurred_region = cv2.GaussianBlur(person_region, (75, 75), 0)
            frame[y1:y2, x1:x2] = blurred_region     

    processed_frames.append(results[0].plot())

    # Update progress bar
    progress = (i + 1) / video.frame_count
    print(f"\rProcessing frame [{progress:.2%}]", end="")

print()

video.to_video(processed_frames, output_path)

# results = model(video.get_frame(0))

# # Display the image
# results[0].show() 