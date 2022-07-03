"""
Ce document vient construire les matrices : 
    - liste iti noeuds = telle que liste_iti_noeuds[i][j] renvoie la liste des noeuds par lesquels on va devoir passer pour aller de i vers j 
    - matrix_durations = telle que matrix_durations[i][j] renvoie le temps de trajet necessaire pour aller du noeud i vers le noeud j. On appellera cette matrice lors des calculs de vrpy. 

Ce travail de construction de matrices est un travail préliminaire : il dépend simplement du découpage en sous cluster et ne dépend pas du trafic dans les axes considérés. 

"""

import find_all_nodes_write_file as toolbox 

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
import random as rd 
from time import * 
import networkx as nx
import numpy as np
from folium.features import DivIcon
import io
from PIL import Image
import selenium
from selenium import webdriver
import os 
import pickle
import multiprocessing


# -----------------------------------------------------------------------------------------------------------------------------------------------
def construction_matrices(Noeuds, matrix_liste_iti_noeuds_cluster, matrix_durations_cluster):
    """
    Cette fonction prend en entrée la liste des noeuds qui ont été prédéfinis. 
    Elle renvoie : 
        - la matrice des itinéraires entre les noeuds : liste_itineraires[i][j] c'est la liste de tous les noeuds qu'il faut emprunter pour aller de i vers j. 
        - la matrice des temps de trajet entre les noeuds. 
    """

    N_nodes = len(Noeuds)
    matrix_durations = np.zeros((N_nodes,N_nodes))
    liste_routes = []
    liste_itineraires = []
    liste_iti_points = []

    i = 0 
    for node_start in Noeuds : 
        liste_itineraires.append([])
        liste_iti_points.append([])
        start_x = Noeuds[node_start][1] 
        start_y = Noeuds[node_start][0]
        print('i = ', i)
        j = 0
        for node_end in Noeuds :
            end_x = Noeuds[node_end][1] 
            end_y = Noeuds[node_end][0]
            texte = requests.get("https://wxs.ign.fr/essentiels/geoportail/itineraire/rest/1.0.0/route?resource=bdtopo-osrm&start=" + str(start_x) + "," + str(start_y) + "&end=" + str(end_x) + "," + str(end_y) + "&timeUnit=second")
            texte = json.loads(texte.text)
            itineraire = texte['geometry']['coordinates']
            duration = texte['duration']
            matrix_durations[i,j] = duration 
            for element in itineraire: 
                if round(element[0]) == 2 : 
                    p = element[0]
                    element[0] = element[1]
                    element[1] = p 
            itineraire_points = toolbox.change(itineraire,  0.00025*(1/3), 0.0002*(1/3), 0.000225*(1/3))
            liste_iti_points.append([itineraire_points])

            #il va maintenant falloir modifier cela en une liste de noeud. 
            itineraire_noeuds = []
            node_courant = "-1"
            ending_point = itineraire_points[-1]
            min = 100000
            for point in itineraire_points:
                for node in Noeuds  : 
                    if node != node_courant and toolbox.dist(point, Noeuds[node]) <= 0.00020 : 
                        itineraire_noeuds.append(node)
                        node_courant = node

            ending_node = itineraire_noeuds[-1] #On crée cette lista pour éviter des situations du type : [6, 4, 0, 4, 0] pour aller de 6 en 0... 
            lista = []
            for node in itineraire_noeuds: 
                if node != ending_node: 
                    lista.append(node)
            lista.append(ending_node)

            liste_itineraires[i].append(lista)  #Donc liste_itineraires[i][j] c'est l'itineraire pour aller de i vers j en parlant en noeud. 
            j+=1
        i+=1 
    matrix_liste_iti_noeuds_cluster.append(liste_itineraires)
    matrix_durations_cluster.append(matrix_durations)




def construction_matrices_cluster(Noeuds_cluster):
    import time 

    start = time.perf_counter()
    manager = multiprocessing.Manager()
    matrix_durations_cluster = manager.list()
    matrix_liste_iti_noeuds_cluster = manager.list()
    processors = []

    for Noeuds in Noeuds_cluster: #on se place tour à tour dans chacun des sous-clusters.
        p = multiprocessing.Process(target = construction_matrices, args = [Noeuds, matrix_liste_iti_noeuds_cluster, matrix_durations_cluster])
        processors.append(p)
        p.start()

    k = 1
    for p in processors: 
        p.join()
        print('Nous en avons fini avec le calcul des matrices pour le cluster numéro', k)
        k +=1

    end = time.perf_counter()
    print('Nous avons mis', end-start, 'secondes à faire la parallélisation pour trouver calculer les matrices dans tous les sous-clusters')

    return matrix_liste_iti_noeuds_cluster, matrix_durations_cluster


# -----------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    
    with open ('Liste des dictionnaires des noeuds dans le cluster 2, découpé en sous-clusters', 'rb') as temp:
        Noeuds_cluster = pickle.load(temp) #Attention, ici : Noeuds_liste[0] c'est le dictionnaire des noeuds dans le premier cluster, origine comprise. C'est ce que l'on appelle "Noeuds". 
    
    matrix_liste_iti_noeuds_cluster, matrix_durations_cluster = construction_matrices_cluster(Noeuds_cluster)

    with open('Matrice des noeuds pour le cluster', 'wb') as temp:
        pickle.dump(matrix_liste_iti_noeuds_cluster, temp)

    # with open('Matrice des temps pour le cluster', 'wb') as temp:
    #     pickle.dump(matrix_durations_cluster, temp)


