from tkinter import *

canvas_width = 600
canvas_height =600

master = Tk()

w = Canvas(master, 
           width=canvas_width, 
           height=canvas_height,background="Yellow")
w.pack()

centro_x, centro_y = 300, 300
raggio_interno = 100
raggio_esterno = 150
ovale_interno = w.create_oval(centro_x - raggio_interno, centro_y - raggio_interno,
                                     centro_x + raggio_interno, centro_y + raggio_interno,
                                     fill="blue")
ovale_esterno = w.create_oval(centro_x - raggio_esterno, centro_y - raggio_esterno,
                                     centro_x + raggio_esterno, centro_y + raggio_esterno,
                                     fill="lightgray")

mainloop()