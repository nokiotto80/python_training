#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk

# Creazione della finestra principale
root = tk.Tk()
root.title("Tavola Pitagorica con Zoom")

# Dimensioni originali e ingrandite
original_width = 5
original_height = 2
zoomed_width = 15
zoomed_height = 5

# Funzione per creare un'etichetta con un colore alternato e gestire l'evento click
def create_label(row, col, value):
    colore = "blue" if (row + col) % 2 == 0 else "orange"  # Alternanza di colori bianco e nero
    label = tk.Label(root, text=value, bg=colore, width=original_width, height=original_height, borderwidth=1, relief="solid")
    label.grid(row=row, column=col)

    # Funzione interna per gestire l'evento click
    def zoom(event):
       # nonlocal original_width, original_height, zoomed_width, zoomed_height
        if label.cget("width") == original_width:
            label.config(width=zoomed_width, height=zoomed_height, borderwidth=3)
        else:
            label.config(width=original_width, height=original_height, borderwidth=1)

    label.bind("<Button-1>", zoom)

# Creazione della tavola pitagorica
for i in range(1, 11):
    for j in range(1, 11):
        value = i * j
        create_label(i, j, value)

root.mainloop()