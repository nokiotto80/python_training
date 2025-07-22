#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 20:59:15 2025

@author: macbook_vincenzo
"""

import random
import string
from tkinter import Tk, Button, Label, Entry, Checkbutton,StringVar, Spinbox, simpledialog, Menu,messagebox
import threading

import pyperclip #installato da comando : pip install pyperclip
import os
import datetime


# Crea la finestra principale
window = Tk()
window.title("Generatore di Password")

#parte dove la finestra viene PERSONALIZZATA; menu di scelta di cambio colore
# Creazione del menu a barre
menu_bar = Menu(window)
window.config(menu=menu_bar)

# Menu "Colori"
menu_colori = Menu(menu_bar, tearoff=0)
menu_colori.add_command(label="Rosso", command=lambda: cambia_colore("red"))
menu_colori.add_command(label="Giallo", command=lambda: cambia_colore("yellow"))
menu_colori.add_command(label="Verde", command=lambda: cambia_colore("green"))
menu_colori.add_command(label="Blu", command=lambda: cambia_colore("blue"))

menu_bar.add_cascade(label="Colori", menu=menu_colori)



def genera_password(lunghezza, caratteri_speciali=True, numeri=True):
    """
    Genera una password casuale.

    Args:
        lunghezza (int): Lunghezza desiderata della password.
        caratteri_speciali (bool, optional): Include caratteri speciali. Defaults to True.
        numeri (bool, optional): Include numeri. Defaults to True.

    Returns:
        str: La password generata.
    """

    caratteri = string.ascii_letters
    if caratteri_speciali:
        caratteri += string.punctuation
    if numeri:
        caratteri += string.digits

    password = ''.join(random.choice(caratteri) for _ in range(lunghezza))
    return password



def genera_password_con_interfaccia():
    lunghezza =  int(spinbox.get())
    caratteri_speciali = var_speciali.get() == "1"
    numeri = var_numeri.get() == "1"
    password = genera_password(lunghezza, caratteri_speciali, numeri)
    label_password.config(text="La password generata è:\n"+password)
    
#funzione per salvare le password in un FILE di testo
def salva_password():
    lunghezza =  int(spinbox.get())

    # Chiedi il nome del servizio in una finestra modale
    nome_servizio = simpledialog.askstring(title="Nome del servizio", prompt="Inserisci il nome del servizio:")
    if nome_servizio:
       print("Password salvata nel file f{password_salvate} con il nome f{nome_servizio}")
    else:
        print("Nome servizio non inserito")
    data_creazione = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    password = label_password.cget("text")
    with open("password_salvate.txt", "a") as file:
        file.write(f"{nome_servizio},{password},{lunghezza},{data_creazione}\n")
        

# lunghezzza della password: da spinbox
spinbox = Spinbox(window, from_=8, to=20)
spinbox.pack()

# Variabili per le checkbox
var_speciali = StringVar(value="1")
var_numeri = StringVar(value="1")

# Checkbox per i caratteri speciali
check_speciali = Checkbutton(window, text="Includi caratteri speciali", variable=var_speciali)
check_speciali.pack()

# Checkbox per i numeri
check_numeri = Checkbutton(window, text="Includi numeri", variable=var_numeri)
check_numeri.pack()

# Etichetta per visualizzare la password generata
label_password = Label(window)
label_password.pack()

# Bottone 1 per generare la password
button = Button(window, text="Genera Password", command=genera_password_con_interfaccia)
button.pack(pady=10)

# Bottone 2 per copiare la password
button_copia = Button(window, text="Copia", command=lambda: pyperclip.copy(label_password.cget("text")))
button_copia.pack(pady=20)



# Funzione per cambiare il colore
def cambia_colore(colore):
    window.config(bg=colore)

#apri il file con le password salvate

def apri_file_password():
    try:
        path = os.path.join(os.path.dirname(__file__), "password_salvate.txt")
        # Per macOS, usa il comando 'open'
        os.system("open " + path)
    except FileNotFoundError:
        messagebox.showerror("Errore", "Il file delle password non è stato trovato.")
    except OSError as e:
        messagebox.showerror("Errore", f"Si è verificato un errore durante l'apertura del file: {str(e)}")

# Bottone 3 per SALVARE a parre la password in un file
button_salva_file = Button(window, text="Salva in File", command=salva_password)
button_salva_file.pack(pady=30)

# Bottone 4 per aprire il file delle password
button_apri_file = Button(window, text="Apri File Password", command=apri_file_password)
button_apri_file.pack(pady=40)

window.mainloop()