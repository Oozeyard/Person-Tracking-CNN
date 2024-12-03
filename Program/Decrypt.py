import cv2
import json
from Crypto.Cipher import AES
import numpy as np
from VideoReader import VideoReader

class Decrypt:
    def __init__(self, video_path, output_path, frame_path, decrypt_ids=None, allIdSelected=False):
        self.video_path = video_path
        self.output_path = output_path
        self.frame_data = self.load_frame_data(frame_path)
        self.decrypt_ids = decrypt_ids
        self.allIdSelected = allIdSelected

    def load_frame_data(self, file_path):
        """
        Load frame metadata from a JSON file.
        """
        with open(file_path, "r") as f:
            frame_data = [json.loads(line) for line in f]
        return frame_data

    def process_frame(self, frame, frame_data, decrypt_ids=None):
        """
        Decrypt specific regions in a frame based on provided IDs.
        If no IDs are provided, decrypt all regions.
        """
        for bbox in frame_data.get("bboxes", []):
            if decrypt_ids is None or bbox["id"] in decrypt_ids:
                x1, y1, x2, y2 = bbox["coords"]
                key = bytes.fromhex(bbox["key"])
                iv = bytes.fromhex(bbox["iv"])

                encrypted_region = np.array(bbox["region"], dtype=np.uint8)

                if frame_data.get("isSelective", True):
                    encrypted_msb = np.array(bbox["encrypted_msb"], dtype=np.uint8)
                    decrypted_region = self.selective_decrypt(encrypted_region, key, iv, encrypted_region.shape, encrypted_msb)
                else:
                    decrypted_region = self.aes_decrypt(encrypted_region, key, iv, encrypted_region.shape)
                frame[y1:y2, x1:x2] = decrypted_region
        return frame

    def process(self):
        """
        Decrypt encrypted regions in the video for multiple IDs.
        """
        video_reader = VideoReader(self.video_path)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        if self.decrypt_ids is None or self.allIdSelected:
            output_file = self.output_path
        else:
            output_file = f"{self.output_path.rsplit('.', 1)[0]}_ids_{'_'.join(map(str, self.decrypt_ids))}.mp4"
        out = cv2.VideoWriter(output_file, fourcc, video_reader.fps, (video_reader.width, video_reader.height))

        for frame_index in range(video_reader.frame_count):
            success, frame = video_reader.read()
            print(f"\rProcessing frame {frame_index}/{video_reader.frame_count}", end="")
            if not success:
                break

            # Get metadata for the current frame
            current_frame_data = next((fd for fd in self.frame_data if fd["frame_index"] == frame_index), None)
            if current_frame_data:
                frame = self.process_frame(frame, current_frame_data, self.decrypt_ids)

            out.write(frame)

        video_reader.release()
        out.release()
    
    def aes_decrypt(self, encrypted_region, key, iv, original_shape):
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

    def selective_decrypt(self, encrypted_region, key, iv, original_shape, encrypted_msb):
        """
        Déchiffrement sélectif des 6 bits LSB d'une région.
        """
        cipher = AES.new(key, AES.MODE_CBC, iv)

        flat_region = encrypted_region.flatten()

        # Extract the 6 LSBs
        encrypted_lsb = flat_region & 0x3F  # Mask
        encrypted_lsb |= encrypted_msb  # Set the 2 MSBs

        # Pad the LSBs
        padding_length = (16 - len(encrypted_lsb) % 16) % 16
        padded_encrypted_lsb = np.pad(encrypted_lsb, (0, padding_length), mode='constant', constant_values=0)

        # Decrypt the padded LSBs
        decrypted_lsb_bytes = cipher.decrypt(padded_encrypted_lsb.tobytes())

        decrypted_lsb = np.frombuffer(decrypted_lsb_bytes, dtype=np.uint8)[:len(encrypted_lsb)]

        # Replace the 6 LSBs with the decrypted LSBs
        flat_region &= 0xC0
        flat_region |= decrypted_lsb & 0x3F  # Set the new 6 LSBs

        decrypted_region = flat_region.reshape(original_shape)

        return decrypted_region

