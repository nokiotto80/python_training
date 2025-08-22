import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter, ExifTags
import os
import math
from playsound import playsound
import threading
import time

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from rembg import remove
import io

class PhotoEditorApp:
    def __init__(self, master):
        self.master = master
        master.title("Il Mio Photo Tool")

        self.image = None
        self.original_image_full = None # Questa è la variabile che conserva l'immagine originale non toccata
        # Queste variabili sotto sono usate per gestire lo stato corrente dell'immagine
        # o copie temporanee per specifiche operazioni.
        self.original_image_for_warp = None # Base PIL per il warp (quando non è attiva la GPU)
        self.original_color_image = None # Immagine base a colori per le operazioni interne (es. b/n toggle, warp)
        
        self.tk_image = None
        self.current_image_path = None
        self.zoom_level = 1.0
        self.blur_radius = 0
        self.alpha_level = 1.0
        
        self.warp_active = False
        # --- MODIFICHE PER EFFETTO "LENTE D'INGRANDIMENTO" ---
        self.warp_radius = 80  # Raggio più piccolo per un effetto più localizzato
        self.warp_strength = 1.2 # Forza maggiore per un'ingrandimento più evidente
        # Puoi sperimentare con questi valori:
        # Per un raggio ancora più piccolo: 50
        # Per una forza ancora maggiore: 1.5 o 2.0
        # --- FINE MODIFICHE ---
        self.original_image_for_warp_tensor = None 
        

        self.is_grayscale_active = tk.BooleanVar(value=False)

        self.warp_sound_path = "/Users/macbook_vincenzo/Python/sounds/213693__taira-komori__warp1.mp3"
        self.sound_thread = None
        self.sound_playing = False

        self.camera_active = False
        self.camera_capture = None
        self.camera_thread = None
        self.stop_camera_thread = threading.Event()
        self.current_camera_frame = None

        self.zoom_box_active = True
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        
        self.canvas_message_id = None 

        # --- VARIABILE PER IL DISPOSITIVO PYTORCH ---
        self.device = torch.device("cpu") 
        self.gpu_accelerated_active = False 
        
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
            print(f"PyTorch utilizzerà il dispositivo: {self.device} (MPS)")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
            print(f"PyTorch utilizzerà il dispositivo: {self.device} (CUDA/ROCm)")
        else:
            print(f"PyTorch utilizzerà il dispositivo: {self.device} (CPU)")
        # --- FINE VARIABILE ---

        self.create_widgets()
        self.update_warp_status()
        self.on_grayscale_selection() 
        self.show_canvas_message("Clicca su 'APRI' per caricare un'immagine o 'ATTIVA FOTOCAMERA'")

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # 1. Crea una cornice per i pulsanti (se non ce l'hai già)

        self.status_bar = tk.Label(self.master, text="Nessuna immagine caricata.", bd=1, relief=tk.SUNKEN, anchor=tk.W, justify=tk.LEFT)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.warp_status_bar = tk.Label(self.master, text="Warp: OFF", bd=1, relief=tk.FLAT, anchor=tk.E, bg="lightblue", fg="darkblue", font=('Helvetica', 10, 'bold'))
        self.warp_status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.main_content_area = tk.Frame(self.master)
        self.main_content_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(self.main_content_area)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.image_display_frame = tk.Frame(self.main_content_area, bg="lightgrey")
        self.image_display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.image_display_frame, bg="lightgrey", highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.image_label = self.canvas.create_image(0, 0, anchor="nw")
        
        self.image_label_widget = self.canvas

        self.image_label_widget.bind('<Motion>', self.handle_mouse_motion)
        self.image_label_widget.bind('<Leave>', self.handle_mouse_leave)
        
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        
        # Crea e impacchetta il pulsante Warp nel button_frame
        self.warp_toggle_button = tk.Button(button_frame, text="Warp: OFF", command=self.toggle_warp)
        self.warp_toggle_button.pack(pady=5, fill=tk.X)
        
        #un altro Frame per i bottoni sotto a tutto,per impacchettare meglio
        # Crea un frame separato per i controlli che vuoi sotto l'immagine
        self.bottom_controls_frame = tk.Frame(self.main_content_area)
        self.bottom_controls_frame.pack(side=tk.BOTTOM, fill=tk.X)

# A questo punto, sei ancora all'interno del button_frame.
# Ora crea e impacchetta lo slider nello stesso button_frame, subito dopo il pulsante.
        self.warp_slider = tk.Scale(
             button_frame,  # Il genitore dello slider è lo stesso frame del pulsante
             from_=10,
             to=200,
             resolution=1,
             orient=tk.HORIZONTAL,
             length=180,
             label="Raggio Warp",
             command=self.update_warp_radius,
             variable=self.warp_radius,
             font=("Helvetica", 8)
)
        self.warp_slider.set(50)
        self.warp_slider.pack(pady=5, fill=tk.X) # Usa pady=5 per dare un po' di spazio



        self.toggle_camera_button = tk.Button(button_frame, text="ATTIVA/DISATTIVA FOTOCAMERA", command=self.toggle_camera)
        self.toggle_camera_button.pack(pady=5, fill=tk.X)

        self.take_photo_button = tk.Button(button_frame, text="SCATTA FOTO", command=self.take_photo, state=tk.DISABLED)
        self.take_photo_button.pack(pady=5, fill=tk.X)

        self.open_button = tk.Button(button_frame, text="APRI", command=self.open_image)
        self.open_button.pack(pady=5, fill=tk.X)

        self.close_button = tk.Button(button_frame, text="CHIUDI", command=self.close_image)
        self.close_button.pack(pady=5, fill=tk.X)
        

        
        
        # --- INIZIO NUOVO PULSANTE "RIPRISTINA ORIGINALE" ---
        tk.Frame(button_frame, height=1, bg="grey").pack(fill=tk.X, pady=10)

        # Caricamento dell'icona
        # Assicurati che 'restore_icon.png' sia nella stessa directory del tuo script,
        # oppure specifica il percorso completo.
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Percorso modificato dall'utente per l'icona UNDO (restore_icon.png)
            icon_path = "/Users/macbook_vincenzo/Python/photo_tool_env/restore_icon.png" 
            self.restore_icon = Image.open(icon_path)
            self.restore_icon = self.restore_icon.resize((24, 24), Image.LANCZOS) # Ridisiziona l'icona
            self.restore_tk_icon = ImageTk.PhotoImage(self.restore_icon)
            
            self.restore_button = tk.Button(button_frame, image=self.restore_tk_icon, text=" Ripristina Originale", compound=tk.LEFT, command=self.restore_original_image)
        except FileNotFoundError:
            print(f"Avviso: file icona '{icon_path}' non trovato. Il pulsante 'Ripristina Originale' sarà solo testo.")
            self.restore_button = tk.Button(button_frame, text="Ripristina Originale", command=self.restore_original_image)
        except Exception as e:
            print(f"Errore caricamento icona: {e}. Il pulsante 'Ripristina Originale' sarà solo testo.")
            self.restore_button = tk.Button(button_frame, text="Ripristina Originale", command=self.restore_original_image)
            
        self.restore_button.pack(pady=5, fill=tk.X)
        # --- FINE NUOVO PULSANTE "RIPRISTINA ORIGINALE" ---


        tk.Frame(button_frame, height=1, bg="grey").pack(fill=tk.X, pady=10)

        self.zoom_in_button = tk.Button(button_frame, text="ZOOM +", command=self.zoom_in)
        self.zoom_in_button.pack(pady=5, fill=tk.X)

        self.zoom_out_button = tk.Button(button_frame, text="ZOOM -", command=self.zoom_out)
        self.zoom_out_button.pack(pady=5, fill=tk.X)
        
        self.reset_zoom_button = tk.Button(button_frame, text="RESET ZOOM", command=self.reset_zoom)
        self.reset_zoom_button.pack(pady=5, fill=tk.X)
        
        tk.Frame(button_frame, height=1, bg="grey").pack(fill=tk.X, pady=10)

        self.blur_plus_button = tk.Button(button_frame, text="BLUR +", command=self.blur_plus)
        self.blur_plus_button.pack(pady=5, fill=tk.X)

        self.blur_minus_button = tk.Button(button_frame, text="BLUR -", command=self.blur_minus)
        self.blur_minus_button.pack(pady=5, fill=tk.X)

        tk.Frame(button_frame, height=1, bg="grey").pack(fill=tk.X, pady=10)

        self.rotate_right_button = tk.Button(button_frame, text="RotateDX", command=self.rotate_right)
        self.rotate_right_button.pack(pady=5, fill=tk.X)

        self.rotate_left_button = tk.Button(button_frame, text="Rotatesx", command=self.rotate_left)
        self.rotate_left_button.pack(pady=5, fill=tk.X)

        tk.Frame(button_frame, height=1, bg="grey").pack(fill=tk.X, pady=10)

        alpha_button_frame = tk.Frame(button_frame)
        alpha_button_frame.pack(pady=5, fill=tk.X)
        
        self.alpha_plus_button = tk.Button(alpha_button_frame, text="ALPHA +", command=self.alpha_plus)
        self.alpha_plus_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.alpha_minus_button = tk.Button(alpha_button_frame, text="ALPHA -", command=self.alpha_minus)
        self.alpha_minus_button.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.removeBG_button = tk.Button(button_frame, text="Rimuovi sfondo", command=self.remove_ai_background)
        self.removeBG_button.pack(pady=5, fill=tk.X)
        
        grayscale_frame = tk.Frame(button_frame, bd=1, relief=tk.RIDGE)
        grayscale_frame.pack(pady=10, padx=5, fill=tk.X)

        tk.Label(grayscale_frame, text="Modalità Colore:").pack(anchor=tk.W, padx=5, pady=2)

        self.color_radio = tk.Radiobutton(grayscale_frame, text="Immagine a colori", 
                                          variable=self.is_grayscale_active, value=False, 
                                          command=self.on_grayscale_selection)
        self.color_radio.pack(anchor=tk.W, padx=10)

        self.bw_radio = tk.Radiobutton(grayscale_frame, text="Immagine in bianco e nero", 
                                       variable=self.is_grayscale_active, value=True, 
                                       command=self.on_grayscale_selection)
        self.bw_radio.pack(anchor=tk.W, padx=10)
        
        # Aggiungi un pulsante per attivare la funzione

        # Aggiungi una variabile di controllo per lo slider
        self.cartoonize_factor = tk.DoubleVar()
        self.cartoonize_factor.set(0) # Inizializza a 0 per mostrare l'immagine originale
        
        # Crea e impacchetta lo slider
        self.cartoonize_slider = tk.Scale(
            self.bottom_controls_frame,
            from_=0,
            to=100,
            resolution=1,
            orient=tk.HORIZONTAL,
            length=200,
            label="Fattore Cartoon",
            command=self.update_cartoonize, # La funzione che si attiva muovendo lo slider
            variable=self.cartoonize_factor
        )
        self.cartoonize_slider.pack(pady=5)
        
     
    def update_warp_radius(self,val):

        # 'val' è il valore numerico (str o int) passato automaticamente da Tkinter
        
        # Non è necessario usare self.warp_radius.get(), perché 'val' contiene già il valore.
        # Se vuoi, puoi stamparlo per verifica.
        print(f"Il raggio del Warp è ora: {val}")
    
        # Puoi usare la variabile di controllo per altri scopi, ma non è necessario
        # aggiornarla qui perché è già aggiornata dal legame 'variable=self.warp_radius'
        
        # ... Inserisci qui la logica per l'effetto Warp ...
        
        # Questa riga era la causa dell'errore precedente e ora non serve più:
        # self.warp_radius.set(val)
                
    def open_image(self):
        if self.camera_active:
            self.stop_camera()

        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("All Files", "*.*")]
        )
        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path):
        try:
            pil_image = Image.open(file_path)
            if pil_image.mode not in ("RGB", "RGBA"):
                pil_image = pil_image.convert("RGB")
                
            self.original_image_full = pil_image.copy() # L'ORIGINALE PULITA VIENE SALVATA QUI
            self.original_image_for_warp = pil_image.copy()
            self.image = pil_image.copy()
            self.original_color_image = pil_image.copy()

            self.current_image_path = file_path
            self.zoom_level = 1.0
            self.blur_radius = 0
            self.alpha_level = 1.0
            self.gpu_accelerated_active = False 

            self.is_grayscale_active.set(False) 
            self.display_image()
            self.update_status_bar()
            self.hide_canvas_message()
        except Exception as e:
            messagebox.showerror("Errore Caricamento Immagine", f"Non è stato possibile caricare l'immagine: {e}")
            self.image = None
            self.original_image_full = None
            self.original_image_for_warp = None
            self.original_color_image = None
            self.current_image_path = None
            self.gpu_accelerated_active = False 
            self.display_image()
            self.update_status_bar()
            self.show_canvas_message("Errore nel caricamento. Riprova.")
    
    def show_canvas_message(self, message):
        if self.canvas_message_id:
            self.canvas.delete(self.canvas_message_id)
        
        self.canvas.update_idletasks()
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2

        self.canvas_message_id = self.canvas.create_text(
            cx, cy, 
            text=message, 
            fill="gray", 
            font=("Helvetica", 16, "bold"), 
            justify=tk.CENTER, 
            width=self.canvas.winfo_width() - 20 
        )

    def hide_canvas_message(self):
        if self.canvas_message_id:
            self.canvas.delete(self.canvas_message_id)
            self.canvas_message_id = None
            
    def display_image(self, img_to_display=None):
        self.hide_canvas_message() 

        if img_to_display is None:
            if self.image:
                base_image = self.image
            elif self.camera_active and self.current_camera_frame:
                base_image = self.current_camera_frame
            else:
                self.canvas.itemconfig(self.image_label, image="")
                self.tk_image = None
                self.show_canvas_message("Nessuna immagine selezionata. Clicca su 'APRI' o 'ATTIVA FOTOCAMERA'") 
                return
        else:
            base_image = img_to_display

        frame_width = self.canvas.winfo_width()
        frame_height = self.canvas.winfo_height()

        if frame_width == 0 or frame_height == 0:
            self.master.after(10, lambda: self.display_image(img_to_display))
            return

        img_width, img_height = base_image.size
        
        display_width = int(img_width * self.zoom_level)
        display_height = int(img_height * self.zoom_level)

        if display_width == 0 or display_height == 0:
            self.show_canvas_message("Immagine troppo piccola per essere visualizzata.")
            return

        scale_w = frame_width / display_width
        scale_h = frame_height / display_height
        scale = min(scale_w, scale_h)

        if scale > 1.0 and self.zoom_level >= 1.0:
             final_display_width = display_width
             final_display_height = display_height
        else:
            final_display_width = int(display_width * scale)
            final_display_height = int(display_height * scale)

        if final_display_width <= 0: final_display_width = 1
        if final_display_height <= 0: final_display_height = 1

        try:
            resized_image = base_image.resize((final_display_width, final_display_height), Image.LANCZOS)
        except ValueError:
            print(f"Warning: Invalid image size after resize attempt ({final_display_width}, {final_display_height}). Skipping resize.")
            resized_image = base_image
        
        if self.blur_radius > 0:
            resized_image = resized_image.filter(ImageFilter.GaussianBlur(self.blur_radius))

        if self.alpha_level < 1.0:
            # Crea un'immagine di sfondo bianca per la trasparenza (simulando alpha su RGB)
            background = Image.new("RGB", resized_image.size, (255, 255, 255))
            resized_image = Image.blend(background, resized_image, self.alpha_level)

        self.tk_image = ImageTk.PhotoImage(resized_image)
        
        x_pos = (frame_width - final_display_width) / 2
        y_pos = (frame_height - final_display_height) / 2
        self.canvas.coords(self.image_label, x_pos, y_pos)
        self.canvas.itemconfig(self.image_label, image=self.tk_image)

    def close_image(self):
        self.image = None
        self.original_image_full = None
        self.original_image_for_warp = None
        self.original_color_image = None
        self.tk_image = None
        self.current_image_path = None
        self.zoom_level = 1.0
        self.blur_radius = 0
        self.alpha_level = 1.0
        self.is_grayscale_active.set(False)
        self.gpu_accelerated_active = False 

        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = None
        self.start_x = None
        self.start_y = None

        self.display_image()
        self.update_status_bar()
        self.update_warp_status()
        self._stop_warp_sound()
        
        if self.camera_active:
            self.stop_camera()

    def zoom_in(self):
        if self.image:
            self.zoom_level *= 1.25
            self.gpu_accelerated_active = False 
            self.display_image()
            self.update_status_bar()
        else: 
            self.show_canvas_message("Carica un'immagine per zoomare.")

    def zoom_out(self):
        if self.image:
            self.zoom_level /= 1.25
            if self.zoom_level < 0.05:
                self.zoom_level = 0.05
            self.gpu_accelerated_active = False 
            self.display_image()
            self.update_status_bar()
        else: 
            self.show_canvas_message("Carica un'immagine per zoomare.")

    def restore_original_image(self):
        if self.original_image_full:
            self.image = self.original_image_full.copy()
            self.original_image_for_warp = self.original_image_full.copy()
            self.original_color_image = self.original_image_full.copy()
            self.zoom_level = 1.0
            self.blur_radius = 0
            self.alpha_level = 1.0
            self.is_grayscale_active.set(False) # Resetta anche la modalità colore
            self.gpu_accelerated_active = False # Resetta lo stato GPU
            
            # Applica la scala iniziale se l'immagine è troppo grande per il canvas
            # Questo è già gestito da display_image, che ridimensiona per adattarsi.
            self.display_image()
            self.update_status_bar("Immagine originale ripristinata.")
        else:
            self.show_canvas_message("Nessuna immagine originale da ripristinare.")


    def reset_zoom(self):
        # Questo metodo è simile a restore_original_image ma è chiamato "reset_zoom"
        # e le sue descrizioni non sono coerenti con l'effetto completo di "reset"
        # che invece è coperto da `restore_original_image`.
        # Se intendevi un reset che non tocca blur/alpha, andrebbe modificato.
        # Per ora, lo lascio come un reset parziale (solo zoom, blur, alpha).
        if self.original_image_full:
            # Reset solo di zoom, blur, alpha sul *current* self.image
            # Se vuoi ripartire dall'originale, usa self.restore_original_image
            # o imposta self.image = self.original_image_full.copy() qui.
            self.image = self.original_image_full.copy() # Lo imposto come un reset completo come il tuo `restore_original_image`
            self.original_image_for_warp = self.original_image_full.copy()
            self.original_color_image = self.original_image_full.copy()

            self.zoom_level = 1.0
            self.blur_radius = 0
            self.alpha_level = 1.0
            self.gpu_accelerated_active = False 
            
            if self.is_grayscale_active.get():
                self.image = self.image.convert("L").convert("RGB") 
            
            self.display_image()
            self.update_status_bar("Zoom, blur e alpha resettati.") # Modificato per riflettere il reset
        else:
            self.show_canvas_message("Nessuna immagine da ripristinare per lo zoom.")


    def blur_plus(self):
        if self.image:
            self.blur_radius += 1
            if self.blur_radius > 10: self.blur_radius = 10
            self.gpu_accelerated_active = False 
            self.display_image()
            self.update_status_bar(f"Blur: {self.blur_radius}")
        else:
            self.show_canvas_message("Carica un'immagine per applicare il blur.")

    def blur_minus(self):
        if self.image:
            self.blur_radius -= 1
            if self.blur_radius < 0: self.blur_radius = 0
            self.gpu_accelerated_active = False 
            self.display_image()
            self.update_status_bar(f"Blur: {self.blur_radius}")
        else:
            self.show_canvas_message("Carica un'immagine per applicare il blur.")

    def rotate_right(self):
        if self.image:
            self.image = self.image.rotate(-90, expand=True) 
            
            if self.original_image_for_warp: 
                self.original_image_for_warp = self.original_image_for_warp.rotate(-90, expand=True) 
            if self.original_image_full:
                self.original_image_full = self.original_image_full.rotate(-90, expand=True)
            if self.original_color_image:
                self.original_color_image = self.original_color_image.rotate(-90, expand=True)
            
            self.gpu_accelerated_active = False 
            self.display_image()
            self.update_status_bar("Ruotato di 90° a destra.")
        else:
            self.show_canvas_message("Carica un'immagine per ruotare.")

    def rotate_left(self):
        if self.image:
            self.image = self.image.rotate(90, expand=True) 
            
            if self.original_image_for_warp: 
                self.original_image_for_warp = self.original_image_for_warp.rotate(90, expand=True)
            if self.original_image_full:
                self.original_image_full = self.original_image_full.rotate(90, expand=True)
            if self.original_color_image:
                self.original_color_image = self.original_color_image.rotate(90, expand=True)

            self.gpu_accelerated_active = False 
            self.display_image()
            self.update_status_bar("Ruotato di 90° a sinistra.")
        else:
            self.show_canvas_message("Carica un'immagine per ruotare.")

    def alpha_plus(self):
        if self.image:
            self.alpha_level += 0.1
            if self.alpha_level > 1.0: self.alpha_level = 1.0
            self.gpu_accelerated_active = False 
            self.display_image()
            self.update_status_bar(f"Opacità (Alpha): {self.alpha_level:.1f}")
        else:
            self.show_canvas_message("Carica un'immagine per regolare l'opacità.")

    def alpha_minus(self):
        if self.image:
            self.alpha_level -= 0.1
            if self.alpha_level < 0.0: self.alpha_level = 0.0
            self.gpu_accelerated_active = False 
            self.display_image()
            self.update_status_bar(f"Opacità (Alpha): {self.alpha_level:.1f}")
        else:
            self.show_canvas_message("Carica un'immagine per regolare l'opacità.")

    def update_status_bar(self, message=None):
        grayscale_status = "B/N" if self.is_grayscale_active.get() else "Colori"
        gpu_status = f" | GPU: {'ON' if self.gpu_accelerated_active else 'OFF (CPU)'}" if self.device.type != 'cpu' else " | GPU: N/A (CPU Mode)"
        
        if message:
            self.status_bar.config(text=message + gpu_status)
        elif self.image:
            _, file_extension = os.path.splitext(self.current_image_path) if self.current_image_path else ("", "")
            self.status_bar.config(text=f"Immagine: {os.path.basename(self.current_image_path) if self.current_image_path else 'N/A'} "
                                         f"({self.image.width}x{self.image.height}px) | "
                                         f"Zoom: {self.zoom_level:.2f}x | Blur: {self.blur_radius} | "
                                         f"Alpha: {self.alpha_level:.1f} | "
                                         f"Warp: {'ON' if self.warp_active else 'OFF'} | "
                                         f"Colore: {grayscale_status}"
                                         f"{gpu_status}") 
        elif self.camera_active:
             self.status_bar.config(text="Fotocamera attiva..." + gpu_status)
        else:
            self.status_bar.config(text="Nessuna immagine caricata." + gpu_status)

    def update_warp_status(self):
        status = "ON" if self.warp_active else "OFF"
        self.warp_toggle_button.config(text=f"Warp: {status}")
        self.warp_status_bar.config(text=f"Warp: {status}")
        if self.warp_active:
            self.warp_status_bar.config(bg="lightcoral", fg="darkred")
        else:
            self.warp_status_bar.config(bg="lightblue", fg="darkblue")

    def toggle_camera(self):
        if not self.camera_active:
            self.start_camera()
        else:
            self.stop_camera()

    def start_camera(self):
        if self.image:
            self.close_image()
            
        self.camera_capture = cv2.VideoCapture(0)
        if not self.camera_capture.isOpened():
            messagebox.showerror("Errore Fotocamera", "Impossibile accedere alla fotocamera. Controlla che non sia già in uso e i permessi.")
            self.camera_active = False
            self.take_photo_button.config(state=tk.DISABLED)
            self.show_canvas_message("Fotocamera non disponibile.")
            return

        self.camera_active = True
        self.take_photo_button.config(state=tk.NORMAL)
        self.stop_camera_thread.clear()
        self.hide_canvas_message()
        self.gpu_accelerated_active = False 

        self.camera_thread = threading.Thread(target=self._camera_capture_loop)
        self.camera_thread.daemon = True
        self.camera_thread.start()

        self._update_camera_feed()

    def _camera_capture_loop(self):
        while not self.stop_camera_thread.is_set():
            ret, frame = self.camera_capture.read()
            if not ret:
                print("Errore nella lettura del frame dalla fotocamera.")
                self.show_canvas_message("Errore feed fotocamera.")
                break
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.current_camera_frame = Image.fromarray(frame_rgb)
        
        if self.camera_capture:
            self.camera_capture.release()
            print("Fotocamera rilasciata.")

    def _update_camera_feed(self):
        if self.camera_active and self.current_camera_frame:
            self.display_image(self.current_camera_frame)

        if self.camera_active:
            self.master.after(10, self._update_camera_feed)
        else:
            self.show_canvas_message("Nessuna immagine selezionata. Clicca su 'APRI' o 'ATTIVA FOTOCAMERA'")

    def stop_camera(self):
        if self.camera_active:
            self.camera_active = False
            self.stop_camera_thread.set()
            
            if self.camera_thread and self.camera_thread.is_alive():
                self.camera_thread.join(timeout=1.0)

            self.take_photo_button.config(state=tk.DISABLED)
            self.canvas.itemconfig(self.image_label, image="")
            self.tk_image = None
            self.current_camera_frame = None
            self.gpu_accelerated_active = False 
            print("Fotocamera disattivata.")
            self.show_canvas_message("Fotocamera disattivata.")

    def take_photo(self):
        if self.camera_active and self.current_camera_frame:
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                photo_filename = f"scatto_{timestamp}.png"
                save_path = os.path.join(script_dir, photo_filename)

                self.stop_camera() 
                self.current_camera_frame.save(save_path)
                self.load_image(save_path)
                messagebox.showinfo("Successo", f"Foto salvata e caricata come: {photo_filename}")
            except Exception as e:
                messagebox.showerror("Errore Salvataggio", f"Impossibile salvare la foto: {e}")
        else:
            self.show_canvas_message("La fotocamera non è attiva o non ci sono frame da scattare.")
    
    def on_closing(self):
        self.stop_camera()
        self._stop_warp_sound()
        self.master.destroy()

    def on_mouse_down(self, event):
        if self.image and not self.camera_active and self.zoom_box_active and not self.warp_active:
            self.start_x = event.x
            self.start_y = event.y
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", dash=(4, 2), width=2)
            self.gpu_accelerated_active = False 
            self.update_status_bar()
        elif not self.image:
            self.show_canvas_message("Carica un'immagine per utilizzare gli strumenti.")
    
    def on_mouse_drag(self, event):
        if self.rect_id and self.image and not self.camera_active and self.zoom_box_active and not self.warp_active:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_mouse_up(self, event):
        if self.rect_id and self.image and not self.camera_active and self.zoom_box_active and not self.warp_active:
            end_x, end_y = event.x, event.y

            self.canvas.delete(self.rect_id)
            self.rect_id = None

            x1 = min(self.start_x, end_x)
            y1 = min(self.start_y, end_y)
            x2 = max(self.start_x, end_x)
            y2 = max(self.start_y, end_y)

            if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
                self.show_canvas_message("Area di selezione troppo piccola per lo zoom. Selezionare un'area più grande.")
                self.display_image()
                self.start_x = None
                self.start_y = None
                return

            current_image_tk_width = self.tk_image.width()
            current_image_tk_height = self.tk_image.height()
            
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            x_offset = (canvas_width - current_image_tk_width) / 2
            y_offset = (canvas_height - current_image_tk_height) / 2

            relative_x1 = x1 - x_offset
            relative_y1 = y1 - y_offset
            relative_x2 = x2 - x_offset
            relative_y2 = y2 - y_offset

            relative_x1 = max(0, relative_x1)
            relative_y1 = max(0, relative_y1)
            relative_x2 = min(current_image_tk_width, relative_x2)
            relative_y2 = min(current_image_tk_height, relative_y2)

            current_displayed_image_pixel_width, current_displayed_image_pixel_height = self.image.size
            
            scale_to_original_x = current_displayed_image_pixel_width / current_image_tk_width
            scale_to_original_y = current_displayed_image_pixel_height / current_image_tk_height

            crop_x1 = int(relative_x1 * scale_to_original_x)
            crop_y1 = int(relative_y1 * scale_to_original_y)
            crop_x2 = int(relative_x2 * scale_to_original_x)
            crop_y2 = int(relative_y2 * scale_to_original_y)
            
            crop_x1 = max(0, crop_x1)
            crop_y1 = max(0, crop_y1)
            crop_x2 = min(current_displayed_image_pixel_width, crop_x2)
            crop_y2 = min(current_displayed_image_pixel_height, crop_y2)

            if crop_x2 <= crop_x1 or crop_y2 <= crop_y1:
                self.show_canvas_message("Area di crop invalida o troppo piccola per lo zoom. Riprova.")
                self.display_image()
                self.start_x = None
                self.start_y = None
                return

            try:
                self.image = self.image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                self.zoom_level = 1.0
                
                # Aggiorna la base colore e la base warp non-GPU con l'immagine croppata
                if self.original_color_image:
                    self.original_color_image = self.original_color_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))
                else: 
                     self.original_color_image = self.image.copy()

                self.original_image_for_warp = self.image.copy() 

                self.gpu_accelerated_active = False 
                self.display_image()
                self.update_status_bar(f"Zoom applicato all'area: ({crop_x1}, {crop_y1}) - ({crop_x2}, {crop_y2})")
            except Exception as e:
                messagebox.showerror("Errore Zoom", f"Impossibile applicare lo zoom: {e}") 
                self.display_image()
            
            self.start_x = None
            self.start_y = None

    def toggle_warp(self):
        if not self.image:
            self.show_canvas_message("Carica un'immagine per attivare l'effetto Warp.")
            return

        self.warp_active = not self.warp_active
        if self.warp_active:
            self.update_status_bar("Warp attivo. Clicca e trascina sull'immagine.")
            self._play_warp_sound()
            self.canvas.bind('<Button-1>', self._start_warp)
            self.canvas.bind('<B1-Motion>', self._apply_warp)
            self.canvas.bind('<ButtonRelease-1>', self._end_warp)
            self.zoom_box_active = False
            self.color_radio.config(state=tk.DISABLED)
            self.bw_radio.config(state=tk.DISABLED)
            self.gpu_accelerated_active = (self.device.type != 'cpu') 
        else:
            self.update_status_bar("Warp disattivato.")
            self._stop_warp_sound()
            self.canvas.unbind('<Button-1>')
            self.canvas.unbind('<B1-Motion>')
            self.canvas.unbind('<ButtonRelease-1>')
            self.canvas.bind('<Button-1>', self.on_mouse_down)
            self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
            self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
            
            if self.original_color_image:
                self.image = self.original_color_image.copy()
            
            if self.is_grayscale_active.get():
                self.image = self.image.convert("L").convert("RGB")

            self.gpu_accelerated_active = False 
            self.display_image()

            self.zoom_box_active = True
            self.color_radio.config(state=tk.NORMAL)
            self.bw_radio.config(state=tk.NORMAL)
        self.update_warp_status() 
        self.update_status_bar() 

    def _play_warp_sound(self):
        if not self.sound_playing:
            self.sound_playing = True
            self.sound_thread = threading.Thread(target=self._play_sound_loop)
            self.sound_thread.daemon = True
            self.sound_thread.start()


    def _play_sound_loop(self):
        """Riproduce il suono del warp in un loop finché self.sound_playing è True."""
        while self.sound_playing:
            try:
                playsound(self.warp_sound_path)
            except Exception as e:
                print(f"Errore nella riproduzione del suono warp: {e}")
                self.sound_playing = False # Ferma il loop in caso di errore
                break
            # Breve pausa per non sovraccaricare, se il suono è molto corto
            # o se vuoi che si ripeta con un piccolo intervallo.
            # Se il suono è lungo, non è necessario un time.sleep aggiuntivo.
            time.sleep(0.1) 

    def _stop_warp_sound(self):
        self.sound_playing = False
        if self.sound_thread and self.sound_thread.is_alive():
            # Aspetta che il thread del suono termini (se non è bloccato da playsound)
            # playsound può bloccare, quindi l'arresto non è sempre immediato.
            pass # Non fare join qui per non bloccare l'UI

    def _start_warp(self, event):
        if self.image:
            # Converte le coordinate del canvas in coordinate dell'immagine originale
            x_canvas, y_canvas = event.x, event.y
            img_x_offset = (self.canvas.winfo_width() - self.tk_image.width()) / 2
            img_y_offset = (self.canvas.winfo_height() - self.tk_image.height()) / 2

            x_tk_img = x_canvas - img_x_offset
            y_tk_img = y_canvas - img_y_offset

            # Scala le coordinate Tkinter alla dimensione dell'immagine originale PIL
            scale_x = self.image.width / self.tk_image.width()
            scale_y = self.image.height / self.tk_image.height()

            x_img = int(x_tk_img * scale_x)
            y_img = int(y_tk_img * scale_y)

            # Assicurati che le coordinate siano all'interno dei limiti dell'immagine
            x_img = max(0, min(x_img, self.image.width - 1))
            y_img = max(0, min(y_img, self.image.height - 1))
            
            # Salva la posizione iniziale del mouse per le operazioni di trascinamento
            self.last_warp_point = (x_img, y_img)

            # Prepara l'immagine originale per il warp (copia per GPU o CPU)
            if self.gpu_accelerated_active:
                # Se la GPU è attiva, converti l'immagine PIL in un tensore PyTorch
                # e spostala sul dispositivo GPU (MPS/CUDA).
                # Solo se non è già stata convertita o se l'immagine è cambiata.
                if self.original_image_for_warp_tensor is None or self.original_image_for_warp.size != self.image.size:
                    np_img = np.array(self.original_color_image.convert("RGB")) / 255.0
                    self.original_image_for_warp_tensor = torch.tensor(np_img, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0).to(self.device)
                self.current_gpu_warped_image_tensor = self.original_image_for_warp_tensor.clone() # Clona per le modifiche
            else:
                self.original_image_for_warp = self.image.copy() # Per il warp CPU, lavoriamo sulla copia corrente dell'immagine

            # Applica il warp immediatamente al click iniziale per mostrare l'effetto
            self._apply_warp(event)
        else:
            self.show_canvas_message("Carica un'immagine per applicare il warp.")

    def _apply_warp(self, event):
        if self.warp_active and self.image:
            x_canvas, y_canvas = event.x, event.y
            img_x_offset = (self.canvas.winfo_width() - self.tk_image.width()) / 2
            img_y_offset = (self.canvas.winfo_height() - self.tk_image.height()) / 2

            x_tk_img = x_canvas - img_x_offset
            y_tk_img = y_canvas - img_y_offset

            scale_x = self.image.width / self.tk_image.width()
            scale_y = self.image.height / self.tk_image.height()

            x_img = int(x_tk_img * scale_x)
            y_img = int(y_tk_img * scale_y)
            
            # Assicurati che le coordinate siano all'interno dei limiti dell'immagine
            x_img = max(0, min(x_img, self.image.width - 1))
            y_img = max(0, min(y_img, self.image.height - 1))

            if self.gpu_accelerated_active:
                self._apply_warp_gpu(x_img, y_img)
            else:
                self._apply_warp_cpu(x_img, y_img)
            self.update_status_bar()

    def _end_warp(self, event):
        # Quando il mouse viene rilasciato, l'immagine corrente diventa la nuova base per future modifiche
        if self.warp_active and self.image:
            # Se stiamo usando la GPU, dobbiamo convertire l'immagine warappata dal tensore
            # di nuovo in un'immagine PIL e assegnarla a self.image.
            if self.gpu_accelerated_active and self.current_gpu_warped_image_tensor is not None:
                img_array = self.current_gpu_warped_image_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
                self.image = Image.fromarray((img_array * 255).astype(np.uint8))
                self.original_image_for_warp_tensor = None # Resetta per ricaricare alla prossima attivazione del warp
            
            # Aggiorna anche l'immagine "originale a colori" che viene usata per il toggle B/N
            self.original_color_image = self.image.copy()
            # E l'immagine per il warp non-GPU
            self.original_image_for_warp = self.image.copy()
            
            self.display_image() # Aggiorna la visualizzazione finale
            self.update_status_bar("Warp applicato e finalizzato.")
        self.last_warp_point = None

    def _apply_warp_cpu(self, x, y):
        # Placeholder: Questa è l'implementazione del warp via CPU
        # Devi integrare qui la tua logica di warp.
        # Questo è un esempio molto semplificato di "pinch" o "bulge".
        if self.original_image_for_warp is None:
            self.original_image_for_warp = self.image.copy()

        img_np = np.array(self.original_image_for_warp)
        h, w, c = img_np.shape
        
        # Crea una mesh di coordinate
        coords = np.indices((h, w)).astype(np.float32)
        cy, cx = coords[0], coords[1]
        
        # Calcola la distanza dal punto centrale (x, y)
        dist_sq = (cx - x)**2 + (cy - y)**2
        
        # Maschera per l'area di effetto
        mask = dist_sq < self.warp_radius**2
        
        # Normalizza la distanza per il calcolo della forza
        normalized_dist = np.sqrt(dist_sq) / self.warp_radius
        normalized_dist[normalized_dist > 1] = 1 # Clampa a 1
        
        # Calcola il fattore di distorsione (inverso della distanza per effetto lente)
        # Il fattore di distorsione è massimo al centro e diminuisce verso il bordo
        # strength viene applicato in modo inverso per "magnify"
        # 1 - normalized_dist fa sì che sia 1 al centro e 0 al bordo
        # (1 - normalized_dist)**2 rende la transizione più morbida
        # Il self.warp_strength controlla quanto è forte l'ingrandimento
        distortion_factor = (1 - normalized_dist)**2 * self.warp_strength

        # Calcola lo spostamento delle coordinate
        delta_x = (cx - x) * distortion_factor
        delta_y = (cy - y) * distortion_factor

        # Applica lo spostamento, ma in direzione opposta per "ingrandire"
        # O per "spostare" i pixel verso il centro
        new_cx = cx - delta_x
        new_cy = cy - delta_y

        # Limita le nuove coordinate ai bordi dell'immagine
        new_cx = np.clip(new_cx, 0, w - 1)
        new_cy = np.clip(new_cy, 0, h - 1)
        
        # Usa remap di OpenCV per applicare la distorsione
        # Assicurati che new_cx e new_cy siano di tipo float32
        warped_img_np = cv2.remap(img_np, new_cx.astype(np.float32), new_cy.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        
        self.image = Image.fromarray(warped_img_np.astype(np.uint8))
        self.display_image()

    def _apply_warp_gpu(self, x, y):
        # Placeholder: Questa è l'implementazione del warp via GPU (PyTorch)
        # Devi integrare qui la tua logica di warp PyTorch.
        # Questo è un esempio di "bulge" o "pinch" usando PyTorch.
        if self.original_image_for_warp_tensor is None:
            # Prepara il tensore dell'immagine se non è già pronto
            np_img = np.array(self.original_color_image.convert("RGB")) / 255.0
            self.original_image_for_warp_tensor = torch.tensor(np_img, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0).to(self.device)
        
        # Clona l'originale per non modificare la base
        img_tensor = self.original_image_for_warp_tensor.clone()
        _, _, H, W = img_tensor.shape

        # Crea una griglia di coordinate normalizzate (-1 a 1)
        # Queste sono le coordinate di output, stiamo cercando dove "prendere" i pixel
        # dalla sorgente per riempire la destinazione.
        grid_x, grid_y = torch.meshgrid(torch.linspace(-1, 1, W, device=self.device), 
                                        torch.linspace(-1, 1, H, device=self.device), indexing='xy')
        grid = torch.stack((grid_x, grid_y), dim=-1) # Shape: (H, W, 2)

        # Converte le coordinate del punto di warp da pixel a normalizzate
        center_x_norm = (x / W) * 2 - 1
        center_y_norm = (y / H) * 2 - 1

        # Calcola la distanza dal centro del warp in coordinate normalizzate
        # Usiamo il raggio in pixel, ma lo normalizziamo per il calcolo della distanza
        # rispetto alle dimensioni normalizzate della griglia.
        # Il raggio normalizzato sarà differente per X e Y se l'immagine non è quadrata,
        # ma per un effetto circolare, è meglio usare un raggio proporzionato alla dimensione minore.
        # Usiamo il raggio in pixel e lo normalizziamo rispetto alla dimensione maggiore
        # o alla media delle dimensioni per coerenza.
        # Per semplicità qui normalizzo rispetto a W (o H), assumendo un raggio circolare.
        radius_norm = (self.warp_radius / min(H, W)) * 2 # Approssimazione per il raggio in spazio normalizzato

        # Calcola la distanza di ogni punto della griglia dal centro del warp
        dist_from_center = torch.sqrt(
            (grid[:, :, 0] - center_x_norm)**2 + 
            (grid[:, :, 1] - center_y_norm)**2
        )

        # Crea una maschera per i pixel all'interno del raggio di influenza
        # Utilizza un raggio normalizzato per la maschera
        mask = dist_from_center < radius_norm

        # Calcola il fattore di distorsione
        # Vogliamo un effetto "ingrandimento", quindi i pixel vicino al centro si spostano meno
        # e quelli più lontani si spostano di più verso il centro (o l'originale)
        
        # Questa formula sposta i pixel dal centro verso l'esterno, creando un "bulge".
        # Per un effetto "lente d'ingrandimento" (pinch/ingrandimento al centro),
        # i pixel all'interno del raggio devono essere spostati *verso* il centro.
        # Un modo per farlo è calcolare il punto di origine inverso.
        
        # Calcola la "magnification factor" che è più forte al centro e diminuisce verso il bordo
        # (1 - (dist_from_center / radius_norm)) è 1 al centro, 0 al bordo.
        # Elevando a potenza si controlla la curva di attenuazione.
        magnification_factor = (1 - (dist_from_center / radius_norm)).pow(2) * self.warp_strength
        magnification_factor = magnification_factor * mask.float() # Applica solo nell'area di interesse

        # Sposta le coordinate dei pixel.
        # Per ingrandire, i pixel che stiamo *campionando* (quelli della griglia di lookup)
        # devono essere "schiacciati" verso il centro.
        # (original_coord - center_coord) è la distanza dal centro.
        # Moltiplicare per (1 - factor) li avvicina al centro.
        
        warped_grid_x = center_x_norm + (grid[:, :, 0] - center_x_norm) * (1 - magnification_factor)
        warped_grid_y = center_y_norm + (grid[:, :, 1] - center_y_norm) * (1 - magnification_factor)

        warped_grid = torch.stack((warped_grid_x, warped_grid_y), dim=-1).unsqueeze(0) # Aggiunge la dimensione batch

        # Applica la griglia warappata all'immagine originale
        # grid_sample richiede input NCHW e grid N H W 2
        warped_tensor = F.grid_sample(img_tensor, warped_grid, mode='bilinear', padding_mode='reflection', align_corners=True)

        # Aggiorna l'immagine visualizzata
        img_array = warped_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()
        self.image = Image.fromarray((img_array * 255).astype(np.uint8))
        self.current_gpu_warped_image_tensor = warped_tensor # Salva per il trascinamento continuo

        self.display_image()


    def on_grayscale_selection(self):
        if self.image is None and not self.camera_active:
            # Se non c'è un'immagine caricata e non è attiva la fotocamera,
            # non fare nulla ma potresti voler mostrare un messaggio.
            # self.show_canvas_message("Carica un'immagine prima di cambiare modalità colore.")
            return

        if self.warp_active:
            # Se il warp è attivo, blocchiamo il cambio di colore
            self.is_grayscale_active.set(not self.is_grayscale_active.get()) # Reset dello stato precedente
            messagebox.showinfo("Avviso", "La modalità colore non può essere cambiata mentre il Warp è attivo.")
            return

        if self.is_grayscale_active.get():
            # Passa a bianco e nero
            if self.image:
                # Usa self.original_color_image come base per convertire in B/N
                # Questo assicura che il B/N sia sempre basato sull'immagine a colori originale
                # o sulla sua ultima versione modificata non-warp.
                self.image = self.original_color_image.convert("L").convert("RGB")
        else:
            # Passa a colori (ripristina l'immagine a colori originale)
            if self.image:
                self.image = self.original_color_image.copy()

        self.gpu_accelerated_active = False # Reset GPU status on color mode change
        self.display_image()
        self.update_status_bar()
        
    

    def handle_mouse_motion(self, event):
        if self.image:
            # Qui puoi aggiungere logica per mostrare coordinate o altre info
            # print(f"Mouse at: {event.x}, {event.y}")
            pass

    def handle_mouse_leave(self, event):
        # Azioni quando il mouse lascia il canvas (es. nascondere informazioni)
        pass
    
    def update_cartoonize(self, new_value):
        # 'new_value' è il valore dello slider, da 0 a 100
        
        # Per sicurezza, converti il valore in un float
        try:
            new_value = float(new_value)
        except (ValueError, TypeError):
            return
    
        # Se il valore è 0, mostra l'immagine originale
        if new_value == 0:
            # Usa il nome corretto della variabile: self.original_image_full
            self.image = self.original_image_full.copy()
            self.display_image()
            return
    
        # Converte il valore dello slider in un fattore di controllo
        strength = int(new_value / 10) + 1 
        
        # Converti l'immagine da PIL a un array NumPy in formato OpenCV (BGR)
        # Usa il nome corretto della variabile qui
        img_bgr = cv2.cvtColor(np.array(self.original_image_full.convert("RGB")), cv2.COLOR_RGB2BGR)
    
        # Passo 1: Edge-Aware Smoothing (Filtro Bilaterale)
        img_smoothed = cv2.bilateralFilter(img_bgr, d=9, sigmaColor=strength * 10, sigmaSpace=strength * 10)
        
        # Passo 2: Rilevamento Bordi
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.adaptiveThreshold(
            img_gray, 255, 
            cv2.ADAPTIVE_THRESH_MEAN_C, 
            cv2.THRESH_BINARY, 
            blockSize=9, C=2
        )
        
        # Passo 3: Combinazione
        img_cartoonized = cv2.bitwise_and(img_smoothed, img_smoothed, mask=edges)
        
        # Converte l'immagine risultante in PIL e la visualizza
        self.image = Image.fromarray(cv2.cvtColor(img_cartoonized, cv2.COLOR_BGR2RGB))
        self.display_image()
        
    
    def remove_ai_background(self):
        if self.image is None:
            self.show_canvas_message("Carica un'immagine per rimuovere lo sfondo.")
            return

        self.update_status_bar("Rimuovendo lo sfondo con AI... (potrebbe richiedere qualche istante)")
        self.master.update_idletasks() # Forza l'aggiornamento della UI

        try:
        # Converti PIL Image in bytes per rembg
           img_byte_arr = io.BytesIO()
           self.image.save(img_byte_arr, format='PNG') # PNG supporta l'alpha
           img_byte_arr = img_byte_arr.getvalue()

        # Usa rembg per la rimozione dello sfondo
        # rembg usa modelli ONNX, ma può sfruttare la GPU se onnxruntime-gpu è installato
        # Il parametro `g_model` seleziona il modello. 'u2net' è un buon default.
           output_bytes = remove(img_byte_arr,
                                 alpha_matting=True,
                                 alpha_matting_foreground_threshold=240,
                                 alpha_matting_background_threshold=10, 
                                 alpha_matting_erode_size=11,
                                 # Aggiungi il parametro providers qui:
                                 providers=['CoreMLExecutionProvider', 'CPUExecutionProvider']
                                 )

        # Converti i bytes di nuovo in PIL Image
           output_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
 
           self.image = output_image
           self.display_image()
           self.update_status_bar("Sfondo rimosso con AI.")
 
        except Exception as e:
               
            messagebox.showerror("Errore Rimozione Sfondo AI", f"Errore: {e}\nAssicurati di avere `rembg` installato correttamente.")
            self.update_status_bar("Rimozione sfondo AI fallita.")
            
            # richiamo funzione per CARTONIZZARE Assumi che self.original_image sia l'immagine originale (un oggetto PIL)
# e self.display_image() sia la funzione per aggiornare il canvas
 


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoEditorApp(root)
    root.mainloop()