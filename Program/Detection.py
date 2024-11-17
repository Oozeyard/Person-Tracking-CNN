from ultralytics import YOLO
import cv2
import torch

class Detection:
    def __init__(self, video, output_path, censored=False, censored_method=None, detect_face=False, callback=None):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model_path = "Models/yolov11n-face.pt" if detect_face else "Models/yolo11n.pt"
        self.model = YOLO(model_path).to(device)
        
        print("GPU : " + str(torch.cuda.is_available()))
        
        self.video = video
        self.output_path = output_path

        self.callback = callback
        self.censored = censored
        self.censored_method = censored_method
    
    def process(self):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, self.video.fps, (self.video.width, self.video.height))

        for i in range(self.video.frame_count):
            success, frame = self.video.read()
            if not success:
                break
            
            results = self.model.track(frame, classes=0, verbose=False, persist=True, tracker="bytetrack.yaml")
            if self.censored:
                self.blur(frame, results)

            out.write(results[0].plot())  # write the frame to the output video
            
            # progress bar
            progress = (i + 1) / self.video.frame_count
            print(f'\rProgress: {progress:.2%}', end='')
            if self.callback:
                self.callback(progress, i, results[0].plot())
        
        self.video.release()
        out.release()
        print(f"\nProcessing complete. Video saved to {self.output_path}")
        
    def process_image(self):
        results = self.model.track(self.video, classes=0, verbose=False, persist=True, tracker="bytetrack.yaml")
        if self.censored:
            self.blur(self.video, results)
        out = results[0].plot()
        cv2.imwrite(self.output_path, out)
        
        
    def blur(self, frame, results):
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                if x1 < 0 or y1 < 0 or x2 > frame.shape[1] or y2 > frame.shape[0]:
                    continue  # Ignore regions out of bounds
                person_region = frame[y1:y2, x1:x2]
                if person_region.size == 0 or person_region.shape[0] == 0 or person_region.shape[1] == 0:
                    print("Invalid region detected. Skipping.")
                    continue  # Ignore empty or invalid regions
                if self.censored_method == 'Gaussian':
                    blur_kernel_size = (85, 85)
                    blurred_region = cv2.GaussianBlur(person_region, blur_kernel_size, 0)
                elif self.censored_method == 'Pixelate':
                    region_height, region_width = person_region.shape[:2]
                    min_pixel_size = 2 # pixel minimum size
                    small_width = max(min_pixel_size, int(region_width * 0.05))
                    small_height = max(min_pixel_size, int(region_height * 0.05))

                    # Downscale & upscale the region to pixelate it
                    small_region = cv2.resize(person_region, (small_width, small_height), interpolation=cv2.INTER_NEAREST)
                    blurred_region = cv2.resize(small_region, (region_width, region_height), interpolation=cv2.INTER_NEAREST)
                frame[y1:y2, x1:x2] = blurred_region

        
    def realease(self):
        self.model.close()
    
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