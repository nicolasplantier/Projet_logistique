import multiprocessing
from tracemalloc import start
import folium 
import numpy as np 
import matplotlib.pyplot as plt
import random as rd 
import requests
import json 
from folium import plugins
from folium.plugins import HeatMap
import time 
from networkx import DiGraph
from vrpy import VehicleRoutingProblem
from time import * 
import networkx as nx
from folium.features import DivIcon
import selenium
from selenium import webdriver


def dist(u,v):
    return ((v[0]-u[0])**2 + (u[1]-v[1])**2)**0.5
    

def distanceGPS(A,B):
    """Retourne la distance en mètres entre les 2 points A et B connus grâce à
       leurs coordonnées GPS (en radians).
    """
    # Rayon de la terre en mètres (sphère IAG-GRS80)
    latA = 2*np.pi*A[0]/360
    longA = 2*np.pi*A[1]/360
    latB = 2*np.pi*B[0]/360
    longB = 2*np.pi*B[1]/360
    RT = 6378137
    # angle en radians entre les 2 points
    S = 2*np.sqrt(np.sin((latB-latA)/2)**2+np.cos(latA)*np.cos(latB)*np.sin((longB-longA)/2)**2)
    # S = np.arccos(np.sin(latA)*np.sin(latB) + np.cos(latA)*np.cos(latB)*np.cos(abs(longB-longA)))
    # distance entre les 2 points, comptée sur un arc de grand cercle
    return S*RT

    
def change(way, dmax, dmin, h): #
    """
    dmax c'est la distance maximale autorisée entre deux points : si est dépassé, on en crée de nouveaux
    dmin c'est l'inverse : on détruit un point. h c'est la distance optimale, entre les deux.   
    """
    N = len(way)
    c = 0 #C'est l'indice courant, on se déplace le long du chemin.
    while c+1 != N: 
        D = dist(way[c],way[c+1]) #Distance between start and arrival  
        x1, y1 = way[c]
        x2, y2 = way[c+1]
        if D > dmax: 
            x = (h/D)*(x2 - x1) + x1
            y = (h/D)*(y2 - y1) + y1
            way.insert(c+1, [x,y])
            c += 1
        elif D < dmin : 
            way.pop(c+1)
        else : 
            c += 1
        N = len(way)
    return way 


def construction_ligne_matrice(node_start, i, nodes, matrix_durations, liste_itineraires):
    start_x = nodes[node_start][1] 
    start_y = nodes[node_start][0]
    j = 0

    for node_end in nodes :
        print("Nous sommes en train de traiter l'itinéraire partant du noeud", i, "vers le noeud", j)
        end_x = nodes[node_end][1] 
        end_y = nodes[node_end][0]
        if node_start == node_end: 
            matrix_durations.append([0,i, j])
            liste_itineraires.append([[node_start, node_end], i, j]) 
        else : 

            texte = requests.get(f'''https://wxs.ign.fr/essentiels/geoportail/itineraire/rest/1.0.0/route?resource=bdtopo-osrm&start={str(start_x)},{str(start_y)}&end={str(end_x)},{str(end_y)}&timeUnit=second''')
            texte = json.loads(texte.text)
            itineraire = texte['geometry']['coordinates']
            duration = texte['duration']
            matrix_durations.append([duration, i, j])  
            for element in itineraire: 
                if round(element[0]) == 2 : 
                    p = element[0]
                    element[0] = element[1]
                    element[1] = p 
            itineraire_points = change(itineraire,  0.00025*(1/3), 0.0002*(1/3), 0.000225*(1/3))

            #il va maintenant falloir modifier cela en une liste de noeud. 
            itineraire_noeuds = []
            node_courant = "-1" 
            for point in itineraire_points:
                for node in nodes : 
                    if node != node_courant and distanceGPS(point, nodes[node]) <= 15 : 
                        itineraire_noeuds.append(node)
                        node_courant = node
            ending_node = itineraire_noeuds[-1]
            lista = []  #On crée cette liste pour éviter situations du type : [6, 4, 0, 4, 0] pour aller de 6 en 0... 
            noeuds_deja_dis = []
            for node in itineraire_noeuds: 
                if node not in noeuds_deja_dis and node != ending_node: 
                    lista.append(node)
                    noeuds_deja_dis.append(node)
                elif node == ending_node:
                    lista.append(node)
                    liste_itineraires.append([lista, i, j])  #Donc liste_itineraires[i] ce sont les itinéraires au départ de i, mais pas dans le bon ordre. 
        j+=1


def construction_matrices(nodes):
    """
    nodes : liste des noeuds du quartier
    Renvoie : 
        - la matrice des itinéraires entre les noeuds : liste_itineraires[i][j] liste de tous les noeuds empruntés pour aller de i vers j. 
        - la matrice des temps de trajet entre les noeuds. 
        - la matrice des routes : liste_routes[i][j] : 
            o Si i et j pas reliés : vaut 0 
            o Si i et j bien reliés : objet de la class route
    """
    N_nodes = len(nodes)
    processors = []

    manager = multiprocessing.Manager()
    matrix_durations = manager.list()
    liste_itineraires = manager.list()
    
    i = 0 
    for node_start in nodes : 
        p = multiprocessing.Process(target = construction_ligne_matrice, args=[node_start, i, nodes, matrix_durations, liste_itineraires])
        processors.append(p)
        p.start()
        i+=1 
    for p in processors:
        p.join()
    liste_itineraires_real = []
    matrix_durations_real = []
    for i in range(N_nodes):
        liste_itineraires_real.append([])
        matrix_durations_real.append([])
        for j in range(N_nodes): 
            liste_itineraires_real[i].append([])
            matrix_durations_real[i].append([])
    for element in matrix_durations: 
        matrix_durations_real[element[1]][element[2]] = element[0]
    for element in liste_itineraires: 
        liste_itineraires_real[element[1]][element[2]] = element[0]

    return liste_itineraires_real, matrix_durations_real

# ------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    with open('Noeuds dans le quartier latin', 'r') as opfile:
        nodes = eval(opfile.read())
    liste_itineraires, matrix_durations = construction_matrices(nodes)
    print(matrix_durations)
    with open('Matrice des itineraires entres les noeuds', 'w') as opfile : 
        opfile.write(str(liste_itineraires)) 
    np.savetxt('Matrice des temps de trajet entre les noeuds', X = matrix_durations)

