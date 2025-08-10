#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 30 11:24:23 2025
programma per QUANTUM Computing. Illustrazione per studio del 
QBIT, tramite framework Qiskit. SImulazione di un circuito quantistico 
con 2 QBIT
@author: macbook_vincenzo
"""

# Importa le classi necessarie
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt

# --- 1. Dichiarazione dei 2 Qubit ---
circuito = QuantumCircuit(2, 2)
circuito.h(0)
circuito.cx(0, 1)

# --- 2. Disegno del Circuito ---
print("Disegno del circuito quantistico:")
circuito.draw(output='mpl')

# --- 3. Misurazione e Simulazione ---
# Aggiungiamo le misurazioni ai qubit
circuito.measure([0, 1], [0, 1])

# Otteniamo il simulatore
simulator = Aer.get_backend('qasm_simulator')

# Non usiamo più execute. Invece, chiamiamo il metodo 'run' del simulatore.
# Il metodo run restituisce un oggetto Job che gestisce l'esecuzione.
job = simulator.run(circuito, shots=1024)

# Aspettiamo che il job finisca e otteniamo il risultato.
result = job.result()
counts = result.get_counts(circuito)

print("\nRisultati della simulazione (1024 esecuzioni):")
print(counts)

print("\n \nR Visualizzazione del GRAFICO con matPlot (vedi sezione PLOTS a destra)")
plot_histogram(counts)
plt.title("Distribuzione delle misure - Stato di Bell")
plt.show()