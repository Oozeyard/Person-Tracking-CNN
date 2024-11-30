import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import time
from tkVideoPlayer import TkinterVideo
from VideoReader import VideoReader
from Detection import Detection
from Decrypt import Decrypt
import json

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Tracking App")
        self.root.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue") 
        
        # video extension
        self.video_exts = r"*.mp4 *.png *.jpg"#  *.avi *.mov  *.mkv"  /!\ Only mp4 files are supported for now

        
        # Blur
        self.blur_var = ctk.BooleanVar()
        self.face_detection_var = ctk.BooleanVar()
        self.face_detection_var.set(False)
        self.blur_type = ctk.StringVar(value="Gaussian")

        # Video path
        self.video_path = ""
        self.output_path = ""
        self.decrypt_window = None
    
        self.create_widgets()

    def create_widgets(self):
        # Video path
        video_frame = ctk.CTkFrame(self.root)
        video_frame.pack(pady=5, padx=5)
        ctk.CTkLabel(video_frame, text="Video to process:").pack(side="left", padx=5)
        ctk.CTkButton(video_frame, text="Select", command=self.select_video).pack(side="left", padx=5)
        self.video_path_label = ctk.CTkLabel(video_frame, text="", width=300, anchor="w")  # Label pour afficher le chemin de la vidéo
        self.video_path_label.pack(side="left", padx=5)
        
        # output path
        output_frame = ctk.CTkFrame(self.root)
        output_frame.pack(pady=5)
        ctk.CTkLabel(output_frame, text="Output Location:").pack(side="left", padx=5)
        ctk.CTkButton(output_frame, text="Select", command=self.select_output).pack(side="left", padx=5)
        self.output_path_label = ctk.CTkLabel(output_frame, text="", width=300, anchor="w")  # Label pour afficher le chemin de la sortie
        self.output_path_label.pack(side="left", padx=5)
        
        # Checkbox Frame
        checkbox_frame = ctk.CTkFrame(self.root)
        checkbox_frame.pack(pady=5)

        # Checkbox Face detection
        ctk.CTkCheckBox(checkbox_frame, text="Face detection only", variable=self.face_detection_var).pack(side="left", padx=5)
        # Checkbox blur
        ctk.CTkCheckBox(checkbox_frame, text="Apply anonymization", variable=self.blur_var, command=self.toggle_blur_options).pack(side="left", padx=5)
        
        # blur options
        self.blur_options = ctk.CTkComboBox(self.root, values=["Gaussian", "Pixelate", "AES", "Selective"], variable=self.blur_type, state="disabled")
        self.blur_options.pack(pady=5)
        

        # preview video
        self.video_panel = ctk.CTkFrame(self.root, width=600, height=320, corner_radius=15)
        self.video_panel.pack(pady=10)
        self.video_panel.pack_propagate(False)
        self.vid_player = TkinterVideo(self.video_panel, scaled=True, keep_aspect=True, consistant_frame_rate=True, bg="black")
        self.vid_player.set_resampling_method(1)
        self.vid_player.pack(expand=True, fill="both", padx=10, pady=10)
        self.vid_player.bind("<<Duration>>", self.update_duration)
        self.vid_player.bind("<<SecondChanged>>", self.update_scale)
        self.vid_player.bind("<<Ended>>", self.video_ended)

        self.progress_slider = ctk.CTkSlider(self.video_panel, from_=-1, to=1, number_of_steps=1, command=self.seek)
        self.progress_slider.set(-1)
        self.progress_slider.pack(fill="both", padx=10, pady=10)

        self.play_pause_btn = ctk.CTkButton(self.video_panel, text="Play ►", command=self.play_pause)
        self.play_pause_btn.pack(pady=10)


        # Progress bar
        self.progress_label = ctk.CTkLabel(self.root, text="Progression:")
        self.progress_label.pack()
        self.progress = ctk.CTkProgressBar(self.root, width=500, progress_color="green")
        self.progress.pack(pady=5)
        self.progress.set(0)
        
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=5)

        # Process button
        process_button = ctk.CTkButton(button_frame, text="Process", command=self.process_video)
        process_button.pack(side='left', padx=5)

        # Decrypt button
        decrypt_button = ctk.CTkButton(button_frame, text="Decrypt Window", command=self.open_decrypt_window)
        decrypt_button.pack(side='left', padx=5)

        # Dynamic label
        self.dynamic_label = ctk.CTkLabel(self.root, text="")
        self.dynamic_label.pack(pady=5)


    def select_video(self):
        self.vid_player.stop()
        self.video_path = filedialog.askopenfilename(title="Select a video", filetypes=[("Video files", self.video_exts)])
        if self.video_path:
            self.video_path_label.configure(text=self.video_path)
            try:
                self.vid_player.load(self.video_path)
                self.vid_player.play()
                self.progress_slider.set(-1)
                self.play_pause_btn.configure(text="Pause ||")
            except:
                print("Unable to load the file")
            
            print(f"Video path: {self.video_path}")

    def select_output(self):
        self.output_path = filedialog.asksaveasfilename(title="Save as", defaultextension=".mp4", filetypes=[("Video file", self.video_exts)])
        if self.output_path:
            self.output_path_label.configure(text=self.output_path)
            print(f"Output path : {self.output_path}")

    def update_duration(self, event):
        try:
            self.duration = int(self.vid_player.video_info()["duration"])
            self.progress_slider.configure(from_=-1, to=self.duration, number_of_steps=self.duration)
        except:
            pass
    
    def seek(self, value):
        if self.video_path:
            try:
                self.vid_player.seek(int(value))
                self.vid_player.play()
                self.vid_player.after(50,self.vid_player.pause)
                self.play_pause_btn.configure(text="Play ►")
            except Exception as e:
                print(f"Error seeking video: {e}")
        
    def update_scale(self, event):
        try:
            self.progress_slider.set(int(self.vid_player.current_duration()))
        except:
            pass
        
    def play_pause(self):
        if self.video_path:
            if self.vid_player.is_paused():
                self.vid_player.play()
                self.play_pause_btn.configure(text="Pause ||")

            else:
                self.vid_player.pause()
                self.play_pause_btn.configure(text="Play ►")
            
    def video_ended(self, event):
        self.play_pause_btn.configure(text="Play ►")
        self.progress_slider.set(-1)

    def toggle_blur_options(self):
        self.blur_options.configure(state="readonly" if self.blur_var.get() else "disabled")

    def update_progress(self, value, index, outImage):
        self.progress_label.configure(text=f"Progression: {value:.2%}")
        self.progress.set(value) #progress:.2%
        self.progress.update_idletasks()
        self.progress_slider.set(index / self.video.get_fps())
        self.progress_slider.update_idletasks()
        self.dynamic_label.update_idletasks()
        self.root.update()
        self.display_video_frame(outImage) # Work but is slow

    def process_video(self):
        if not self.video_path or not self.output_path:
            self.dynamic_label.configure(text="Select a video and output path")
            return
        start_time = time.time()

        if self.video_path.endswith((".png", ".jpg")): # Image processing
            self.dynamic_label.configure(text="Processing image...")
            self.detection = Detection(self.video_path, self.output_path, self.blur_var.get(), self.blur_options.get(), self.face_detection_var.get(), callback=None)
            self.detection.process_image()
        else: # Video processing
            self.video = VideoReader(self.video_path)
            self.dynamic_label.configure(text="Processing video...")
            self.detection = Detection(self.video, self.output_path, self.blur_var.get(), self.blur_options.get(), self.face_detection_var.get(), callback=self.update_progress)
            self.detection.process()
        self.dynamic_label.configure(text=f"Execution time: {round(time.time() - start_time, 2)} seconds")
        
        # time.sleep(0.5)
        # if self.output_path :
        #     self.vid_player.stop()
        #     try:
        #         self.vid_player.load(self.output_path)
        #         # self.vid_player.play()
        #         self.progress_slider.set(0)
        #         self.play_pause_btn.configure(text="Play ►")
        #     except:
        #         print("Unable to load the file")

    def display_video_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        img = img.resize((self.video_panel.winfo_width(), self.video_panel.winfo_height()), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        self.vid_player.config(image=imgtk)
        self.vid_player.image = imgtk
    
    def open_decrypt_window(self):
        if self.decrypt_window is None or self.decrypt_window.root is None:
            self.decrypt_window = DecryptWindow(self.root)
        else:
            self.decrypt_window.root.lift()


class DecryptWindow:
    def __init__(self, root):
        self.root = ctk.CTkToplevel(root)
        self.root.title("Decrypt Video")
        self.root.geometry("800x600")

        self.video_path = ""
        self.frame_data_path = ""
        self.output_path = ""
        self.ids = []  # ids selected
        self.frame_data = None
        self.id_checkbuttons = []  # checkbuttons for IDs
        self.id_vars = []
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.lift()
        self.allIdSelected = False

        self.create_widgets()
    
    def create_widgets(self):
        # Video to decrypt
        video_frame = ctk.CTkFrame(self.root)
        video_frame.pack(pady=5, padx=5)
        ctk.CTkLabel(video_frame, text="Video to decrypt:").pack(side="left", padx=5)
        ctk.CTkButton(video_frame, text="Select", command=self.select_video).pack(side="left", padx=5)
        self.video_path_label = ctk.CTkLabel(video_frame, text="", width=300, anchor="w")
        self.video_path_label.pack(side="left", padx=5)

        # Frame data file
        frame_data_frame = ctk.CTkFrame(self.root)
        frame_data_frame.pack(pady=5, padx=5)
        ctk.CTkLabel(frame_data_frame, text="Frame Data (JSON):").pack(side="left", padx=5)
        ctk.CTkButton(frame_data_frame, text="Select", command=self.select_frame_data).pack(side="left", padx=5)
        self.frame_data_label = ctk.CTkLabel(frame_data_frame, text="", width=300, anchor="w")
        self.frame_data_label.pack(side="left", padx=5)

        # ID selection for decryption
        id_frame = ctk.CTkFrame(self.root)
        id_frame.pack(pady=5, padx=5)
        ctk.CTkLabel(id_frame, text="Select IDs for decryption:").pack(side="left", padx=5)

        # Frame to hold checkbuttons for IDs
        self.id_checkbuttons_frame = ctk.CTkFrame(self.root)
        self.id_checkbuttons_frame.pack(pady=5, padx=5)

        # Select all button
        ctk.CTkButton(self.root, text="Select All IDs", command=self.select_all_ids).pack(pady=5)

        # Output location
        output_frame = ctk.CTkFrame(self.root)
        output_frame.pack(pady=5, padx=5)
        ctk.CTkLabel(output_frame, text="Output Location:").pack(side="left", padx=5)
        ctk.CTkButton(output_frame, text="Select", command=self.select_output).pack(side="left", padx=5)
        self.output_path_label = ctk.CTkLabel(output_frame, text="", width=300, anchor="w")
        self.output_path_label.pack(side="left", padx=5)

        # Decrypt button
        ctk.CTkButton(self.root, text="Decrypt", command=self.decrypt_video).pack(pady=20)

    def select_video(self):
        self.root.lower()
        self.video_path = filedialog.askopenfilename(title="Select Video", filetypes=[("Video files", "*.mp4")])
        if self.video_path:
            self.video_path_label.configure(text=self.video_path)
        self.root.lift()

    def select_frame_data(self):
        self.root.lower()
        self.frame_data_path = filedialog.askopenfilename(title="Select Frame Data", filetypes=[("JSON files", "*.json")], parent=self.root)
        if self.frame_data_path:
            self.frame_data_label.configure(text=self.frame_data_path)
            self.load_frame_data(self.frame_data_path) # Load IDs from JSON file
        self.root.lift()

    def load_frame_data(self, path):
        """Load Json File to show all IDs"""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()

            self.ids.clear()
            self.id_checkbuttons.clear()
            self.id_vars.clear()

            unique_ids = set() # Set to store IDs
            for line in lines:
                try:
                    frame_data = json.loads(line)
                    for bbox in frame_data.get("bboxes", []):
                        unique_ids.add(bbox.get("id"))
                except json.JSONDecodeError as e:
                    print(f"Error loading JSON File : {e}")

            self.ids = sorted(unique_ids)

            # Checkbox showing all IDs
            for widget in self.id_checkbuttons_frame.winfo_children():
                widget.destroy()

            scrollable_frame = self.create_scrollable_frame(self.id_checkbuttons_frame)

            for id_value in self.ids:
                var = ctk.IntVar()
                checkbutton = ctk.CTkCheckBox(
                    scrollable_frame, 
                    text=f"ID {id_value}", 
                    variable=var, 
                )
                checkbutton.pack(anchor="w", pady=2)
                self.id_vars.append(var)
                self.id_checkbuttons.append(checkbutton)


        except Exception as e:
            print(f"Error loading frame data: {e}")


    def select_all_ids(self):
        self.allIdSelected = True
        for var in self.id_vars:
            var.set(True)

    def get_selected_ids(self):
        """Return a list of selected IDs"""
        selected_ids = [self.ids[i] for i, var in enumerate(self.id_vars) if var.get()]
        return selected_ids

    def select_output(self):
        self.root.lower()
        self.output_path = filedialog.asksaveasfilename(title="Save As", defaultextension=".mp4", filetypes=[("Video files", "*.mp4")])
        if self.output_path:
            self.output_path_label.configure(text=self.output_path)
        self.root.lift()

    def decrypt_video(self):
        selected_ids = self.get_selected_ids()
        if not all([self.video_path, self.frame_data_path, self.output_path, selected_ids]):
            ctk.CTkLabel(self.root, text="Please select all files and at least one ID.").pack(pady=5)
            return

        try:
            self.run_decryption(selected_ids)
            ctk.CTkLabel(self.root, text="Decryption complete!").pack(pady=5)
        except Exception as e:
            ctk.CTkLabel(self.root, text=f"Error: {e}").pack(pady=5)

    def run_decryption(self, selected_ids):
        print(f"Decrypting {self.video_path} using {self.frame_data_path} and selected IDs: {selected_ids}...")
        decrypt = Decrypt(self.video_path, self.output_path, self.frame_data_path, selected_ids, self.allIdSelected)
        decrypt.process()

    def on_close(self):
        self.root.destroy()
        self.root = None
        
    def create_scrollable_frame(self, parent):
        """Scrollable Frame"""
        canvas = ctk.CTkCanvas(parent, width=400, height=200, bg="#2b2b2b", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(parent, orientation="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas, fg_color="#2b2b2b")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return scrollable_frame


