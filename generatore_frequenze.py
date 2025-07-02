import tkinter as tk
import numpy as np
import sounddevice as sd

class FrequencyGeneratorApp:
    def __init__(self, master):
        self.master = master
        master.title("Generatore di Frequenza")
        master.geometry("400x500") # Aumenta la dimensione della finestra per il menu e il canvas

        self.frequency = tk.DoubleVar(value=0.0) # Variabile Tkinter per la frequenza attuale
        self.amplitude = 0.5 # Ampiezza fissa del segnale (0.0 a 1.0)
        self.samplerate = 44100 # Frequenza di campionamento audio standard (campioni al secondo)
        self.current_phase = 0.0 # Mantiene la fase corrente in radianti per una forma d'onda continua

        # Variabile Tkinter per la selezione della forma d'onda
        self.waveform_type = tk.StringVar(value="Sinusoidale")
        self.waveform_type.trace_add("write", self.update_waveform_type) # Chiamato quando la forma d'onda cambia

        # Etichetta per visualizzare la frequenza attuale
        self.freq_label = tk.Label(master, text=f"Frequenza: {self.frequency.get():.1f} Hz", font=("Inter", 14))
        self.freq_label.pack(pady=10)

        # Slider (Scale) per il controllo della frequenza
        self.freq_slider = tk.Scale(
            master,
            from_=0,
            to=20000, # Esteso a 20000 Hz come richiesto
            resolution=1, # Passo di 1 Hz
            orient=tk.HORIZONTAL, # Orientamento orizzontale
            length=300, # Lunghezza dello slider in pixel
            label="Seleziona Frequenza (Hz)", # Etichetta dello slider
            command=self.update_frequency_and_draw, # Chiamato quando lo slider si muove
            variable=self.frequency, # Collega lo slider alla variabile self.frequency
            font=("Inter", 12)
        )
        self.freq_slider.set(0) # Imposta la frequenza predefinita a 0 Hz (spento)
        self.freq_slider.pack(pady=10)

        # Menu a tendina per la selezione della forma d'onda
        waveform_options = ["Sinusoidale", "Quadra", "Triangolare", "Dente di Sega"]
        self.waveform_menu_label = tk.Label(master, text="Seleziona Forma d'Onda:", font=("Inter", 12))
        self.waveform_menu_label.pack(pady=(10, 0))
        self.waveform_option_menu = tk.OptionMenu(master, self.waveform_type, *waveform_options)
        self.waveform_option_menu.config(font=("Inter", 12))
        self.waveform_option_menu.pack(pady=(0, 10))


        # Canvas per disegnare la forma d'onda
        self.canvas_width = 350
        self.canvas_height = 200
        self.waveform_canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height, bg="white", bd=2, relief="groove")
        self.waveform_canvas.pack(pady=10)

        # Inizializza e avvia immediatamente lo stream audio
        try:
            self.stream = sd.OutputStream(
                samplerate=self.samplerate,
                channels=1,
                callback=self.audio_callback,
                blocksize=1024
            )
            self.stream.start()
            print("Stream audio avviato.")
        except Exception as e:
            print(f"Errore all'avvio dello stream audio: {e}")
            self.stream = None

        # Assicurati che lo stream audio venga fermato quando la finestra viene chiusa
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Disegna l'onda iniziale (a 0 Hz, quindi piatta)
        self.draw_waveform()

    def generate_waveform_samples(self, waveform_type, frequency, t_array, phase_offset=0.0):
        """
        Genera i campioni della forma d'onda specificata.
        t_array: array del tempo o degli indici dei campioni.
        phase_offset: offset di fase per la continuità.
        """
        if frequency == 0:
            return np.zeros_like(t_array)

        # Calcola la fase per ogni punto, includendo l'offset per la continuità
        # Per le forme d'onda non sinusoidali, è più semplice lavorare con il tempo normalizzato per ciclo
        # piuttosto che con la fase in radianti direttamente, e poi applicare la forma.
        # Tuttavia, per mantenere la continuità, useremo un approccio basato sulla fase accumulata.

        # Frequenza angolare (radianti al secondo)
        angular_frequency = 2 * np.pi * frequency

        # Calcola la fase per ogni punto nel tempo
        # Per l'audio callback, t_array è np.arange(frames) e deve essere scalato per il campionamento
        # Per il disegno, t_array è np.linspace(0, display_duration, num_points)
        if len(t_array) > 1 and t_array[1] - t_array[0] < 1: # Questo è l'array 't' del disegno
            # t_array è già in secondi
            phase_values = angular_frequency * t_array + phase_offset
        else: # Questo è l'array 't' (frames) del callback audio
            # t_array è in campioni, deve essere convertito in secondi e poi in fase
            phase_values = angular_frequency * (t_array / self.samplerate) + phase_offset

        if waveform_type == "Sinusoidale":
            return self.amplitude * np.sin(phase_values)
        elif waveform_type == "Quadra":
            # Un'onda quadra è 1 per la prima metà del ciclo e -1 per la seconda
            # np.sign(np.sin(phase_values)) è un modo comune per generarla
            return self.amplitude * np.sign(np.sin(phase_values))
        elif waveform_type == "Dente di Sega":
            # Un'onda a dente di sega sale linearmente da -1 a 1 per ciclo
            # (phase_values / (2 * np.pi)) % 1 normalizza la fase a [0, 1) per ciclo
            normalized_phase = (phase_values / (2 * np.pi)) % 1
            return self.amplitude * (2 * normalized_phase - 1) # Scala da [0, 1) a [-1, 1)
        elif waveform_type == "Triangolare":
            # Un'onda triangolare sale da -1 a 1 e poi scende a -1 per ciclo
            normalized_phase = (phase_values / (2 * np.pi)) % 1
            # np.abs(2 * normalized_phase - 1) crea una forma a V da 0 a 1 e ritorno a 0
            # 2 * ... - 1 scala da [0, 1] a [-1, 1]
            return self.amplitude * (2 * np.abs(2 * normalized_phase - 1) - 1)
        else:
            return np.zeros_like(t_array) # Default a silenzio o errore

    def audio_callback(self, outdata, frames, time, status):
        """
        Funzione di callback per sounddevice. Questa funzione viene chiamata da un thread separato
        ogni volta che il buffer audio necessita di più dati.
        """
        if status:
            print(status)

        current_freq = self.frequency.get()
        selected_waveform = self.waveform_type.get()

        if current_freq == 0:
            outdata.fill(0)
            self.current_phase = 0.0 # Resetta la fase quando è silenzio
            return

        # Genera i campioni per il blocco corrente
        t_block = np.arange(frames) # Array degli indici dei campioni per questo blocco
        
        # Genera la forma d'onda usando la funzione helper
        # La fase corrente viene passata come offset iniziale per mantenere la continuità
        waveform_samples = self.generate_waveform_samples(
            selected_waveform,
            current_freq,
            t_block, # Passa l'array degli indici dei campioni
            self.current_phase
        )
        
        outdata[:] = waveform_samples.reshape(-1, 1) # Assicura che l'output sia una colonna

        # Aggiorna la fase per il prossimo blocco
        # L'incremento di fase è basato sulla frequenza angolare e sul numero di campioni nel blocco
        increment_per_frame = (2 * np.pi * current_freq) / self.samplerate
        self.current_phase = (self.current_phase + increment_per_frame * frames) % (2 * np.pi)


    def update_waveform_type(self, *args):
        """
        Chiamato quando la selezione della forma d'onda cambia.
        Aggiorna la visualizzazione dell'onda.
        """
        # Resetta la fase quando si cambia la forma d'onda per evitare glitch audio
        self.current_phase = 0.0
        self.draw_waveform() # Ridisegna l'onda con la nuova forma

    def update_frequency_and_draw(self, slider_value=None):
        """
        Aggiorna l'etichetta della frequenza nell'interfaccia utente e ridisegna l'onda sul canvas.
        """
        if slider_value is not None:
            freq = float(slider_value)
            self.frequency.set(freq)
        else:
            freq = self.frequency.get()

        self.freq_label.config(text=f"Frequenza: {freq:.1f} Hz")
        self.draw_waveform()

    def draw_waveform(self):
        """
        Disegna la forma d'onda selezionata sul canvas.
        """
        self.waveform_canvas.delete("all") # Cancella qualsiasi cosa disegnata in precedenza

        current_freq = self.frequency.get()
        selected_waveform = self.waveform_type.get()

        if current_freq == 0:
            # Disegna una linea piatta al centro se la frequenza è 0
            y_center = self.canvas_height / 2
            self.waveform_canvas.create_line(0, y_center, self.canvas_width, y_center, fill="gray", width=2)
            return

        num_points = 1000 # Numero di punti per disegnare la curva

        # Logica per calcolare la durata di visualizzazione (display_duration)
        # per mostrare un numero adeguato di cicli in base alla frequenza.
        if current_freq < 37: # Frequenze molto basse (es. 1 Hz a 36 Hz)
            display_duration = min(2.0 / current_freq, 0.2)
        elif (current_freq >= 37 and current_freq < 100): # Frequenze basse-medie (37 Hz a 99 Hz)
            display_duration = min(1.7 / current_freq, 0.18)
        elif (current_freq >= 100 and current_freq < 500): # Frequenze medie (100 Hz a 499 Hz)
            display_duration = min(1.5 / current_freq, 0.15)
        elif (current_freq >= 500 and current_freq < 1000): # Frequenze medio-alte (500 Hz a 999 Hz)
            display_duration = min(1.3 / current_freq, 0.1)
        else: # Frequenze alte (1000 Hz a 20000 Hz)
            display_duration = 0.005 # 5 millisecondi

        t = np.linspace(0, display_duration, num_points, endpoint=False)
        
        # Genera i valori y per la visualizzazione usando la funzione helper
        y_values = self.generate_waveform_samples(selected_waveform, current_freq, t)

        # Scala i valori y per adattarli all'altezza del canvas
        y_scaled = (y_values * -1 * (self.canvas_height / 2 - 10)) + (self.canvas_height / 2)

        # Crea una lista di coordinate (x, y) per il disegno
        points = []
        for i in range(num_points):
            x = i * (self.canvas_width / num_points)
            y = y_scaled[i]
            points.append(x)
            points.append(y)

        if len(points) < 4:
            return

        self.waveform_canvas.create_line(points, fill="blue", width=3)

    def on_closing(self):
        """
        Chiamato quando la finestra Tkinter viene chiusa. Assicura che lo stream audio sia fermato.
        """
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()
            print("Stream audio fermato e chiuso.")
        self.master.destroy()

# Punto di ingresso principale dell'applicazione
if __name__ == "__main__":
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError:
        print("Per favore, installa le librerie 'numpy' e 'sounddevice' con:")
        print("pip install numpy sounddevice")
        exit()

    root = tk.Tk()
    app = FrequencyGeneratorApp(root)
    root.mainloop()
