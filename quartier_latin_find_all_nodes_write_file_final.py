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
import math 


"""
Définitions de quelques variables globales. 
"""

rgb_orange = (245, 215, 170)
rgb_jaune = (248, 250, 197)
rgb_blanc = (255, 255, 255)
rgb_gris = (237, 238, 236)

green = '#80FF00'
yellow = '#FFFF00'
orange ='#FF8000'
red = '#FF0000'


"""
Définition des fonctions de bases utiles au code
"""

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
    S = np.arccos(np.sin(latA)*np.sin(latB) + np.cos(latA)*np.cos(latB)*np.cos(abs(longB-longA)))
    if math.isnan(S):
        return 0
    return S*RT

    
def change(way, dmax, dmin, h): 
    """
    Cette fonction a pour objectif de passer d'une trajectoire où les points sont répartis de manière irrégulière (beaucoup dans les tournants, peu dans les lignes droites) 
    vers une trajectoire où les points sont répartis de manière régulière : tous écarté au minimum de dmin et au maximum de dmax. 

    Plus précisément : 
        - dmax distance max entre deux points : si dépassée, on ajoute un point sur la trajectoire. 
        - si dist<dmin, on supprime le point suivant
        - h c'est la distance optimale   
    
    Attention, ici dmin et dmax sont exprimées pour la distance euclidienne dans R2, à partir des coordonnées des vecteurs (lat, long). 
    """

    N = len(way)
    c = 0 #indice courant, on se déplace le long du chemin.
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


def route_dect(itineraire): 
    """
    Renvoie la liste des routes d'un itinéraire (liste de points) en détectant les changements d'angles.
    Route : [noeud de début, noeud d'arrivée] (en coordonnées), et donc a priori un segment
    """
    theta = 0 
    N = len(itineraire)
    routes = [[itineraire[0]]] # Chaque élément de routes est une route, avec un point de départ, et un point d'arrivée. 
    for k in range(N-2):
        a = distanceGPS(itineraire[k+2], itineraire[k+1])
        b = distanceGPS(itineraire[k+2], itineraire[k])
        c = distanceGPS(itineraire[k], itineraire[k+1]) 
        try :
            theta = round(np.arccos((a**2 - b**2 - c**2)/(-2*b*c))*360/(2*np.pi))
        except ValueError:
            theta = 0
        if theta >= 35 : #le prochain point est le départ d'une nouvelle route. 
            routes.append([])
            routes[-1].append(itineraire[k+1]) #On ouvre une nouvelle route 
            routes[-2].append(itineraire[k]) #Et on ferme l'ancienne 
    return routes


def find_nodes(coordinates, N, d): 

    """ 
    Trouve tous les noeuds dans le rectangle formé par les points de coordinates (coins opposés bas gauche et haut droite du rectangle)

    N : nombre d'itinéraires que l'on va faire pour trouver tous ces noeuds. 

    On utilisera au sein de cette fonction un API du géoportail pour trouver l'itinéraire optimale entre deux points. 
    """ 

    x_min = coordinates[0][0]
    x_max = coordinates[1][0]
    y_min = coordinates[0][1]
    y_max = coordinates[1][1]
    Delta_x = x_max-x_min
    Delta_y = y_max-y_min

    nodes = {}

    Y = [] # Liste du nombre des points trouvés jusque là
    T = [] # Liste des temps : à chaque point correspond le moment où il a été trouvé
    

    T_init = time()
    courant = 1 # Indice courant du noeud ajouté.
    for k in range(N): 
        print(round((k/N)*100,2)) #indice de progression

        #sélection au hasard des points de départ et d'arrivée de l'itinéraire
        start_x = x_min + Delta_x*rd.random()
        start_y = y_min + Delta_x*rd.random()
        end_x = x_min + Delta_x*rd.random()
        end_y = y_min + Delta_x*rd.random()
        texte = requests.get(f'https://wxs.ign.fr/essentiels/geoportail/itineraire/rest/1.0.0/route?resource=bdtopo-osrm&start={str(start_y)},{str(start_x)}&end={str(end_y)},{str(end_x)}&timeUnit=second')
        texte = json.loads(texte.text)
        itineraire = texte['geometry']['coordinates']
        for el in itineraire: #l'API renvoie lat et long dans le mauvais sens
            i=el[0]
            el[0]=el[1]
            el[1]=i

        itineraire = change(itineraire, 0.000125/3, 0.00005*(2/3), 0.0001125/3) #uniformisation des points
        routes = route_dect(itineraire) #on repère toutes les routes dessus, une route = segment
        noeuds_courant = []
        noeuds_potentiel = []

        if len(routes) != (1 and 2) : #Si 1 route pas de noeuds, si 2 souvent c'est que pas intéressant
            for route in routes[1:len(routes)-1] : 
                noeuds_courant.append(route[0])  #on ne prend que le 0 car le 1 (arrivée) est le départ de la route suivante

            for noeud in noeuds_courant : 
                if len(nodes) !=0 : #c'est à dire si l'on a déjà trouvé des noeuds dans le quartier 
                    d_min = 100000
                    for node in nodes : 
                        if distanceGPS(nodes[node], noeud) <= d_min: 
                            d_min = distanceGPS(nodes[node], noeud)
                    if d_min >= d and d_min != 100000: 
                        noeuds_potentiel.append(noeud)
                        Temps = time()
                        T.append(Temps-T_init)
                        Y.append(len(T))
                else : 
                    noeuds_potentiel.append(noeud)
                    Temps = time()
                    T.append(Temps-T_init)
                    Y.append(len(T))
            for noeud in noeuds_potentiel: 
                nodes[str(courant)] = noeud
                courant += 1
        nodes['0'] = [48.84559987480441, 2.3398174306444814]    #C'est le 60 boulevard saint michel 
    return nodes, T, Y


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__': 
    quartier_latin = [[48.8397708243902, 2.3366302833091703], [48.84790929240088, 2.3454986328314145]]
    Noeuds, T, Y = find_nodes(coordinates = quartier_latin, N = 1000, d = 20) 

    print('On a trouvé dans le quartier latin un total de', len(Noeuds), 'Noeuds')
    with open('Noeuds dans le quartier latin', 'w') as opfile:
        opfile.write(str(Noeuds))

    plt.scatter(T,Y, color ='red')
    plt.xlabel('Temps (en secondes)')
    plt.ylabel('Nombre de noeuds trouvés')
    plt.title('Nombre de Noeuds trouvés dans le quartier latin en fonction du temps')

    # Il faut modifier mypath par la localisation du dossier où vous avez clone le repo git. 
    plt.savefig('mypath/Nombre de Noeuds trouvés dans le quartier latin en fonction du temps.png')
