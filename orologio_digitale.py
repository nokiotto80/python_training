#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 13 16:49:48 2025

@author: macbook_vincenzo
A.I. created by Google Gemini 
successively modified
MODIFICARE, AGGIUNGERE LA DATA SOTTO, usando i "pezzi" da lui generati. possibilemnte SENZA chiedere
a GEMINI,,,un po di esercizio non guasta!
"""

import tkinter as tk
import time
from tkinter import PhotoImage
from PIL import Image, ImageTk # Aggiungi queste importazioni se vuoi usare PNG con trasparenza


class DigitalClock:
    def __init__(self, root):
        
        self.root = root
        self.root.title("Orologio Digitale 7 Segmenti")
        self.root.geometry("650x270") # Dimensione della finestra
        self.root.resizable(False, False) # Non ridimensionabile

        self.segment_color_on = "red"  # Colore dei segmenti accesi
        self.segment_color_off = "#330000" # Colore dei segmenti spenti (grigio scuro/rosso molto scuro)
        self.bg_color = "black" # Colore di sfondo del display

        self.segment_width = 10 # Spessore dei segmenti
        self.digit_width = 60 # Larghezza di una singola cifra
        self.digit_height = 100 # Altezza di una singola cifra
        self.padding = 10 # Spazio tra le cifre
        self.colon_width = 15 # Larghezza dei punti dei due punti
        

        # Definizioni dei segmenti per ogni numero (0-9)
        # Ogni tuple rappresenta (segment_A, segment_B, ..., segment_G)
        # True = segmento acceso, False = segmento spento
        self.segments_map = {
            '0': (True, True, True, True, True, True, False),  # A B C D E F G
            '1': (False, True, True, False, False, False, False),
            '2': (True, True, False, True, True, False, True),
            '3': (True, True, True, True, False, False, True),
            '4': (False, True, True, False, False, True, True),
            '5': (True, False, True, True, False, True, True),
            '6': (True, False, True, True, True, True, True),
            '7': (True, True, True, False, False, False, False),
            '8': (True, True, True, True, True, True, True),
            '9': (True, True, True, True, False, True, True),
            ' ': (False, False, False, False, False, False, False) # Per spazio vuoto
        }
        
        self.segments_map_lettere = {
            'A': (True, True, True, False, True, True, True),  # A B C D E F G
            'B': (True, True, True, True, True, True, True),#COME numero 8

            ' ': (False, False, False, False, False, False, False) # Per spazio vuoto
        }

        # Creazione del Canvas principale per il display dell'orologio
        self.canvas = tk.Canvas(root, bg=self.bg_color, highlightthickness=2)
       
        self.canvas.pack(expand=True, fill="both")
        
        # --- INIZIO MODIFICHE PER L'ICONA ---
        try:
      # Per supportare i file PNG con trasparenza, è consigliabile usare Pillow (PIL).
      # Assicurati di averla installata: pip install Pillow
      
      # Carica l'immagine usando Pillow
         original_image = Image.open("/Users/macbook_vincenzo/Python/clock_icon.png")
      
      # Ridimensiona l'immagine se necessario (es. a 60x60 pixel)
       # Puoi regolare queste dimensioni in base a quanto vuoi che sia grande l'icona
         resized_image = original_image.resize((50, 50), Image.LANCZOS) # o Image.LANCZOS per migliore qualità
       
      # Converte l'immagine Pillow in un formato che Tkinter può usare
         self.clock_icon = ImageTk.PhotoImage(resized_image)
      
      # Mostra l'icona dell'orologio prima dell'ora
      # Le coordinate (x, y) definiscono il centro dell'immagine per anchor="center"
      # O (x, y) definiscono il punto sinistro per anchor="w" (West)
      # Regola le coordinate 50, 50 in base a dove vuoi posizionare l'icona
      # Il 50 in X è una posizione di esempio, potresti volerlo più a sinistra
         self.canvas.create_image(25, self.digit_height / 2 + self.padding, anchor="w",image=self.clock_icon)
      
        except FileNotFoundError:
         print("Errore: Immagine 'clock_icon.png' non trovata. Assicurati che il percorso sia corretto.")
        except Exception as e:
         print(f"Si è verificato un errore durante il caricamento dell'immagine: {e}")
  # --- FINE MODIFICHE PER L'ICONA ---

        # Memorizzeremo gli oggetti Canvas per ogni cifra (ore, minuti, secondi) , per i due punti e le lettere
        self.digits = []
        self.letters = []
        self.colons = []

        # Posizionamento delle cifre e dei due punti
        # Ore
        self.digits.append(self.create_digit_display(self.padding)) # Prima cifra ore
        self.digits.append(self.create_digit_display(self.padding + self.digit_width + self.padding)) # Seconda cifra ore

        # Primo gruppo di due punti
        self.colons.append(self.create_colon_display(self.padding + 2 * (self.digit_width + self.padding)))

        # Minuti
        self.digits.append(self.create_digit_display(self.padding + 2 * (self.digit_width + self.padding) + self.colon_width + self.padding)) # Prima cifra minuti
        self.digits.append(self.create_digit_display(self.padding + 3 * (self.digit_width + self.padding) + self.colon_width + self.padding)) # Seconda cifra minuti

        # Secondo gruppo di due punti (opzionale, se vuoi anche i secondi)
        self.colons.append(self.create_colon_display(self.padding + 4 * (self.digit_width + self.padding) + self.colon_width + self.padding))

        # Secondi (opzionale)
        self.digits.append(self.create_digit_display(self.padding + 4 * (self.digit_width + self.padding) + 2 * self.colon_width + 2 * self.padding)) # Prima cifra secondi
        self.digits.append(self.create_digit_display(self.padding + 5 * (self.digit_width + self.padding) + 2 * self.colon_width + 2 * self.padding)) # Seconda cifra secondi
         
     ##TEST visualizzazione lettera
         # Sposta la lettera alla stessa posizione X della prima cifra dell'ora
        x_offset_lettera1 = self.padding
        y_offset_lettera1 = self.padding + self.digit_height + 50

        self.letters.append(self.create_digit_display(x_offset_lettera1, y_offset=y_offset_lettera1)) # Prima cifra lettera
        # Aggiungi un secondo display per la seconda lettera, posizionandolo dopo la prima
        x_offset_lettera2 = x_offset_lettera1 + self.digit_width + self.padding
        self.letters.append(self.create_digit_display(x_offset_lettera2, y_offset=y_offset_lettera1)) # Seconda lettera

                ##fine test lettera
        # Inizializza l'orologio
        self.update_clock()

    # Funzione per creare un display per una singola cifra (7 segmenti)
    def create_digit_display(self, x_offset,y_offset=None):
        digit_segments = []
        
        x_offset = x_offset +70
        base_y = y_offset if y_offset is not None else self.padding
        
        # Le coordinate sono relative all'inizio del canvas della singola cifra
        # Segmento A (top)
        digit_segments.append(self.canvas.create_rectangle(
            x_offset + self.segment_width, base_y,
            x_offset + self.digit_width - self.segment_width, base_y+ self.segment_width,
            fill=self.segment_color_off, outline=self.segment_color_off
        ))
        
        # Segmento B (top-right)
        digit_segments.append(self.canvas.create_rectangle(
            x_offset + self.digit_width - self.segment_width, base_y+ self.segment_width,
            x_offset + self.digit_width, base_y + self.digit_height / 2 - self.segment_width / 2,
            fill=self.segment_color_off, outline=self.segment_color_off
        ))

        # Segmento C (bottom-right)
        digit_segments.append(self.canvas.create_rectangle(
            x_offset + self.digit_width - self.segment_width, base_y+ self.digit_height / 2 + self.segment_width / 2,
            x_offset + self.digit_width, base_y + self.digit_height - self.segment_width,
            fill=self.segment_color_off, outline=self.segment_color_off
        ))
        
        # Segmento D (bottom)
        digit_segments.append(self.canvas.create_rectangle(
            x_offset + self.segment_width, base_y + self.digit_height - self.segment_width,
            x_offset + self.digit_width - self.segment_width, base_y + self.digit_height,
            fill=self.segment_color_off, outline=self.segment_color_off
        ))

        # Segmento E (bottom-left)
        digit_segments.append(self.canvas.create_rectangle(
            x_offset, base_y + self.digit_height / 2 + self.segment_width / 2,
            x_offset + self.segment_width, base_y + self.digit_height - self.segment_width,
            fill=self.segment_color_off, outline=self.segment_color_off
        ))

        # Segmento F (top-left)
        digit_segments.append(self.canvas.create_rectangle(
            x_offset, base_y + self.segment_width,
            x_offset + self.segment_width, base_y + self.digit_height / 2 - self.segment_width / 2,
            fill=self.segment_color_off, outline=self.segment_color_off
        ))

        # Segmento G (middle)
        digit_segments.append(self.canvas.create_rectangle(
            x_offset + self.segment_width, base_y + self.digit_height / 2 - self.segment_width / 2,
            x_offset + self.digit_width - self.segment_width, base_y + self.digit_height / 2 + self.segment_width / 2,
            fill=self.segment_color_off, outline=self.segment_color_off
        ))
        
        return digit_segments

    # Funzione per creare i punti dei due punti (colons)
    def create_colon_display(self, x_offset):
        x_offset = x_offset +70
        colon_dots = []
        dot_radius = self.segment_width / 2
        dot_padding_y = self.digit_height / 4

        # Punto superiore
        colon_dots.append(self.canvas.create_oval(
            x_offset, self.padding + dot_padding_y - dot_radius,
            x_offset + self.colon_width, self.padding + dot_padding_y + dot_radius,
            fill=self.segment_color_on, outline=self.segment_color_on
        ))

        # Punto inferiore
        colon_dots.append(self.canvas.create_oval(
            x_offset, self.padding + 3 * dot_padding_y - dot_radius,
            x_offset + self.colon_width, self.padding + 3 * dot_padding_y + dot_radius,
            fill=self.segment_color_on, outline=self.segment_color_on
        ))
        
        return colon_dots

    # Funzione per impostare i segmenti di una cifra in base al numero
    def set_digit(self, digit_segments, number_char):
        segment_states = self.segments_map.get(number_char, self.segments_map[' ']) # Ottiene lo stato dei segmenti per il carattere
        
        for i, state in enumerate(segment_states):
            color = self.segment_color_on if state else self.segment_color_off
            self.canvas.itemconfig(digit_segments[i], fill=color, outline=color)
            
    ###TEST Visualizzazione lettera

    def set_letters(self, digit_segments, letter_char):
            segment_states = self.segments_map_lettere.get(letter_char, self.segments_map_lettere[' ']) # Ottiene lo stato dei segmenti per il carattere
            
            for i, state in enumerate(segment_states):
                color = self.segment_color_on if state else self.segment_color_off
                self.canvas.itemconfig(digit_segments[i], fill=color, outline=color)    
        
        
    # Funzione per aggiornare l'orologio
    def update_clock(self):
      
        
        current_time = time.strftime("%H%M%S") # Formato HHMMSS
        current_data = time.strftime("%G%M%Y")
        current_hour = int(current_time[0:2]) # Estrai l'ora come intero
        current_minute = int(current_time[2:4]) # Estrai i minuti come intero
        current_second = int(current_time[4:6]) # Estrai i secondi come intero
        

        
        # Aggiorna le cifre delle ore
        self.set_digit(self.digits[0], current_time[0]) # Prima cifra ora
        self.set_digit(self.digits[1], current_time[1]) # Seconda cifra ora

        # Aggiorna le cifre dei minuti
        self.set_digit(self.digits[2], current_time[2]) # Prima cifra minuto
        self.set_digit(self.digits[3], current_time[3]) # Seconda cifra minuto

        # Aggiorna le cifre dei secondi
        self.set_digit(self.digits[4], current_time[4]) # Prima cifra secondo
        self.set_digit(self.digits[5], current_time[5]) # Seconda cifra secondo
        
        #####TEST VISUALIZZAZIONE DI UNA LETTERA
        
        self.set_letters(self.letters[0], 'A') # Prima cifra data
        
        self.set_letters(self.letters[1], 'B') # seconda cifra data
        #################FINE TEST


            # --- INIZIO MODIFICA PER IL LAMPEGGIO DEI DUE PUNTI ---
        # Il sesto carattere di current_time (current_time[5]) è il secondo corrente.
        # Controlliamo se il secondo è pari o dispari per farli lampeggiare.
        if int(current_time[5]) % 2 == 0:
            # Secondi pari: i due punti sono accesi
            colon_color = self.segment_color_on
        else:
            # Secondi dispari: i due punti sono spenti (colore del background o segment_color_off)
            colon_color = self.bg_color # O self.segment_color_off se preferisci un rosso scuro

        for dot in self.colons[1]: # Itera sui singoli punti all'interno di un gruppo
                self.canvas.itemconfig(dot, fill=colon_color, outline=colon_color)
        # --- FINE MODIFICA PER IL LAMPEGGIO DEI SECONDI DUE PUNTI ---
        
        # --- Gestione del lampeggio del PRIMO gruppo di due punti (tra ore e minuti) ---
        # Lampeggia solo allo scatto da un'ora alla successiva.
        # Il lampeggio avviene per un solo secondo (quando i minuti e i secondi sono 00)
        if current_minute == 0 and current_second == 0 and self.last_hour != current_hour:
            # Se è scattata una nuova ora (e solo per un secondo)
            self.last_hour = current_hour # Aggiorna l'ultima ora per evitare lampeggi continui
            hours_colon_color = self.segment_color_on # Accendi i punti
        elif current_minute == 0 and current_second == 1 and self.last_hour == current_hour:
            # Dopo un secondo, li spegni per dare l'effetto di un singolo lampo
            hours_colon_color = self.bg_color
        else:
            # In tutti gli altri momenti, i punti sono accesi
            hours_colon_color = self.segment_color_on
            # Assicurati che last_hour sia aggiornato se il minuto è > 0, per reset della condizione
            if current_minute > 0 or current_second > 1: # Resetta last_hour se non siamo all'inizio dell'ora
                self.last_hour = current_hour 

        # Applica il colore al primo gruppo di due punti (self.colons[0])
        for dot in self.colons[0]:
            self.canvas.itemconfig(dot, fill=hours_colon_color, outline=hours_colon_color)


        
        # Chiamata ricorsiva dopo 1 secondo
        self.root.after(1000, self.update_clock)

# Funzione principale per l'esecuzione
if __name__ == "__main__":
    root = tk.Tk()
    clock = DigitalClock(root)
    root.mainloop()