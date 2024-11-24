import cv2
import json
from Crypto.Cipher import AES
import numpy as np
import argparse
from VideoReader import VideoReader
from Detection import aes_decrypt, aes_encrypt

def load_frame_data(file_path):
    """
    Load frame metadata from a JSON file.
    """
    with open(file_path, "r") as f:
        frame_data = [json.loads(line) for line in f]
    return frame_data

def process_frame(frame, frame_data, decrypt_ids=None):
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

            decrypted_region = aes_decrypt(encrypted_region, key, iv, encrypted_region.shape)
            frame[y1:y2, x1:x2] = decrypted_region
    return frame

def decrypt(video_path, output_path, frame_data, decrypt_ids=None):
    """
    Decrypt encrypted regions in the video for multiple IDs.
    """
    video_reader = VideoReader(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_file = output_path if decrypt_ids is None else f"{output_path}_ids_{'_'.join(map(str, decrypt_ids))}.mp4"
    out = cv2.VideoWriter(output_file, fourcc, video_reader.fps, (video_reader.width, video_reader.height))

    for frame_index in range(video_reader.frame_count):
        success, frame = video_reader.read()
        print(f"\rProcessing frame {frame_index}/{video_reader.frame_count}", end="")
        if not success:
            break

        # Get metadata for the current frame
        current_frame_data = next((fd for fd in frame_data if fd["frame_index"] == frame_index), None)
        if current_frame_data:
            frame = process_frame(frame, current_frame_data, decrypt_ids)

        out.write(frame)

    video_reader.release()
    out.release()
    print(f"Decrypted video saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Decrypt encrypted regions in a video.")
    parser.add_argument("video_path", type=str, help="Path to the encrypted video file.")
    parser.add_argument("output_path", type=str, help="Path to save the decrypted video file.")
    parser.add_argument("--ids", type=int, nargs='*', help="ID(s) of the region(s) to decrypt. If not provided, all regions will be decrypted.")
    parser.add_argument("--metadata", type=str, default="frame_data.json", help="Path to the metadata file for decryption.")

    args = parser.parse_args()

    # Load frame metadata once
    frame_data = load_frame_data(args.metadata)

    decrypt_ids = set(args.ids) if args.ids else None
    decrypt(args.video_path, args.output_path, frame_data, decrypt_ids)

if __name__ == "__main__":
    main()
