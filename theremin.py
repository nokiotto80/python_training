import tkinter as tk
import math
import numpy as np # Necessario per la manipolazione efficiente degli array audio
import sounddevice as sd # Libreria per la generazione del suono
import time # Per la gestione del tempo

class Theremin:
    def __init__(self, root):
        """
        Inizializza l'applicazione Theremin.
        Configura la finestra principale, il canvas, lo switch per la modalità discreta
        e le variabili per la generazione del suono.
        """
        self.root = root
        self.root.title("Theremin Digitale")
        self.root.geometry("600x650") # Imposta una dimensione iniziale per la finestra
        self.root.resizable(False, False) # Rende la finestra non ridimensionabile per mantenere layout

        # Configurazione del canvas per l'interazione
        self.canvas = tk.Canvas(root, width=500, height=500, bg="black", bd=2, relief="sunken")
        self.canvas.pack(pady=10, padx=10) # Aggiunge padding e un bordo al canvas

        # Frame per contenere lo switch e la label per la frequenza/ampiezza
        self.control_frame = tk.Frame(root, bg="#333333")
        self.control_frame.pack(pady=5)

        # Switch per alternare tra modalità analogica e discreta
        self.switch_var = tk.BooleanVar()
        self.switch = tk.Checkbutton(
            self.control_frame, # Posizionato nel nuovo frame
            text="Modalità Discreta",
            variable=self.switch_var,
            command=self.toggle_mode,
            font=("Inter", 12, "bold"), # Font più leggibile
            fg="white", # Colore del testo
            bg="#444444", # Colore di sfondo del pulsante
            selectcolor="#666666", # Colore quando selezionato
            indicatoron=False, # Nasconde il quadratino di default, per uno stile più moderno
            relief="raised", # Effetto 3D
            padx=15, # Padding interno
            pady=8, # Padding interno
            activebackground="#555555", # Colore quando il mouse è sopra
            activeforeground="white"
        )
        self.switch.pack(side=tk.LEFT, padx=10) # Posiziona a sinistra nel frame

        # Label per mostrare frequenza e ampiezza
        self.info_label = tk.Label(
            self.control_frame, # Posizionato nel nuovo frame
            text="Frequenza: --- Hz | Ampiezza: ---",
            font=("Inter", 12),
            fg="white",
            bg="#333333"
        )
        self.info_label.pack(side=tk.LEFT, padx=10) # Posiziona a destra nel frame

        self.is_discrete = False # Stato iniziale: modalità analogica
        self.points = [] # Lista per memorizzare le coordinate dei punti della costellazione

        # Variabili per la mappatura del suono
        self.min_frequency = 220  # Frequenza minima (La3)
        self.max_frequency = 880  # Frequenza massima (La4)
        self.min_amplitude = 0.0  # Ampiezza minima (silenzio)
        self.max_amplitude = 1.0  # Ampiezza massima (volume massimo)

        self.current_frequency = self.min_frequency # Frequenza iniziale
        self.current_amplitude = self.max_amplitude / 2 # Ampiezza iniziale a metà

        # Variabili per la gestione dello stream audio continuo
        self.sample_rate = 44100 # Frequenza di campionamento standard (Hz)
        self.phase = 0.0 # Fase corrente dell'onda sinusoidale per continuità
        self.stream = None # Oggetto stream di sounddevice
        self.is_playing = False # Flag per indicare se il suono è in riproduzione

        # Binding degli eventi del mouse al canvas
        # <Button-1> si attiva quando il tasto sinistro del mouse viene premuto (una volta)
        self.canvas.bind("<Button-1>", self.start_sound)
        # <B1-Motion> si attiva quando il tasto sinistro del mouse è premuto e il mouse si muove
        self.canvas.bind("<B1-Motion>", self.update_sound_parameters)
        # <ButtonRelease-1> si attiva quando il tasto sinistro del mouse viene rilasciato
        self.canvas.bind("<ButtonRelease-1>", self.stop_sound)

        # Configurazione dello stile della finestra principale
        self.root.configure(bg="#333333") # Sfondo scuro per la finestra

        # Genera i punti della costellazione dopo che il canvas ha le sue dimensioni finali
        self.root.update_idletasks() # Forza Tkinter a calcolare le dimensioni del canvas
        self.generate_points() # Ora genera i punti con le dimensioni corrette del canvas

    def generate_points(self):
        """
        Genera i punti per la modalità discreta, disponendoli in una griglia uniforme
        sull'intera superficie del canvas, simile a un tabellone di Forza 4.
        """
        self.points = [] # Resetta la lista dei punti
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        point_spacing_x = 50
        point_spacing_y = 50

        num_cols = math.floor(canvas_width / point_spacing_x)
        num_rows = math.floor(canvas_height / point_spacing_y)

        margin_x = (canvas_width - (num_cols * point_spacing_x)) / 2 + point_spacing_x / 2
        margin_y = (canvas_height - (num_rows * point_spacing_y)) / 2 + point_spacing_y / 2

        for row in range(num_rows):
            for col in range(num_cols):
                x = margin_x + col * point_spacing_x
                y = margin_y + row * point_spacing_y
                self.points.append((x, y))

    def toggle_mode(self):
        """
        Alterna la modalità del Theremin tra analogica e discreta.
        Pulisce il canvas e ridisegna i punti se si passa alla modalità discreta.
        """
        self.is_discrete = self.switch_var.get()
        self.stop_sound(None) # Ferma il suono quando si cambia modalità
        self.canvas.delete("all") # Pulisce tutti gli elementi disegnati sul canvas
        self.generate_points() # Rigenera i punti ogni volta che si cambia modalità
        if self.is_discrete:
            self.draw_points() # Disegna la costellazione di punti se la modalità è discreta
        self.update_info_label() # Aggiorna la label quando la modalità cambia

    def draw_points(self):
        """
        Disegna tutti i punti della costellazione sul canvas.
        """
        for x, y in self.points:
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="white", outline="white", width=1)

    def _audio_callback(self, outdata, frames, time_info, status):
        """
        Funzione di callback chiamata da sounddevice per riempire il buffer audio.
        Genera campioni di onda sinusoidale in base a frequenza e ampiezza correnti.
        """
        if status:
            print(f"Audio callback status: {status}") # Stampa eventuali avvisi o errori dallo stream audio

        # Assicura che la frequenza non sia zero o negativa
        freq = max(1.0, self.current_frequency)
        amp = max(0.0, min(1.0, self.current_amplitude))

        # Genera i campioni dell'onda sinusoidale per il blocco corrente
        t = (self.phase + np.arange(frames)) / self.sample_rate
        samples = amp * np.sin(2 * np.pi * freq * t)

        # Scrive i campioni nell'output buffer
        outdata[:] = samples.reshape(-1, 1) # Reshape per canale mono

        # Aggiorna la fase per la continuità del suono
        self.phase = (self.phase + frames) % self.sample_rate

    def start_sound(self, event):
        """
        Avvia lo stream audio quando il tasto del mouse viene premuto.
        """
        if not self.is_playing:
            try:
                # Crea e avvia un nuovo stream audio non bloccante con la callback
                self.stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=1, # Canale mono
                    dtype=np.float32, # Formato dati
                    callback=self._audio_callback # La nostra funzione di generazione audio
                )
                self.stream.start()
                self.is_playing = True
                # Aggiorna i parametri audio immediatamente all'avvio del suono
                self.update_sound_parameters(event)
                # Rimosse le stampe da console, ora usiamo la label
            except Exception as e:
                print(f"Errore all'avvio dello stream audio: {e}")
                self.is_playing = False
                if self.stream:
                    self.stream.close()
                self.stream = None

    def update_sound_parameters(self, event):
        """
        Aggiorna la frequenza e l'ampiezza del suono in base alla posizione del mouse.
        Questa funzione aggiorna solo le variabili, la callback si occupa della generazione.
        """
        if not self.is_playing: # Non aggiornare se il suono non è attivo
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        target_x = event.x
        target_y = event.y

        if self.is_discrete:
            # In modalità discreta, trova il punto della costellazione più vicino al cursore
            if not self.points:
                self.generate_points()
                if not self.points: return

            distances = [math.sqrt((target_x - x)**2 + (target_y - y)**2) for x, y in self.points]
            closest_point_index = distances.index(min(distances))
            closest_point = self.points[closest_point_index]

            normalized_x = closest_point[0] / canvas_width
            normalized_y = closest_point[1] / canvas_height

            # Evidenzia il punto selezionato
            self.canvas.delete("highlight") # Rimuove il vecchio highlight
            self.canvas.create_oval(
                closest_point[0] - 6, closest_point[1] - 6,
                closest_point[0] + 6, closest_point[1] + 6,
                fill="red", outline="red", width=2, tags="highlight"
            )

        else:
            # In modalità analogica, usa direttamente le coordinate del mouse
            normalized_x = target_x / canvas_width
            normalized_y = target_y / canvas_height
            self.canvas.delete("highlight") # Rimuove l'highlight se si torna in analogico


        # Limita i valori normalizzati tra 0 e 1
        normalized_x = max(0.0, min(1.0, normalized_x))
        normalized_y = max(0.0, min(1.0, normalized_y))

        # Aggiorna le variabili di frequenza e ampiezza
        self.current_frequency = self.min_frequency + (self.max_frequency - self.min_frequency) * normalized_x
        self.current_amplitude = self.max_amplitude - (self.max_amplitude - self.min_amplitude) * normalized_y

        self.update_info_label() # <--- AGGIUNTA: Aggiorna la label con i nuovi valori

    def update_info_label(self):
        """
        Aggiorna il testo della label con la frequenza e l'ampiezza attuali.
        """
        self.info_label.config(
            text=f"Frequenza: {self.current_frequency:.2f} Hz | Ampiezza: {self.current_amplitude:.2f}"
        )

    def stop_sound(self, event=None): # event=None per permettere chiamate senza evento del mouse
        """
        Ferma la riproduzione audio quando il tasto del mouse viene rilasciato o la modalità cambiata.
        """
        print("stop_sound chiamata.") # DEBUG: Stampa quando la funzione viene chiamata
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()
            print("Stream fermato e chiuso.") # DEBUG: Stampa quando lo stream viene effettivamente fermato
        else:
            print("Nessuno stream attivo da fermare.") # DEBUG: Stampa se non c'è stream attivo
        self.stream = None # Resetta lo stream
        self.is_playing = False # Resetta il flag di riproduzione
        self.canvas.delete("highlight") # Rimuove l'highlight al rilascio del mouse
        self.info_label.config(text="Frequenza: --- Hz | Ampiezza: ---") # Resetta la label


if __name__ == "__main__":
    # Inizializza la finestra Tkinter e l'applicazione Theremin
    root = tk.Tk()
    app = Theremin(root)
    root.mainloop()

    # Assicurati di chiudere lo stream audio quando l'applicazione si chiude
    if app.stream:
        app.stream.close()
