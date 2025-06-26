#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 25 17:36:54 2025

@author: macbook_vincenzo
"""
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter, ExifTags
import os
import math

from playsound import playsound #per riproduzione del suono in modalità WARP
import threading

class PhotoEditorApp:
    def __init__(self, master):
        self.master = master
        master.title("Il Mio Photo Tool")
        self.warp_sound_path = "/Users/macbook_vincenzo/Python/sounds/213693__taira-komori__warp1.mp3"
        self.sound_thread = None # Per tenere traccia del thread del suono
        self.sound_playing = False # Flag per sapere se un suono è già in riproduzione
        # Inizializza TUTTE le variabili di stato subito!
        self.image = None
        self.original_image_for_warp = None
        self.tk_image = None
        self.current_image_path = None
        self.zoom_level = 1.0
        self.blur_radius = 0
        
        self.warp_active = False
        self.warp_radius = 100
        self.warp_strength = 2

        self.create_widgets()
        # Aggiorna lo stato iniziale del warp bar dopo la creazione dei widget
        self.update_warp_status() 


    def create_widgets(self):
        # --- 1. Status Bar Principale ---
        self.status_bar = tk.Label(self.master, text="Nessuna immagine caricata.", bd=1, relief=tk.SUNKEN, anchor=tk.W, justify=tk.LEFT)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- 2. Status Bar del Warp (Nuova Label per il debugging) ---
        self.warp_status_bar = tk.Label(self.master, text="Warp: OFF", bd=1, relief=tk.FLAT, anchor=tk.E, bg="lightblue", fg="darkblue", font=('Helvetica', 10, 'bold'))
        self.warp_status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- 3. Frame Principale per il Contenuto ---
        main_content_area = tk.Frame(self.master)
        main_content_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # --- 4. Frame dei Bottoni ---
        button_frame = tk.Frame(main_content_area)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # --- 5. Area di Visualizzazione Immagine ---
        self.image_display_frame = tk.Frame(main_content_area, bg="lightgrey")
        self.image_display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.image_label = tk.Label(self.image_display_frame)
        self.image_label.pack(expand=True)

        # --- Binding per il Warp/Hover ---
        self.image_label.bind('<Motion>', self.handle_mouse_motion)
        self.image_label.bind('<Leave>', self.handle_mouse_leave)
        
        # Bottone per attivare/disattivare l'effetto warp
        self.warp_toggle_button = tk.Button(button_frame, text="Warp: OFF", command=self.toggle_warp)
        self.warp_toggle_button.pack(pady=5, fill=tk.X)


        # --- Controlli (Bottoni) ---
        self.open_button = tk.Button(button_frame, text="APRI", command=self.open_image)
        self.open_button.pack(pady=5, fill=tk.X)

        self.close_button = tk.Button(button_frame, text="CHIUDI", command=self.close_image)
        self.close_button.pack(pady=5, fill=tk.X)

        tk.Frame(button_frame, height=1, bg="grey").pack(fill=tk.X, pady=10)

        self.zoom_in_button = tk.Button(button_frame, text="ZOOM +", command=self.zoom_in)
        self.zoom_in_button.pack(pady=5, fill=tk.X)

        self.zoom_out_button = tk.Button(button_frame, text="ZOOM -", command=self.zoom_out)
        self.zoom_out_button.pack(pady=5, fill=tk.X)

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


    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Tutti i file immagine", "*.png;*.gif;*.bmp;*.tiff;*.jp2;*.jpg;*.jpeg;*.JPG;*.JPEG"),
                ("JPEG 2000", "*.jp2"),
                ("Immagini PNG", "*.png"),
                ("Immagini JPEG", "*.jpg;*.jpeg;*.JPG;*.JPEG"),
                ("Tutti i file", "*.*")
            ]
        )
        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path):
        try:
            self.image = Image.open(file_path)
            # Salva la copia per il warp subito dopo aver caricato l'immagine principale
            self.original_image_for_warp = self.image.copy() 
            self.current_image_path = file_path
            self.zoom_level = 1.0
            self.blur_radius = 0
            self.display_image()
            self.update_status_bar()
            self.update_warp_status()
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile caricare l'immagine: {e}")
            self.close_image() # Chiama close_image per resettare lo stato in caso di errore
            self.update_status_bar() # Aggiorna le status bar dopo il reset
            self.update_warp_status()

    def display_image(self, warped_image=None):
        current_image_to_display = warped_image if warped_image else self.image

        if current_image_to_display:
            width, height = current_image_to_display.size
            new_width = int(width * self.zoom_level)
            new_height = int(height * self.zoom_level)
            if new_width == 0: new_width = 1
            if new_height == 0: new_height = 1

            if not warped_image:
                resized_image = current_image_to_display.resize((new_width, new_height), Image.LANCZOS)
                if self.blur_radius > 0:
                    resized_image = resized_image.filter(ImageFilter.GaussianBlur(self.blur_radius))
            else:
                # Se è già deformata, facciamo solo il resize (blur e rotazione sono sull'originale)
                resized_image = current_image_to_display.resize((new_width, new_height), Image.LANCZOS)

            self.tk_image = ImageTk.PhotoImage(resized_image)
            self.image_label.config(image=self.tk_image)
            self.image_label.image = self.tk_image
        else:
            self.image_label.config(image="")

    def close_image(self):
        self.image = None
        self.original_image_for_warp = None # Resetta anche l'immagine per il warp
        self.tk_image = None
        self.current_image_path = None
        self.zoom_level = 1.0
        self.blur_radius = 0
        self.display_image()
        self.update_status_bar()
        self.update_warp_status()

    # Le funzioni zoom_in, zoom_out, blur_plus, blur_minus, rotate_right, rotate_left
    # sono lasciate invariate rispetto alla tua ultima versione.
    # Assicurati che rotate_right/left aggiornino self.original_image_for_warp.

    def zoom_in(self):
        if self.image:
            self.zoom_level *= 1.2
            self.display_image()
            self.update_status_bar()

    def zoom_out(self):
        if self.image:
            self.zoom_level /= 1.2
            if self.zoom_level < 0.1:
                self.zoom_level = 0.1
            self.display_image()
            self.update_status_bar()

    def blur_plus(self):
        if self.image:
            self.blur_radius += 1
            # Quando il blur o la rotazione cambia, l'immagine originale per il warp deve riflettere queste modifiche
            # Questo è un punto critico: decidere se il warp opera sull'immagine originale o sull'immagine modificata.
            # Per semplicità, il warp opererà sulla versione attuale di self.image (che include blur, zoom implicito nel ridimensionamento).
            self.display_image() # Display normale, senza warp
            self.update_status_bar()

    def blur_minus(self):
        if self.image and self.blur_radius > 0:
            self.blur_radius -= 1
            self.display_image()
            self.update_status_bar()

    def rotate_right(self):
        if self.image:
            self.image = self.image.rotate(-90, expand=True)
            self.original_image_for_warp = self.image.copy() # Aggiorna la copia per il warp
            self.display_image()
            self.update_status_bar()

    def rotate_left(self):
        if self.image:
            self.image = self.image.rotate(90, expand=True)
            self.original_image_for_warp = self.image.copy() # Aggiorna la copia per il warp
            self.display_image()
            self.update_status_bar()

    def update_status_bar(self):
        if self.image and self.current_image_path:
            file_name = os.path.basename(self.current_image_path)
            file_path = os.path.dirname(self.current_image_path)

            try:
                file_size_bytes = os.path.getsize(self.current_image_path)
                if file_size_bytes > 1024 * 1024:
                    file_size_display = f"{file_size_bytes / (1024 * 1024):.2f} MB"
                elif file_size_bytes > 1024:
                    file_size_display = f"{file_size_bytes / 1024:.2f} KB"
                else:
                    file_size_display = f"{file_size_bytes} Bytes"
            except OSError:
                file_size_display = "N/D"

            exif_data = {}
            try:
                exif_raw = self.image._getexif()
                if exif_raw:
                    for tag_id, value in exif_raw.items():
                        tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                        exif_data[tag_name] = value
            except Exception:
                pass

            status_text = f"File: {file_name} | Dimensione: {file_size_display}\n" \
                          f"Percorso: {file_path}\n" \
                          f"Risoluzione: {self.image.width}x{self.image.height} px | Zoom: {self.zoom_level*100:.0f}% | Blur: {self.blur_radius}"

            if exif_data:
                exif_info_parts = []
                if 'DateTimeOriginal' in exif_data:
                    exif_info_parts.append(f"Data: {exif_data['DateTimeOriginal'].split(' ')[0]}")
                if 'Make' in exif_data:
                    camera_info = exif_data['Make']
                    if 'Model' in exif_data:
                        camera_info += f" {exif_data['Model']}"
                    exif_info_parts.append(f"Fotocamera: {camera_info}")
                if 'FNumber' in exif_data:
                    exif_info_parts.append(f"Apertura: f/{exif_data['FNumber']}")
                if 'ExposureTime' in exif_data:
                    exif_info_parts.append(f"Esposizione: {exif_data['ExposureTime']}")
                
                if exif_info_parts:
                    status_text += "\n" + " | ".join(exif_info_parts)

            self.status_bar.config(text=status_text)
        else:
            self.status_bar.config(text="Nessuna immagine caricata.")
    
    def update_warp_status(self):
        # Controlla se self.warp_status_bar è stato creato prima di usarlo
        if hasattr(self, 'warp_status_bar'):
            status_text = f"Warp: {'ON' if self.warp_active else 'OFF'}"
            bg_color = "lightgreen" if self.warp_active else "lightblue"
            fg_color = "darkgreen" if self.warp_active else "darkblue"
            self.warp_status_bar.config(text=status_text, bg=bg_color, fg=fg_color)
        else:
            # Questo blocco è solo per debugging iniziale se la barra non si crea
            print("Warning: warp_status_bar not yet created.")
  
    # --- Metodi per il Warp e il Suono ---

    def toggle_warp(self):
        self.warp_active = not self.warp_active
        self.warp_toggle_button.config(text=f"Warp: {'ON' if self.warp_active else 'OFF'}")
        self.update_warp_status()
        if not self.warp_active: # Se disattiviamo il warp
               self.display_image() # Ripristina l'immagine originale
               self._stop_warp_sound() # Ferma il suono

    def _play_sound(self):
     """Metodo interno per riprodurre il suono. Eseguito in un thread."""
     if not os.path.exists(self.warp_sound_path):
         print(f"Errore: File suono non trovato: {self.warp_sound_path}")
         self.sound_playing = False # Resetta il flag
         return

     try:
         playsound(self.warp_sound_path)
     except Exception as e:
         print(f"Errore durante la riproduzione del suono: {e}")
     finally:
         self.sound_playing = False # Resetta il flag una volta che il suono è finito

    def _stop_warp_sound(self):
     """Simula l'interruzione del suono (playsound non ha una API stop diretta)."""
     # Con playsound, non c'è un modo diretto per "fermare" un suono in riproduzione.
     # Possiamo solo impedire che nuovi suoni partano o aspettare che quelli in corso finiscano.
     # Se il suono è breve, questo è accettabile.
     # Se fosse un suono lungo, si dovrebbe usare una libreria come pygame.mixer.
     self.sound_playing = False # Indica che non vogliamo che riparta automaticamente

     # Se il thread è ancora in esecuzione, non possiamo "terminarlo" forzatamente,
     # ma possiamo aspettare che finisca il suo lavoro o ignorarlo.
     # Per ora, la semplice gestione del flag sound_playing è sufficiente.
     if self.sound_thread and self.sound_thread.is_alive():
         print("Warp sound thread still alive, but flag set to stop new ones.")



    # --- Metodi per il Warp ---

    def toggle_warp(self):
        self.warp_active = not self.warp_active
        # Aggiorna il testo del bottone immediatamente
        self.warp_toggle_button.config(text=f"Warp: {'ON' if self.warp_active else 'OFF'}")
        self.update_warp_status() # Aggiorna la nuova status bar del warp
        if not self.warp_active and self.image:
            self.display_image() # Se disattiviamo, ripristina l'immagine originale

    def handle_mouse_motion(self, event):
        # Controllo iniziale: l'immagine deve essere caricata E il warp attivo
        if self.image is None or self.original_image_for_warp is None or not self.warp_active:
            return # Esci se non c'è immagine o il warp non è attivo
        
        # Avvia il suono in un thread separato solo se non sta già suonando
        if not self.sound_playing:
           self.sound_playing = True
           # Target è la funzione che il thread eseguirà
           self.sound_thread = threading.Thread(target=self._play_sound)
           self.sound_thread.daemon = True # Il thread termina quando il programma principale termina
           self.sound_thread.start() # Avvia il thread

           img_width, img_height = self.image_label.winfo_width(), self.image_label.winfo_height()
        
           current_displayed_width = int(self.image.width * self.zoom_level)
           current_displayed_height = int(self.image.height * self.zoom_level)

        # Evita divisione per zero e calcoli errati se l'immagine visualizzata è 0x0
        if current_displayed_width <= 0 or current_displayed_height <= 0:
            self._stop_warp_sound()
            return

        x_offset = (img_width - current_displayed_width) / 2
        y_offset = (img_height - current_displayed_height) / 2

        mouse_x_on_image = event.x - x_offset
        mouse_y_on_image = event.y - y_offset

        original_x = int(mouse_x_on_image * (self.original_image_for_warp.width / current_displayed_width))
        original_y = int(mouse_y_on_image * (self.original_image_for_warp.height / current_displayed_height))

        warped_img = self._apply_warp_effect(original_x, original_y)
        if warped_img:
            self.display_image(warped_img)

    def handle_mouse_leave(self, event):
        if self.image and self.warp_active:
            self.display_image()
            self._stop_warp_sound() # Ferma il suono quando il mouse lascia l'immagine

    def _apply_warp_effect(self, center_x, center_y):
        if not self.original_image_for_warp:
            return None

        img_to_warp = self.original_image_for_warp.copy()
        if self.blur_radius > 0:
            img_to_warp = img_to_warp.filter(ImageFilter.GaussianBlur(self.blur_radius))

        distorted_img = Image.new("RGB", img_to_warp.size)
        pixels_original = img_to_warp.load()
        pixels_distorted = distorted_img.load()
        
        width, height = img_to_warp.size
        
        radius_sq = self.warp_radius * self.warp_radius

        for x_distorted in range(width):
            for y_distorted in range(height):
                dx = x_distorted - center_x
                dy = y_distorted - center_y
                distance_sq = dx*dx + dy*dy
                
                if distance_sq < radius_sq:
                    distance = math.sqrt(distance_sq)
                    if distance == 0:
                        pixels_distorted[x_distorted, y_distorted] = pixels_original[x_distorted, y_distorted]
                        continue

                    factor = 1.0 - (distance / self.warp_radius) ** self.warp_strength
                    
                    x_original = int(center_x + dx * factor)
                    y_original = int(center_y + dy * factor)

                    if 0 <= x_original < width and 0 <= y_original < height:
                        pixels_distorted[x_distorted, y_distorted] = pixels_original[x_original, y_original]
                    else:
                        pixels_distorted[x_distorted, y_distorted] = (0, 0, 0) # Nero per i pixel fuori raggio
                else:
                    pixels_distorted[x_distorted, y_distorted] = pixels_original[x_distorted, y_distorted]
        
        return distorted_img


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoEditorApp(root)
    root.mainloop()