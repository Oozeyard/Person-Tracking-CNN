import customtkinter as ctk
from PIL import Image  # Nécessite le module Pillow pour afficher les images
import cv2
import time
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
        self.video_exts = r"*.mp4  *.avi *.mov  *.mkv"  

        
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
        video_frame.pack(pady=5)
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

        # Progress bar
        ctk.CTkLabel(self.root, text="Progression:").pack(pady=5)
        self.progress = ctk.CTkProgressBar(self.root, width=300)
        self.progress.pack(pady=5)
        self.progress.set(0)
        
        #Process button
        ctk.CTkButton(self.root, text="Process", command=self.process_video).pack(pady=5)

        # Zone d'affichage de la vidéo finale
        self.video_frame = ctk.CTkFrame(self.root, width=600, height=400)
        self.video_frame.pack(pady=10)
        self.video_label = ctk.CTkLabel(self.video_frame)
        self.video_label.pack()

    def select_video(self):
        self.video_path = filedialog.askopenfilename(title="Choisissez une vidéo", filetypes=[("Fichiers vidéo", self.video_exts)])
        if self.video_path:
            self.video_path_label.configure(text=self.video_path)
            print(f"Video path: {self.video_path}")

    def select_output(self):
        self.output_path = filedialog.asksaveasfilename(title="Sauvegarder sous", defaultextension=".mp4", filetypes=[("Fichiers vidéo", self.video_exts)])
        if self.output_path:
            self.output_path_label.configure(text=self.output_path)
            print(f"Output path : {self.output_path}")

    def toggle_blur_options(self):
        if self.blur_var.get():
            self.blur_options.configure(state="normal")
        else:
            self.blur_options.configure(state="disabled")

    def update_progress(self, value):
        self.progress.set(value / 100)
        self.root.update_idletasks()

    def process_video(self):
        start_time = time.time()
        detection = Detection(video)
        video = VideoReader(self.video_path)
        # detection = Detection(video, self.blur_var.get(), self.blur_type.get())
        video.extract()
        detection.process()
        end_time = time.time()

        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")
        for i in range(video.get_frame_count()):
            self.update_progress((i + 1) / video.get_frame_count() * 100)
            self.display_video_frame(video.get_frame(i))
            self.root.update_idletasks()
            time.sleep(0.01)
    
    def display_video_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        image = ImageTk.PhotoImage(image)
        self.video_label.configure(image=image)
        self.video_label.image = image


