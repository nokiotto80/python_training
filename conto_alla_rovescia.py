#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 10:46:45 2024

@author: macbook_vincenzo
"""

import time
from tkinter import Tk, Button

from playsound import playsound

def conto_alla_rovescia(minuti, tap,suono):
    """
    Funzione per eseguire un conto alla rovescia.

    Args:
        minuti (int): Numero di minuti per il conto alla rovescia.
        suono (str): Percorso del file audio.
    """

    secondi = minuti * 60
    while secondi:
        mins, secs = divmod(secondi, 60)
        timer = f"\r{mins:02d}:{secs:02d}"  # Utilizzo f-string per formattare e \r per il ritorno a capo senza andare a capo
        print(timer, end="")
        playsound(tap) # sulla falsariga di "suono" ho inserito un TICCHETTIO al secondo
        time.sleep(0.80)
        secondi -= 1
    print("\nTempo scaduto!")
    playsound(suono)

if __name__ == "__main__":
    try:
        minuti = int(input("Inserisci il numero di minuti per il conto alla rovescia: "))
        suono = "/Users/macbook_vincenzo/Python/Gong.wav"  # Sostituisci con il percorso del tuo file
        
        tap = "/Users/macbook_vincenzo/Python/tap.wav"  # Sostituisci con il percorso del tuo file
        conto_alla_rovescia(minuti,tap, suono)
    except ValueError:
        print("Devi inserire un numero intero.")
        