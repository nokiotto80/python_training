import tkinter as tk
from tkinter import *
from tkinter import filedialog, font



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
    if T.tag_ranges("sel"):  # Verifica se è presente una selezione
        current_tags = T.tag_names("sel.first", "sel.last")
        if "bold" in current_tags:
            T.tag_remove("bold", "sel.first", "sel.last")
        else:
            T.tag_add("bold", "sel.first", "sel.last")

def apply_italic():
    current_tags = T.tag_names("sel.first", "sel.last")  # Corretto: solo due argomenti
    if "italic" in current_tags:
        T.tag_remove("italic", "sel.first", "sel.last")
    else:
        T.tag_add("italic", "sel.first", "sel.last")

def apply_underline():
    current_tags = T.tag_names("sel.first", "sel.last")  # Corretto: solo due argomenti
    if "underline" in current_tags:
        T.tag_remove("underline", "sel.first", "sel.last")
    else:
        T.tag_add("underline", "sel.first", "sel.last")


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

T.pack()

T.tag_configure("bold", font=font.Font(weight="bold"))
T.tag_configure("italic", font=font.Font(slant="italic"))
T.tag_configure("underline", underline=1)


tk.mainloop()