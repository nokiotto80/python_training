"""
Generatore di password casuali, scelta della lunghezza. 
Opzionali: caratteri speciali e numeri.
possibilità inserire in un file di testo
controllo captcha
"""
import tkinter as tk
from tkinter import Button, Label, Entry, Checkbutton, StringVar, Spinbox, simpledialog, Menu, messagebox
import random
import string
import datetime
import pyperclip # installato con: pip install pyperclip
import os
import threading # Mantenuto per future espansioni o operazioni lunghe

# Moduli per il CAPTCHA
from captcha.image import ImageCaptcha
from PIL import Image, ImageTk # Necessita: pip install Pillow

# Variabili globali per il CAPTCHA
current_captcha_text = ""
captcha_photo = None # Per mantenere un riferimento all'immagine Tkinter

# Crea la finestra principale
window = tk.Tk()
window.title("Generatore di Password")
window.geometry("400x650") # Aumenta l'altezza per il CAPTCHA

# Parte dove la finestra viene PERSONALIZZATA; menu di scelta di cambio colore
# Creazione del menu a barre
menu_bar = Menu(window)
window.config(menu=menu_bar)

# Menu "Colori"
menu_colori = Menu(menu_bar, tearoff=0)
menu_colori.add_command(label="Rosso", command=lambda: cambia_colore("red"))
menu_colori.add_command(label="Giallo", command=lambda: cambia_colore("yellow"))
menu_colori.add_command(label="Verde", command=lambda: cambia_colore("green"))
menu_colori.add_command(label="Blu", command=lambda: cambia_colore("blue"))
menu_colori.add_command(label="Malva", command=lambda: cambia_colore("#E0BBE4")) # Un colore malva più specifico
menu_colori.add_command(label="Grigio (Default)", command=lambda: cambia_colore(window.cget('bg'))) # Per tornare al colore di default

menu_bar.add_cascade(label="Colori", menu=menu_colori)

# Funzione per cambiare il colore di sfondo della finestra
def cambia_colore(colore):
    window.config(bg=colore)

# Funzione per generare la password
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

    # Assicura che la password contenga almeno un carattere di ogni tipo selezionato, se possibile
    password_list = []
    if caratteri_speciali and string.punctuation:
        password_list.append(random.choice(string.punctuation))
    if numeri and string.digits:
        password_list.append(random.choice(string.digits))
    if string.ascii_letters:
        password_list.append(random.choice(string.ascii_letters)) # Assicura sempre almeno una lettera

    # Riempi il resto della password
    # Assicurati che lunghezza sia sufficiente per i caratteri già aggiunti
    remaining_length = lunghezza - len(password_list)
    if remaining_length < 0: # Se la lunghezza è troppo piccola per i requisiti minimi
        remaining_length = 0

    for _ in range(remaining_length):
        if caratteri: # Assicura che ci siano caratteri da cui scegliere
            password_list.append(random.choice(caratteri))
        else: # Se non ci sono caratteri selezionati, non possiamo generare
            messagebox.showwarning("Attenzione", "Nessun tipo di carattere selezionato per la password!")
            return "" # Ritorna una stringa vuota o gestisci l'errore diversamente

    random.shuffle(password_list) # Mescola i caratteri per una maggiore casualità
    return ''.join(password_list)

# Funzione per generare la password e aggiornare l'etichetta
def genera_password_con_interfaccia():
    try:
        lunghezza = int(spinbox.get())
        if lunghezza < 8 or lunghezza > 20:
            messagebox.showwarning("Attenzione", "La lunghezza della password deve essere tra 8 e 20.")
            return
    except ValueError:
        messagebox.showerror("Errore", "Inserisci una lunghezza valida per la password.")
        return

    caratteri_speciali = var_speciali.get() == "1"
    numeri = var_numeri.get() == "1"

    # Genera la password
    password = genera_password(lunghezza, caratteri_speciali, numeri)
    if password: # Solo se la password è stata generata con successo
        label_password.config(text="La password generata è:\n" + password)

# Funzione per generare e visualizzare un nuovo CAPTCHA
def generate_new_captcha():
    global current_captcha_text, captcha_photo
    
    # Genera una stringa casuale per il CAPTCHA (es. 6 caratteri alfanumerici)
    captcha_chars = string.ascii_uppercase + string.digits
    current_captcha_text = ''.join(random.choice(captcha_chars) for _ in range(6))

    image_captcha = ImageCaptcha(width=250, height=50)
    image_data = image_captcha.generate(current_captcha_text)
    
    # Salva l'immagine temporaneamente e caricala con Pillow
    # Usiamo un BytesIO per evitare di scrivere su disco, se possibile, ma per semplicità ora salviamo
    temp_captcha_file = "temp_captcha.png"
    image_captcha.write(current_captcha_text, temp_captcha_file)
    
    img = Image.open(temp_captcha_file)
    captcha_photo = ImageTk.PhotoImage(img)
    
    captcha_label.config(image=captcha_photo)
    captcha_label.image = captcha_photo # Mantiene un riferimento per evitare che l'immagine venga "garbage collected"
    
    captcha_entry.delete(0, tk.END) # Pulisce il campo di input del CAPTCHA
    
    # Rimuovi il file temporaneo dopo averlo caricato
    if os.path.exists(temp_captcha_file):
        os.remove(temp_captcha_file)

# Funzione per salvare le password in un file di testo
def salva_password():
    # 1. Verifica CAPTCHA
    user_captcha_input = captcha_entry.get()
    if user_captcha_input.lower() != current_captcha_text.lower():
        messagebox.showerror("Errore CAPTCHA", "Codice CAPTCHA errato. Riprova.")
        generate_new_captcha() # Genera un nuovo CAPTCHA dopo l'errore
        return

    # 2. Verifica se una password è stata generata
    displayed_text = label_password.cget("text")
    if not displayed_text.startswith("La password generata è:\n"):
        messagebox.showwarning("Attenzione", "Genera prima una password da salvare!")
        return

    # Estrai la password effettiva dal testo dell'etichetta
    password_da_salvare = displayed_text.replace("La password generata è:\n", "")

    # Ottieni la lunghezza dalla spinbox
    try:
        lunghezza = int(spinbox.get())
    except ValueError:
        messagebox.showerror("Errore", "Lunghezza password non valida per il salvataggio.")
        return

    # 3. Chiedi il nome del servizio in una finestra modale (InputBox)
    nome_servizio = simpledialog.askstring(title="Nome del servizio", prompt="Inserisci il nome del servizio (opzionale):", parent=window)

    # Se l'utente ha cliccato "OK" (anche se il campo è vuoto)
    if nome_servizio is not None:
        data_creazione = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open("password_salvate.txt", "a") as file:
                file.write(f"{nome_servizio},{password_da_salvare},{lunghezza},{data_creazione}\n")
            messagebox.showinfo("Successo", f"Password salvata per '{nome_servizio}' nel file 'password_salvate.txt'.")
            generate_new_captcha() # Genera un nuovo CAPTCHA dopo il salvataggio
        except IOError as e:
            messagebox.showerror("Errore di salvataggio", f"Impossibile salvare la password: {e}")
    else:
        # L'utente ha cliccato "Annulla" sulla finestra di dialogo
        messagebox.showinfo("Annullato", "Salvataggio password annullato.")
        generate_new_captcha() # Genera un nuovo CAPTCHA anche se annullato


# Funzione per copiare la password negli appunti
def copia_password():
    displayed_text = label_password.cget("text")
    if not displayed_text.startswith("La password generata è:\n"):
        messagebox.showwarning("Attenzione", "Genera prima una password da copiare!")
        return
    password_to_copy = displayed_text.replace("La password generata è:\n", "")
    pyperclip.copy(password_to_copy)
    messagebox.showinfo("Copiato", "Password copiata negli appunti!")

# Funzione per aprire il file con le password salvate
def apri_file_password():
    try:
        path = os.path.join(os.path.dirname(__file__), "password_salvate.txt")
        if not os.path.exists(path):
            messagebox.showwarning("Attenzione", "Il file 'password_salvate.txt' non esiste ancora. Genera e salva una password per crearlo.")
            return

        if os.name == 'posix': # macOS e Linux
            os.system(f"open \"{path}\"") # Usa virgolette per percorsi con spazi
        elif os.name == 'nt': # Windows
            os.startfile(path)
        else:
            messagebox.showwarning("Sistema non supportato", "L'apertura automatica del file non è supportata per il tuo sistema operativo.")

    except OSError as e:
        messagebox.showerror("Errore di apertura", f"Si è verificato un errore durante l'apertura del file: {str(e)}")


# --- Layout dei widget ---

# Lunghezza della password: da spinbox
label_lunghezza = Label(window, text="Lunghezza della password (8-20):")
label_lunghezza.pack(pady=(10, 0))
spinbox = Spinbox(window, from_=8, to=20, width=5)

spinbox.pack()

# Variabili per le checkbox
var_speciali = StringVar(value="1") # Default su "1" (selezionato)
var_numeri = StringVar(value="1")   # Default su "1" (selezionato)

# Checkbox per i caratteri speciali
check_speciali = Checkbutton(window, text="Includi caratteri speciali", variable=var_speciali)
check_speciali.pack(pady=5)

# Checkbox per i numeri
check_numeri = Checkbutton(window, text="Includi numeri", variable=var_numeri)
check_numeri.pack(pady=5)

# Etichetta per visualizzare la password generata
label_password = Label(window, text="Premi 'Genera Password'", wraplength=300, justify="center", font=("Arial", 12, "bold"))
label_password.pack(pady=15)

# Bottone 1 per generare la password
button_genera = Button(window, text="Genera Password", command=genera_password_con_interfaccia, width=20, height=2)
button_genera.pack(pady=5)

# Bottone 2 per copiare la password
button_copia = Button(window, text="Copia Password", command=copia_password, width=20, height=2)
button_copia.pack(pady=5)

# --- Sezione CAPTCHA ---
captcha_frame = tk.Frame(window)
captcha_frame.pack(pady=10)

captcha_instruction_label = Label(captcha_frame, text="Inserisci il codice CAPTCHA:")
captcha_instruction_label.pack(side=tk.TOP, pady=(0,5))

captcha_image_frame = tk.Frame(captcha_frame) # Frame per allineare immagine e input
captcha_image_frame.pack()

captcha_label = Label(captcha_image_frame) # Etichetta per l'immagine del CAPTCHA
captcha_label.pack(side=tk.LEFT, padx=5)

captcha_entry = Entry(captcha_image_frame, width=10, font=("Arial", 14)) # Campo di input per il CAPTCHA
captcha_entry.pack(side=tk.LEFT, padx=5)

# Bottone per rigenerare il CAPTCHA (opzionale, ma utile)
button_refresh_captcha = Button(captcha_frame, text="Rigenera CAPTCHA", command=generate_new_captcha)
button_refresh_captcha.pack(pady=5)


# Bottone 3 per SALVARE la password in un file
button_salva_file = Button(window, text="Salva in File", command=salva_password, width=20, height=2)
button_salva_file.pack(pady=5)

# Bottone 4 per aprire il file delle password
button_apri_file = Button(window, text="Apri File Password", command=apri_file_password, width=20, height=2)
button_apri_file.pack(pady=5)

# Genera il primo CAPTCHA all'avvio dell'applicazione
generate_new_captcha()

# Avvia il loop principale di Tkinter
window.mainloop()
