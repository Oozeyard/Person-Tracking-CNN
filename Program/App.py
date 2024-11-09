import customtkinter as ctk
from PIL import Image, ImageTk  # Nécessite le module Pillow pour afficher les images
import cv2
import time
from tkinter import filedialog
from tkVideoPlayer import TkinterVideo
from VideoReader import VideoReader
from Detection import Detection

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Tracking App")
        self.root.geometry("800x600")
        ctk.set_appearance_mode("dark")  # Mode sombre
        ctk.set_default_color_theme("blue")  # Thème bleu par défaut
        
        # video extension
        self.video_exts = r"*.mp4"#  *.avi *.mov  *.mkv"  /!\ Only mp4 files are supported for now

        
        # Variable pour le choix de floutage
        self.blur_var = ctk.BooleanVar()
        self.blur_type = ctk.StringVar(value="Gaussian")

        # Chemin des fichiers vidéo
        self.video_path = ""
        self.output_path = ""

        # Crée les éléments de l'interface
        self.create_widgets()

    def create_widgets(self):
        # Choix de la vidéo à traiter
        video_frame = ctk.CTkFrame(self.root)
        video_frame.pack(pady=5, padx=5)
        ctk.CTkLabel(video_frame, text="Vidéo à traiter:").pack(side="left", padx=5)
        ctk.CTkButton(video_frame, text="Sélectionner", command=self.select_video).pack(side="left", padx=5)
        self.video_path_label = ctk.CTkLabel(video_frame, text="", width=300, anchor="w")  # Label pour afficher le chemin de la vidéo
        self.video_path_label.pack(side="left", padx=5)
        
        # Choix du fichier de sortie
        output_frame = ctk.CTkFrame(self.root)
        output_frame.pack(pady=5)
        ctk.CTkLabel(output_frame, text="Emplacement de sortie:").pack(side="left", padx=5)
        ctk.CTkButton(output_frame, text="Sélectionner", command=self.select_output).pack(side="left", padx=5)
        self.output_path_label = ctk.CTkLabel(output_frame, text="", width=300, anchor="w")  # Label pour afficher le chemin de la sortie
        self.output_path_label.pack(side="left", padx=5)
        
        # Checkbox pour le floutage
        ctk.CTkCheckBox(self.root, text="Appliquer un floutage", variable=self.blur_var, command=self.toggle_blur_options).pack(pady=5)
        
        # Liste des types de floutage
        self.blur_options = ctk.CTkComboBox(self.root, values=["Gaussian", "Mosaic", "Pixelate"], variable=self.blur_type, state="disabled")
        self.blur_options.pack(pady=5)

        # Visualisation de la vidéo
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
        
        #Process button
        ctk.CTkButton(self.root, text="Process", command=self.process_video).pack(pady=5)

        # Label to appear when needed
        self.dynamic_label = ctk.CTkLabel(self.root, text="", anchor="w")
        self.dynamic_label.pack(pady=5)


    def select_video(self):
        self.vid_player.stop()
        self.video_path = filedialog.askopenfilename(title="Choisissez une vidéo", filetypes=[("Fichiers vidéo", self.video_exts)])
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
        self.output_path = filedialog.asksaveasfilename(title="Sauvegarder sous", defaultextension=".mp4", filetypes=[("Fichiers vidéo", self.video_exts)])
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
            except:
                pass
        
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
        if self.blur_var.get():
            self.blur_options.configure(state="normal")
        else:
            self.blur_options.configure(state="disabled")

    def update_progress(self, value, index):
        self.progress_label.configure(text=f"Progression: {value:.2%}")
        self.progress.set(value) #progress:.2%
        self.progress.update_idletasks()
        self.progress_slider.set(index / self.video.get_fps())
        self.progress_slider.update_idletasks()
        self.display_video_frame(self.detection.processed_frames[index]) # Work but is slow

    def process_video(self):
        self.dynamic_label.update_idletasks()
        if not self.video_path:
            self.dynamic_label.configure(text="Select a video file")
            return
        if not self.output_path:
            self.dynamic_label.configure(text="Select an output path")
            return

        start_time = time.time()

        self.video = VideoReader(self.video_path)
        self.dynamic_label.configure(text="Extracting frames from video...")
        self.dynamic_label.update()
        self.video.extract()

        self.detection = Detection(self.video, self.output_path, callback=self.update_progress)
        time.sleep(0.1)
        self.dynamic_label.configure(text="Processing video...")
        self.dynamic_label.update()
        self.detection.process()

        end_time = time.time()
        execution_time = end_time - start_time
        self.dynamic_label.configure(text=f"Execution time: {round(execution_time, 2)} seconds")
        self.dynamic_label.update()
        time.sleep(1)

        try:
            self.vid_player.load(self.output_path)
            self.vid_player.play()
            self.progress_slider.set(-1)
            self.play_pause_btn.configure(text="Pause ||")
        except:
            print("Unable to load the file")

    
    def display_video_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        img = img.resize((self.video_panel.winfo_width(), self.video_panel.winfo_height()), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        self.vid_player.config(image=imgtk)
        self.vid_player.image = imgtk



