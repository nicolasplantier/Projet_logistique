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
import pandas as pd 
import multiprocess
import multiprocessing
import pickle


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



def create_sub_cluster(cluster, N): 
    """
    Un cluster c'est la liste des coordonnées que nous venons de définir. 
    N c'est le nombre de carré que l'on voudra en largeur 

    Cette fonction renvoie un dictionnaire : une clé c'est un sous cluster, dont l'élément est la liste des coordonnées des points concernés ainsi que leur poids (comme dans le cluster initial finalement) 
    """
    for i in range(len(cluster)): 
        cluster[i] = [[cluster[i][0][1], cluster[i][0][0]], cluster[i][1]]
    liste_min_bandelette = []
    x_min = np.infty
    x_max = -np.infty
    y_min = np.infty
    y_max = -np.infty
    for k in range(len(cluster)):
        if cluster[k][0][0] < x_min :
            x_min = cluster[k][0][0]
        if cluster[k][0][0] > x_max :
            x_max = cluster[k][0][0]
        if cluster[k][0][1] < y_min :
            y_min = cluster[k][0][1]
        if cluster[k][0][1] > y_max :
            y_max = cluster[k][0][1]

    liste_l = [] #c'est la liste des largeurs des bandelettes. 
    for k in range(N): 
        liste_l.append((x_max-x_min)/N )

    cluster_courant = cluster.copy() #c'est le cluster courant : on va de gauche à droite pour construire tous nos cluster (bandelette après bandelette)
    
    #print([x_min, y_min], [x_max, y_max])

    carres_regroupes = []
    for k in range(N): #on est sur la k-ème bandelette 
        bandelette = [] #on stocke nos données sur chaque carré là dedans. 
        x_min_bandelette = x_min +k*liste_l[k] 
        x_max_bandelette = x_min +(k+1)*liste_l[k] 
        dist_min_basg = +np.infty
        dist_min_hautg = +np.infty
        dist_min_basd = +np.infty
        dist_min_hautd = +np.infty
        point_bas_gauche = cluster_courant[0]
        point_haut_gauche = cluster_courant[1]
        for point in cluster_courant:
            if distanceGPS(point[0], [x_min,y_min]) < dist_min_basg: 
                dist_min_basg = distanceGPS(point[0], [x_min,y_min])
                point_bas_gauche = point #Attention, on a la donnée pds_rec avec 
            if distanceGPS(point[0], [x_min,y_max]) < dist_min_hautg: 
                dist_min_hautg = distanceGPS(point[0], [x_min,y_max])
                point_haut_gauche = point #Attention, on a la donnée pds_rec avec 
        y_min_courant = point_bas_gauche[0][1]
        y_max_courant = point_haut_gauche[0][1]
        L = y_max_courant-y_min_courant
        l = liste_l[k]

        l_distance = distanceGPS([48.782633, 2.310045], [48.782633, 2.310045+l])
        L_distance = distanceGPS([48.782633, 2.310045], [ 48.782633+L, 2.310045])
        #print(l_distance, L_distance/N, 1)

        n = 1

        while L_distance/n > l_distance:
            n+=1 
        if n != 1: 
            if abs(L_distance/(n-1)-l_distance) < abs(L_distance/n-l_distance):
                n = n-1
        #on a désormais des carrés de taille (l x L)
        #print(l_distance, L_distance/n, 2)
        for i in range(n): 
            car = []
            if i == 0:
                carre = [[x_min_bandelette, y_max_courant-i*(L/n)], [x_min_bandelette+ l, y_max]]
            elif i == n-1:
                carre = [[x_min_bandelette, y_max_courant-i*(L/n)], [x_min_bandelette+l, y_min]]
            else : 
                carre = [[x_min_bandelette, y_max_courant-i*(L/n)],[x_min_bandelette+l, y_max_courant-(i-1)*(L/n)]]
            
            #on a désormais notre petit carré courant. 
            x_min_carre, y_min_carre = carre[0]
            x_max_carre, y_max_carre = carre[1]

            cluster_courant_courant = cluster_courant
            for point in cluster_courant:
                coor_point = point[0]
                if coor_point[0] > x_min_carre and coor_point[0] < x_max_carre and coor_point[1] > y_min_carre and coor_point[1] < y_max_carre:
                    car.append(point)
                    cluster_courant_courant.pop(cluster_courant_courant.index(point))
            cluster_courant = cluster_courant_courant
            for i in range(len(car)): 
                car[i] = [[car[i][0][1], car[i][0][0]], car[i][1]]
            bandelette.append(car)
        carres_regroupes.append(bandelette)
    return(carres_regroupes)
            


def find_nodes_modified(coordinates, N, d): 
    """
    C'est la fonction que l'on va utiliser pour trouver toutes les noeuds dans un espace donné. 
    N c'est le nombre d'itinéraires que l'on va faire pour trouver tous ces noeuds. 

    """ 
    x_min = coordinates[0][0]
    x_max = coordinates[1][0]
    y_min = coordinates[0][1]
    y_max = coordinates[1][1]
    Delta_x = x_max-x_min
    Delta_y = y_max-y_min

    nodes = {}

    T = [] # C'est la liste des temps qui pour le moment est vide : dès que l'on trouve un nouveau point, on ajoute un temps
    Y = [] # C'est la liste du nombre de points trouvés : dès que l'on en trouve un, on ajoute un élément. 

    T_init = time()
    courant = 1 #C'est l'indice courant du noeud que l'on ajoute. ATTENTION, POUR LES SOUS-CLUSTER, ON MET BIEN 1. LE 0 C'EST LE NOEUD ORIGINAL
    for k in range(N): 
        start_x = x_min + Delta_x*rd.random()
        start_y = y_min + Delta_x*rd.random()
        end_x = x_min + Delta_x*rd.random()
        end_y = y_min + Delta_x*rd.random()
        texte = requests.get("https://wxs.ign.fr/essentiels/geoportail/itineraire/rest/1.0.0/route?resource=bdtopo-osrm&start=" + str(start_y) + "," + str(start_x) + "&end=" + str(end_y) + "," + str(end_x) + "&timeUnit=second")
        texte = json.loads(texte.text)
        itineraire = texte['geometry']['coordinates']
        for el in itineraire:
            i=el[0]
            el[0]=el[1]
            el[1]=i
        itineraire = change(itineraire, 0.000125/3, 0.00005*(2/3), 0.0001125/3)
        routes = route_dect(itineraire)
        noeuds_courant = []
        noeuds_potentiel = []
        if len(routes) !=1 and len(routes)!=2 : #S'il n'y a qu'une seule route il n'y a pas de noeuds qui nous intéressent
            for route in routes[1:len(routes)-1] : 
                #if distanceGPS(route[0], route[1]) >= 70: 
                noeuds_courant.append(route[0])
            for noeud in noeuds_courant : 
                if len(nodes) !=0 :
                    d_min = 1000
                    for node in nodes : 
                        if distanceGPS(nodes[node], noeud) <= d_min: 
                            d_min = distanceGPS(nodes[node], noeud)
                    if d_min >= d: 
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
        #print(nodes)
    return nodes
    

def find_nodes_scluster(sub_cluster, origin, N_iti, nodes_sub_clusters, k):
    # cette fonction calcule tous les noeuds dans un sub_cluster, le k-ième plus précisement. 
    x_min = np.infty
    y_min = np.infty 
    x_max = -np.infty 
    y_max = -np.infty

    for point in sub_cluster:
        x = point[0][0]
        y = point[0][1]
        if x<x_min : 
            x_min = x
        if x > x_max: 
            x_max = x
        if y < y_min :
            y_min = y
        if y > y_max : 
            y_max = y
    x_min_inf, y_min_inf = x_min - 0.003, y_min - 0.003
    x_max_sup, y_max_sup = x_max + 0.003, y_max + 0.003
    nodes_sub_cluster = find_nodes_modified(coordinates= [[x_min_inf,y_min_inf],[x_max_sup, y_max_sup]], N = N_iti, d = 20)
    # Il faut savoir que à cette étape on a trop de noeuds : on a été obligé d'élargir notre sub_cluster pour être sûr de bien trouver tous les noeuds. On peut maintenant le réduire à nouveau. 
    wrong_nodes = [] 
    for nodes in nodes_sub_cluster: 
        x,y = nodes_sub_cluster[nodes]
        if x < x_min or x > x_max or y < y_min or y >y_max:
            wrong_nodes.append(nodes)
    right_nodes = {}
    courant = 1
    for nodes in nodes_sub_cluster: 
        if nodes not in wrong_nodes: 
            right_nodes[str(courant)] = nodes_sub_cluster[nodes]
            courant += 1 
    right_nodes['0'] = origin 
    nodes_sub_clusters[k] = right_nodes




def find_all_nodes(subclusters, origin, N_iti): 
    """
    Cette fonction trouve tous les noeuds en utilisant la parallélisation dans un grand cluster
    en le faisant dans chacun des sous-cluster individuel en parallèle. 
    """
    import time
    start = time.perf_counter()
    manager = multiprocessing.Manager()
    nodes_sub_clusters = manager.dict()
    k = 0
    processors = []
    for i in range(len(subclusters)): #C'est le numéro de la bandelette 
        for j in range(len(subclusters[i])): #C'est le subcluster à la j-ième position dans cette bandelette 
            p = multiprocessing.Process(target = find_nodes_scluster, args=[subclusters[i][j], origin, N_iti, nodes_sub_clusters, k])
            processors.append(p)
            p.start() #On démarre tous les processeurs au fur et à mesure
            k+=1 
    k = 1
    for p in processors: 
        p.join() #en faisant cela, on est en train de modifier nodes_sub_clusters
        print('nous en avons fini avec le cluster', k)
        k+=1
    end = time.perf_counter()
    print('Nous avons mis', end-start, 'secondes à faire la parallélisation pour trouver les noeuds')
    return nodes_sub_clusters.values()




############## Partie executable 

if __name__ == "__main__":
    print('Nous lisons le fichier')
    df = pd.read_csv("/Users/nicolasplantier/Documents/Mines Paris/UE 22 - Ingénieurie logicielle/Input 2/output_df_test.csv")  
    mask = df['cluster'] == 2 #C'est le 5ème arrondissement et même beaucoup plus large 
    df = df[mask]
    cluster = []
    for k in range(len(df)): 
        texte = df.iloc[k]['geometry']
        a = ''
        b = ''
        i = 0 
        while texte[i] != '2': 
            i +=1
        while texte[i] != ' ': 
            a += texte[i]
            i += 1
        i += 1
        while texte[i] != ')':
            b += texte[i]
            i += 1
        coor = [[eval(b), eval(a)], df.iloc[k]['pds_rec']]
        cluster.append(coor)

    print('Nous commençons à découper en sous clusters')
    subclusters = create_sub_cluster(cluster, 5)

    print('Nous allons chercher les noeuds avec de la parallélisation maintenant')
    origin = [48.845553847446546, 2.3398328515404336]
    nodes_sub_clusters = find_all_nodes(subclusters, origin, 7)
    
    with open('Liste des dictionnaires des noeuds dans le cluster 2, découpé en sous-clusters', 'wb') as temp:
        pickle.dump(nodes_sub_clusters, temp)
