#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lancio di 2 DADI
             2 dices launch simulation
Created on Tue Dec 24 18:18:27 2024

@author: macbook_vincenzo
"""


import random

def lancia_dadi():
    dado1 = random.randint(1, 6)
    dado2 = random.randint(1, 6)
    return dado1, dado2

while True:
    input("Premi Invio per lanciare i dadi...")
    dado1, dado2 = lancia_dadi()
    print(f"Hai lanciato un {dado1} e un {dado2}")
    if input("Vuoi lanciare di nuovo? (S/N): ").lower() != 's':
        break

