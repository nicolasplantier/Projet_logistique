
import numpy as np 


with open('Matrice des itineraires entres les noeuds', 'r') as opfile : 
    liste_itineraires = eval(opfile.read()) 
matrix_durations = np.loadtxt('Matrice des temps de trajet entre les noeuds')


