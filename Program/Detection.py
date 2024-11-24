from ultralytics import YOLO
import cv2
import torch
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import numpy as np
import json
import os

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

        # AES dictionary
        self.aes_keys = {}

    def generate_aes_key(self):
        return get_random_bytes(16) #AES 128 bits key
    
    def process(self):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, self.video.fps, (self.video.width, self.video.height))

        if os.path.exists("aes_keys.txt"):
            os.remove("aes_keys.txt")
        if os.path.exists("frame_data.json"):
            os.remove("frame_data.json")

        for i in range(self.video.frame_count):
            success, frame = self.video.read()
            if not success:
                break
            
            results = self.model.track(frame, classes=0, verbose=False, show=False, persist=True, tracker="bytetrack.yaml")

            if self.censored:
                self.blur(frame, results, i)

            out.write(results[0].plot())  # write the frame to the output video
            
            # progress bar
            progress = (i + 1) / self.video.frame_count
            print(f'\rProgress: {progress:.2%}', end='')
            
            if self.callback:
                self.callback(progress, i, results[0].plot())
        
        self.video.release()
        out.release()
        print(f"\nProcessing complete. Video saved to {self.output_path}")

    def handle_aes_and_tracking(self, results):
        current_ids = set()
        for result in results:
            for box in result.boxes:
                track_id = int(box.id.item())
                current_ids.add(track_id)

                assert len(set(self.aes_keys.keys())) == len(self.aes_keys), "Duplicate keys detected!"
                
                if track_id not in self.aes_keys:
                    # Generate a new AES key for this track ID
                    self.aes_keys[track_id] = self.generate_aes_key()
                    with open("aes_keys.txt", "a") as f:
                        f.write(f"ID: {track_id}, Key: {self.aes_keys[track_id].hex()}\n")
        
        
    def process_image(self):
        frame = cv2.imread(self.video)
        results = self.model.track(frame, classes=0, verbose=False, persist=True, tracker="bytetrack.yaml")
        if self.censored:
            self.blur(frame, results)
        out = results[0].plot()
        cv2.imwrite(self.output_path, out)
        
        
    def blur(self, frame, results, frame_index):
        # Handle AES and tracking
        self.handle_aes_and_tracking(results)

        # JSON file to store the AES keys
        frame_data = {
            "frame_index": frame_index,
            "bboxes": []
        }

        line_width = 2
        for result in results:
            for box in result.boxes:
                track_id = int(box.id.item())
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                x1, y1, x2, y2 = x1 + line_width, y1 + line_width, x2 - line_width, y2 - line_width
                if x1 < 0 or y1 < 0 or x2 > frame.shape[1] or y2 > frame.shape[0]:
                    continue  # Ignore regions out of bounds
                person_region = frame[y1:y2, x1:x2]
                if person_region.size == 0 or person_region.shape[0] == 0 or person_region.shape[1] == 0:
                    print("Invalid region detected. Skipping.")
                    continue  # Ignore empty or invalid regions
                if self.censored_method == 'Gaussian':
                    blurred_region = self.gaussian_blur(person_region)
                elif self.censored_method == 'Pixelate':
                    blurred_region = self.pixelate(person_region)
                elif self.censored_method == 'AES':
                    key = self.aes_keys.get(track_id)
                    if key != None:
                        blurred_region, iv = aes_encrypt(person_region, key)
                        # print(f"ID {track_id}: Key: {key.hex()}, IV: {iv.hex()}")
                        bbox_data = {
                            "id": track_id,
                            "coords": [x1, y1, x2, y2],
                            "key": key.hex(),
                            "iv": iv.hex(),
                            "region": blurred_region.tolist()
                        }
                        frame_data["bboxes"].append(bbox_data)

                    else:
                        blurred_region = person_region
                    
                frame[y1:y2, x1:x2] = blurred_region

            with open("frame_data.json", "a") as f:
                f.write(json.dumps(frame_data) + "\n")

    def gaussian_blur(self, region):
        """
        Apply Gaussian blur to a region
        """
        kernel_size = (85, 85)
        return cv2.GaussianBlur(region, kernel_size, 0)

    def pixelate(self, region):
        """
        Pixelate a region
        """
        region_height, region_width = region.shape[:2]
        min_pixel_size = 2
        small_width = max(min_pixel_size, int(region_width * 0.05))
        small_height = max(min_pixel_size, int(region_height * 0.05))
        
        # Downscale & upscale the region to pixelate it
        small_region = cv2.resize(region, (small_width, small_height), interpolation=cv2.INTER_NEAREST)
        return cv2.resize(small_region, (region_width, region_height), interpolation=cv2.INTER_NEAREST)
    
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


############################################################################################################
# AES Encryption and Decryption
############################################################################################################
def aes_encrypt(region, key):
    """
    AES encryption.
    """
    iv = get_random_bytes(16)  # AES 128 bits IV
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Convert region to bytes
    region_bytes = region.tobytes()

    # Block size for AES encryption
    block_size = 16
    num_blocks = len(region_bytes) // block_size  

    encrypted_bytes = b''  # Store the encrypted data

    for i in range(num_blocks):
        block = region_bytes[i * block_size:(i + 1) * block_size]
        encrypted_block = cipher.encrypt(block)
        encrypted_bytes += encrypted_block

    # Get the remaining data
    remaining_data = region_bytes[num_blocks * block_size:]

    # Concatenate the remaining data to the encrypted data
    encrypted_bytes += remaining_data

    # Convert the encrypted bytes to a numpy array
    encrypted_array = np.frombuffer(encrypted_bytes, dtype=np.uint8)

    # Reshape the encrypted data to the original shape
    encrypted_array = encrypted_array.reshape(region.shape)

    return encrypted_array, iv


def aes_decrypt(encrypted_region, key, iv, original_shape):
    """
    AES decryption.
    """
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Convert encrypted region to bytes
    encrypted_bytes = encrypted_region.tobytes()

    # Block size for AES decryption
    block_size = 16
    num_blocks = len(encrypted_bytes) // block_size  

    
    decrypted_bytes = b'' # Store the decrypted data

    for i in range(num_blocks):
        block = encrypted_bytes[i * block_size:(i + 1) * block_size]
        decrypted_block = cipher.decrypt(block)
        decrypted_bytes += decrypted_block

    # Get the remaining data
    remaining_data = encrypted_bytes[num_blocks * block_size:]

    # Concatenate the remaining data to the decrypted data
    decrypted_bytes += remaining_data

    # Convert the decrypted bytes to a numpy array
    decrypted_region = np.frombuffer(decrypted_bytes, dtype=np.uint8)

    # Reshape the decrypted data to the original shape
    decrypted_region = decrypted_region.reshape(original_shape)

    return decrypted_region

    
    