"""
Author: Macbook_Vincenzo
Date. more or less 05/2025
Editor di testo, Si è partiti dalle funzioni per i grassetto, corsivo, sottolineato. salvataggio su file.
Disponibili menu dal file
Aggiunta funzione di sintesi vocale

"""
import tkinter as tk
from tkinter import *
from tkinter import filedialog, font
from gtts import gTTS
from playsound import playsound
import os



root = Tk()

# specify size of window.
root.geometry("250x250")
root.title("Editor di testo")

# Creazione del menu
menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff =0)
menu_bar.add_cascade(label="File", menu=file_menu)

# Toolbar creation
toolbar = tk.Frame(root)
toolbar.pack(side=tk.TOP, fill=tk.X)

def apply_bold():
    try:
        # Ottieni l'inizio e la fine della selezione
        start = T.index("sel.first")
        end = T.index("sel.last")

        if T.tag_ranges("bold"):
            # Rimuovi il grassetto se è già presente nella selezione
            T.tag_remove("bold", start, end)
        else:
            # Applica il grassetto
            T.tag_add("bold", start, end)
    except tk.TclError:
        # Gestisce il caso in cui non c'è una selezione
        pass

def apply_italic():
    try:
        # Ottieni l'inizio e la fine della selezione
        start = T.index("sel.first")
        end = T.index("sel.last")

        if T.tag_ranges("italic"):
            # Rimuovi il grassetto se è già presente nella selezione
            T.tag_remove("italic", start, end)
        else:
            # Applica il grassetto
            T.tag_add("italic", start, end)
    except tk.TclError:
        # Gestisce il caso in cui non c'è una selezione
        pass

def apply_underline():
    try:
        # Ottieni l'inizio e la fine della selezione
        start = T.index("sel.first")
        end = T.index("sel.last")

        if T.tag_ranges("underline"):
            # Rimuovi il grassetto se è già presente nella selezione
            T.tag_remove("underline", start, end)
        else:
            # Applica il grassetto
            T.tag_add("underline", start, end)
    except tk.TclError:
        # Gestisce il caso in cui non c'è una selezione
        pass


# Funzioni per il menu
def open_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        with open(file_path, 'r') as f:
            T.delete('1.0', tk.END)  # Cancella il testo esistente
            T.insert('1.0', f.read())

def save_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt")
    if file_path:
        with open(file_path, 'w') as f:
            try:
                f.write(T.get('1.0', tk.END))
            except:
             print("Errore nello scrivere il file")
            
def close_file():
    T.delete('1.0', tk.END)

# Aggiunta delle voci al menu
file_menu.add_command(label="Apri", command=open_file)
file_menu.add_command(label="Salva", command=save_file)
file_menu.add_command(label="Chiudi", command=close_file)

root.config(menu=menu_bar)

# Create text widget and specify size.
T = Text(root, height = 5, width = 52)

# Statusbar
status_var = tk.StringVar()
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

# Funzione per aggiornare la statusbar
def update_status():
    text = T.get("1.0", tk.END)
    char_count = len(text)
    vowel_count = sum(text.count(vowel) for vowel in "aeiouAEIOU")
    consonant_count = char_count - vowel_count  # Assumiamo che tutti gli altri siano consonanti
    status_var.set(f"Caratteri: {char_count}, Vocali: {vowel_count}, Consonanti: {consonant_count}")

# Aggiorna la statusbar inizialmente e quando il testo cambia
update_status()
T.bind("<KeyRelease>", lambda event: update_status())

# Pulsanti
bold_button = tk.Button(toolbar, text="G", command=apply_bold)
bold_button.pack(side=tk.LEFT)

italic_button = tk.Button(toolbar, text="C", command=apply_italic)
italic_button.pack(side=tk.LEFT)

underline_button = tk.Button(toolbar, text="S", command=apply_underline)
underline_button.pack(side=tk.LEFT)

def text_to_speech():
    """Converte il testo del widget in parlato e lo riproduce."""
    text_to_read = T.get("1.0", tk.END)
    if text_to_read.strip(): # Controlla che il testo non sia vuoto
        try:
            tts = gTTS(text=text_to_read, lang='it') # 'it' per la lingua italiana
            tts_filename = "speech.mp3"
            tts.save(tts_filename)
            playsound(tts_filename)
            os.remove(tts_filename) # Elimina il file audio temporaneo dopo la riproduzione
        except Exception as e:
            # Gestisce eventuali errori, ad esempio la mancanza di connessione a internet
            print(f"Errore durante la sintesi vocale: {e}")
            # Potresti anche mostrare un messaggio di errore all'utente con tk.messagebox
    else:
        print("Il campo di testo è vuoto.")

# Aggiungi un pulsante alla tua toolbar
speak_button = tk.Button(toolbar, text="🗣️ Leggi", command=text_to_speech)
speak_button.pack(side=tk.LEFT, padx=5)


T.pack()

T.tag_configure("bold", font=font.Font(weight="bold"))
T.tag_configure("italic", font=font.Font(slant="italic"))
T.tag_configure("underline", underline=1)


tk.mainloop()