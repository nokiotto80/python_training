import tkinter as tk
import numpy as np
import sounddevice as sd

class FrequencyGeneratorApp:
    def __init__(self, master):
        self.master = master
        master.title("Generatore di Frequenza")
        master.geometry("400x650") # Aumenta la dimensione della finestra per le etichette degli assi

        self.frequency = tk.DoubleVar(value=0.0) # Variabile Tkinter per la frequenza attuale
        self.amplitude_var = tk.DoubleVar(value=0.5) # Ampiezza controllata dallo slider (0.0 a 1.0)
        self.phase_var = tk.DoubleVar(value=0.0) # Variabile Tkinter per lo shift di fase in gradi

        self.samplerate = 44100 # Frequenza di campionamento audio standard (campioni al secondo)
        self.current_phase = 0.0 # Mantiene la fase corrente in radianti per una forma d'onda continua (per AUDIO)
        self.display_phase_offset = 0.0 # Mantiene la fase corrente per la VISUALIZZAZIONE dell'onda animata

        # Variabile Tkinter per la selezione della forma d'onda
        self.waveform_type = tk.StringVar(value="Sinusoidale")
        self.waveform_type.trace_add("write", self.update_waveform_type) # Chiamato quando la forma d'onda cambia

        # Etichetta di stato combinata (Frequenza, Ampiezza, Fase)
        self.status_label = tk.Label(
            master,
            text=self._get_status_text(), # Inizializza il testo
            font=("Inter", 14)
        )
        self.status_label.pack(pady=10)

        # Slider 1) (Scale) per il controllo della frequenza
        self.freq_slider = tk.Scale(
            master,
            from_=0,
            to=20000, # Esteso a 20000 Hz
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

        # Slider 2) (Scale) per il controllo del volume, AMPIEZZA onda
        self.volume_slider = tk.Scale(
            master,
            from_=0.0, # Volume minimo (silenzio)
            to=1.0, # Volume massimo (ampiezza 1.0)
            resolution=0.01, # Passo più fine
            orient=tk.HORIZONTAL, # Orientamento orizzontale
            length=300, # Lunghezza dello slider in pixel
            label="Regola Volume (Ampiezza)", # Etichetta dello slider
            command=self.update_volume_label, # Chiamato quando lo slider si muove
            variable=self.amplitude_var, # Collega lo slider alla variabile self.amplitude_var
            font=("Inter", 12)
        )
        self.volume_slider.set(0.5) # Imposta il volume predefinito a metà
        self.volume_slider.pack(pady=10)

        # Slider 3) (Scale) per il controllo della FASE, angolo, shift di essa
        self.phase_slider = tk.Scale(
            master,
            from_=-180.0, # Fino a -180 gradi
            to=180.0, # Fino a +180 gradi
            resolution=0.5, # Passo più fine
            orient=tk.HORIZONTAL, # Orientamento orizzontale
            length=300, # Lunghezza dello slider in pixel
            label="Sposta la Fase (°)", # Etichetta dello slider
            command=self.update_phase_and_display, # Chiamato quando lo slider si muove
            variable=self.phase_var, # Collega lo slider alla variabile self.phase_var
            font=("Inter", 12)
        )
        self.phase_slider.set(0) # Imposta la fase predefinita a 0 gradi
        self.phase_slider.pack(pady=10)

        # Bottone per fermare e resettare tutto
        self.stop_button = tk.Button(
            master,
            text="STOP",
            command=self.stop_and_reset,
            width=20,
            height=2,
            font=("Inter", 12)
        )
        self.stop_button.pack(pady=5)

        # Menu a tendina per la selezione della forma d'onda
        waveform_options = ["Sinusoidale", "Quadra", "Triangolare", "Dente di Sega", "SINC"]
        self.waveform_menu_label = tk.Label(master, text="Seleziona Forma d'Onda:", font=("Inter", 12))
        self.waveform_menu_label.pack(pady=(10, 0))
        self.waveform_option_menu = tk.OptionMenu(master, self.waveform_type, *waveform_options)
        self.waveform_option_menu.config(font=("Inter", 12))
        self.waveform_option_menu.pack(pady=(0, 10))

        # --- Canvas per disegnare la forma d'onda e le sue etichette degli assi ---
        self.canvas_width = 350
        self.canvas_height = 200
        # Posiziona il canvas usando place per un controllo preciso
        self.waveform_canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height, bg="white", bd=2, relief="groove")
        # Calcolo approssimativo della posizione Y dopo gli elementi impacchettati
        canvas_y_pos = 400
        canvas_x_pos = 40 # Lascia spazio a sinistra per l'etichetta Y
        self.waveform_canvas.place(x=canvas_x_pos, y=canvas_y_pos)

        # Etichetta Asse Y
        self.y_axis_label = tk.Label(master, text="Ampiezza", font=("Inter", 10), fg="gray")
        # Posizionata a sinistra del canvas, centrata verticalmente
        self.y_axis_label.place(x=canvas_x_pos - 35, y=canvas_y_pos + self.canvas_height / 2, anchor="center")

        # Etichetta Asse X
        self.x_axis_label = tk.Label(master, text="Tempo (s)", font=("Inter", 10), fg="gray")
        # Posizionata sotto il canvas, centrata orizzontalmente
        self.x_axis_label.place(x=canvas_x_pos + self.canvas_width / 2, y=canvas_y_pos + self.canvas_height + 15, anchor="center")
        # --- Fine etichette assi ---

        # Variabile per gestire l'ID del ciclo di animazione
        self.animation_id = None 

        # Inizializza e avvia immediatamente lo stream audio
        try:
            self.stream = sd.OutputStream(
                samplerate=self.samplerate,
                channels=1,
                callback=self.audio_callback,
                blocksize=2048 # Aumentato il blocksize per tentare di ridurre gli scatti
            )
            self.stream.start()
            print("Stream audio avviato.")
        except Exception as e:
            print(f"Errore all'avvio dello stream audio: {e}")
            self.stream = None

        # Assicurati che lo stream audio venga fermato quando la finestra viene chiusa
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Avvia il ciclo di animazione del grafico
        self.animate_waveform()

    def _get_status_text(self):
        """Helper function to format the status text."""
        freq = self.frequency.get()
        amp = self.amplitude_var.get()
        phase_deg = self.phase_var.get() # Ottieni il valore in gradi
        return f"Frequenza: {freq:.1f} Hz, Ampiezza: {amp:.2f}, Fase: {phase_deg:.1f}°"

    def generate_waveform_samples(self, waveform_type, frequency, t_array, phase_offset_current=0.0):
        """
        Genera i campioni della forma d'onda specificata.
        t_array: array del tempo o degli indici dei campioni.
        phase_offset_current: offset di fase attuale (per audio o visualizzazione continua).
        """
        if frequency == 0:
            return np.zeros_like(t_array)

        current_amplitude = self.amplitude_var.get()
        phase_shift_degrees = self.phase_var.get()
        phase_shift_radians = np.radians(phase_shift_degrees) # Converti da gradi a radianti

        angular_frequency = 2 * np.pi * frequency

        # Calcola la fase per ogni punto nel tempo, aggiungendo lo shift dallo slider
        if len(t_array) > 1 and (t_array[1] - t_array[0]) < 1: # Questo è l'array 't' del disegno (già in secondi)
            phase_values = angular_frequency * t_array + phase_offset_current + phase_shift_radians
        else: # Questo è l'array 't' (frames) del callback audio (deve essere convertito in secondi)
            phase_values = angular_frequency * (t_array / self.samplerate) + phase_offset_current + phase_shift_radians

        if waveform_type == "Sinusoidale":
            return current_amplitude * np.sin(phase_values)
        elif waveform_type == "Quadra":
            return current_amplitude * np.sign(np.sin(phase_values))
        elif waveform_type == "Dente di Sega":
            normalized_phase = (phase_values / (2 * np.pi)) % 1
            return current_amplitude * (2 * normalized_phase - 1)
        elif waveform_type == "Triangolare":
            normalized_phase = (phase_values / (2 * np.pi)) % 1
            return current_amplitude * (2 * np.abs(2 * normalized_phase - 1) - 1)
        elif waveform_type == "SINC":
            sinc_x_range = 10.0
            normalized_phase = (phase_values / (2 * np.pi)) % 1
            sinc_x_value = (normalized_phase * sinc_x_range) - (sinc_x_range / 2)
            return current_amplitude * np.sinc(sinc_x_value)
        else:
            return np.zeros_like(t_array)

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

        t_block = np.arange(frames)
        
        waveform_samples = self.generate_waveform_samples(
            selected_waveform,
            current_freq,
            t_block,
            self.current_phase # Passa la fase corrente per l'audio
        )
        
        outdata[:] = waveform_samples.reshape(-1, 1)

        increment_per_frame = (2 * np.pi * current_freq) / self.samplerate
        self.current_phase = (self.current_phase + increment_per_frame * frames) % (2 * np.pi)

    def stop_and_reset(self):
        """
        Metodo per fermare la riproduzione, resettare gli slider e aggiornare l'interfaccia.
        """

        
        # Resetta i valori degli slider
        self.frequency.set(0)
        self.amplitude_var.set(0.5)
        self.phase_var.set(0)
        
        # Resetta la fase audio e di visualizzazione
        self.current_phase = 0.0
        self.display_phase_offset = 0.0

        # Aggiorna la status label e il display del canvas
        self.status_label.config(text=self._get_status_text())
        self.draw_waveform()
        print("Valori resettati e visualizzazione aggiornata.")


    def update_volume_label(self, slider_value=None):
        """
        Aggiorna l'etichetta di stato.
        """
        self.status_label.config(text=self._get_status_text())

    def update_phase_and_display(self, slider_value=None):
        """
        Aggiorna l'etichetta di stato quando lo slider di fase si muove.
        """
        self.status_label.config(text=self._get_status_text())


    def update_waveform_type(self, *args):
        """
        Chiamato quando la selezione della forma d'onda cambia.
        """
        # Resetta la fase per audio e visualizzazione per evitare glitch e far ripartire l'animazione
        self.current_phase = 0.0
        self.display_phase_offset = 0.0 
        # L'animazione aggiornerà il disegno al prossimo frame.

    def update_frequency_and_draw(self, slider_value=None):
        """
        Aggiorna l'etichetta della frequenza nell'interfaccia utente.
        Il disegno è ora gestito dal ciclo di animazione.
        """
        if slider_value is not None:
            freq = float(slider_value)
            self.frequency.set(freq)
        else:
            freq = self.frequency.get()

        self.status_label.config(text=self._get_status_text())

    def animate_waveform(self):
        """
        Aggiorna continuamente la visualizzazione dell'onda sul canvas.
        """
        current_freq = self.frequency.get()
        animation_interval_ms = 20 # 50 frames per second
        animation_interval_seconds = animation_interval_ms / 1000.0

        if current_freq > 0:
            # Incrementa la fase di visualizzazione per far muovere l'onda
            # L'incremento è proporzionale alla frequenza per un effetto realistico
            self.display_phase_offset = (self.display_phase_offset + 
                                         2 * np.pi * current_freq * animation_interval_seconds) % (2 * np.pi)
        else:
            self.display_phase_offset = 0.0 # Resetta se la frequenza è zero

        self.draw_waveform() # Ridisegna l'onda con la fase aggiornata
        
        # Ripianifica l'esecuzione di questa funzione
        self.animation_id = self.master.after(animation_interval_ms, self.animate_waveform)

    def draw_waveform(self):
        """
        Disegna la forma d'onda selezionata sul canvas.
        """
        self.waveform_canvas.delete("all")

        current_freq = self.frequency.get()
        selected_waveform = self.waveform_type.get()

        if current_freq == 0:
            y_center = self.canvas_height / 2
            self.waveform_canvas.create_line(0, y_center, self.canvas_width, y_center, fill="gray", width=2)
            return

        num_points = 1000

        # Logica per calcolare la durata di visualizzazione (display_duration)
        if current_freq < 37:
            display_duration = min(2.0 / current_freq, 0.2)
        elif (current_freq >= 37 and current_freq < 100):
            display_duration = min(1.7 / current_freq, 0.18)
        elif (current_freq >= 100 and current_freq < 500):
            display_duration = min(1.5 / current_freq, 0.15)
        elif (current_freq >= 500 and current_freq < 1000):
            display_duration = min(1.3 / current_freq, 0.1)
        else:
            display_duration = 0.005

        t = np.linspace(0, display_duration, num_points, endpoint=False)
        
        # Genera i valori y per la visualizzazione usando la funzione helper e l'offset di fase per l'animazione
        y_values = self.generate_waveform_samples(selected_waveform, current_freq, t, self.display_phase_offset)

        y_scaled = (y_values * -1 * (self.canvas_height / 2 - 10)) + (self.canvas_height / 2)

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
        # Annulla il ciclo di animazione se è attivo
        if self.animation_id:
            self.master.after_cancel(self.animation_id)
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
