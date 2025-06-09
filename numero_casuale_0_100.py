#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 17:18:49 2024

@author: macbook_vincenzo
"""

import random

def indovina_numero():
    """
    Gioco indovina il numero tra 0 e 100.
    """

    numero_segreto = random.randint(0, 100)
    tentativi = 0

    print("Benvenuto nel gioco Indovina il numero!")
    print("Ho pensato a un numero tra 0 e 100. Prova a indovinarlo!")

    while True:
        try:
            scelta = int(input("Inserisci il tuo numero: "))
        except ValueError:
            print("Devi inserire un numero intero.")
            continue

        tentativi += 1

        if scelta < numero_segreto:
            print("Il numero è più grande.")
        elif scelta > numero_segreto:
            print("Il numero è più piccolo.")
        else:
            print(f"Complimenti! Hai indovinato in {tentativi} tentativi.")
            break

if __name__ == "__main__":
    indovina_numero()