#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 22 18:08:13 2025

@author: macbook_vincenzo
"""

# Python3 program to get selected
# value(s) from tkinter listbox

# Import tkinter
from tkinter import *

# Create the root window
root = Tk()
root.geometry('180x200')
root.title("ListBox esempio")

# Create a listbox
listbox = Listbox(root, width=40, height=10, selectmode=MULTIPLE)

# Inserting the listbox items
listbox.insert(1, "TPSIT")
listbox.insert(2, "Algoritmi")
listbox.insert(3, "Sistemi e Reti")
listbox.insert(4, "Machine Learning")
listbox.insert(5, "Blockchain")
listbox.insert(6, "Intelligenza Artificiale")


# Funzione che stampa elemento selezionato/i
def selezionato():
	
	# Traverse the tuple returned by
	# curselection method and print
	# corresponding value(s) in the listbox
	for i in listbox.curselection():
		print(listbox.get(i))
        

def cancella():# Cancella elemento/i selezionati
  
    end_index = listbox.index("end")
    if end_index == 0:
        print("la listbox è vuota, che vuoi cancellare ancora?")
	
    
    selected_checkboxs = listbox.curselection() 
  
    for selected_checkbox in selected_checkboxs[::-1]: 
        listbox.delete(selected_checkbox) 
        
        
def visualizza():
	for i in listbox.curselection():
		listbox.update()
        
        
def inserisci():
    
     listbox.insert("end", "ELEMENTO")

     

# Create a button widget and
# map the command parametermeter to

# selected_item function
btn = Button(root, text='Print Selected', command=selezionato)

# Placing the button and listbox
btn2 = Button(root, text='Delete Selected', command=cancella)

# Placing the button and listbox
btn3 = Button(root, text='ADD element', command=inserisci)

# Placing the button and listbox
btn.pack(side='bottom')
btn2.pack(side='bottom',pady=30)
btn3.pack(side='bottom',pady=30)


listbox.pack()

root.mainloop()
