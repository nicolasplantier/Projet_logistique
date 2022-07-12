# Il faut modifier my path par la localisation du dossier où vous avez clone le repo git. 

df = pd.read_csv("mypath/output_df_test.csv")  


# ----------------------------------------------------------------------------------------------------

import multiprocessing
from tkinter import N
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
import pandas as pd  
import os 

"""
Quelques variables globales 
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
On charge dans un premier temps quelques données qui seront des variables globales 
"""    

print('Nous lisons les données déjà calculées')

# On a d'abord les Noeuds 
with open('Noeuds dans le quartier latin', 'r') as opfile: 
    Noeuds = eval(opfile.read())

# On a aussi la liste des itineraires 
with open('Matrice des itineraires entres les noeuds', 'r') as opfile : 
    liste_iti_noeuds = eval(opfile.read()) 

# On la matrice des durées 
liste_durations = np.loadtxt('Matrice des temps de trajet entre les noeuds')

N_nodes = len(Noeuds)
matrix_durations = np.zeros((N_nodes, N_nodes))
for i in range(N_nodes):
    for j in range(N_nodes): 
        matrix_durations[i,j] = liste_durations[i][j]

mask = df['cluster'] == 2 #C'est le 5ème arrondissement et même beaucoup plus large (une partie du 6ème, du 13ème et du 14ème)
df = df[mask]
liste_coor_temp = []
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
    coor = [eval(a), eval(b)]
    liste_coor_temp.append(coor)

liste_coor = []
    
x_min, y_min = np.infty, np.infty
x_max, y_max = -np.infty, -np.infty 
for node in Noeuds : 
    noeud = Noeuds[node]
    if noeud[0] < x_min: 
        x_min = noeud[0]
    if noeud[1] < y_min: 
        y_min = noeud[1]
    if noeud[0] > x_max: 
        x_max = noeud[0]
    if noeud[1] > y_max: 
        y_max = noeud[1]

# On se restreint maintenant aux coordonnées qui sont dans la zone qui nous interesse : celle où l'on a trouvé des noeuds. 
for coor in liste_coor_temp: 
    if coor[1] < x_max and coor[1] > x_min and coor[0] > y_min and coor[0] < y_max:
        liste_coor.append(coor)

for k in range(len(liste_coor)): 
    liste_coor[k] = [liste_coor[k][1], liste_coor[k][0]]

print('Nous avons fini de lire les données déjà calculées')

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


"""
On définit maintenant toutes les fonctions et les classes dont nous allons avoir besoin. 
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
    S = 2*np.sqrt(np.sin((latB-latA)/2)**2+np.cos(latA)*np.cos(latB)*np.sin((longB-longA)/2)**2)
    # S = np.arccos(np.sin(latA)*np.sin(latB) + np.cos(latA)*np.cos(latB)*np.cos(abs(longB-longA)))
    # distance entre les 2 points, comptée sur un arc de grand cercle
    return S*RT


def quel_noeud_coor(coor, ville, nodes): 
    d_min = 1000000
    for node in nodes : 
        if distanceGPS(nodes[node], coor) <= d_min :
            mon_noeud = node 
            d_min = distanceGPS(nodes[node], coor)
    distanceGPS(nodes[node], coor)
    return mon_noeud 


def vrpy_trouver_tournée_coor(liste_coor, nodes, time_limit):
    
    """
    Nodes c'est notre liste de noeuds que l'on aura donc bien prédéfinie. La première étape va consister à atribuer à toutes les adresses le noeud leur correspondant. 
    adresses_et_demandes c'est un dictionnaire : chacune des clés est pour une adresse. pour chaque adresse on a donc une liste d'un élément : un dictionnaire 
    où l'on va retrouver toutes les infos necssaires pour l'adresse en question. 

    Capacité, c'est le nombre de camion que l'on a à notre disposition pour effectuer les tournées dans le quartier. 

    """

    noeuds_et_demandes = {}
    for coor in liste_coor: 
        noeud = quel_noeud_coor(coor, "Paris", nodes)
        if noeud != '0':
            if noeud not in noeuds_et_demandes: 
                noeuds_et_demandes[noeud] = [{'demande' : rd.random()}]
            else : 
                noeuds_et_demandes[noeud][0]['demande'] += rd.random()
    
    """
    On a désormais converti notre dictionnaire des demandes des adresses en un dictionnaire de demandes reportée sur les noeuds. 
    Il faut désormais établir les tournées. On va vouloir renvoyer à la suite (même si plusieurs tournées sont effectuées en parallèle) la grande liste 
    qui contient tous les noeuds que l'on va visiter dans l'odre (c'est la concaténation de toutes les tournées)
    """
    print('On commence vrpy')
    G = DiGraph()
    for noeud in noeuds_et_demandes : # ici on crée les edges entre les noeuds et le début / la fin qui est au noeud 0. 
        G.add_edge('Source', noeud, cost = matrix_durations[0,eval(noeud)-1])
        G.add_edge(noeud, 'Sink', cost = matrix_durations[eval(noeud)-1,0])
        G.nodes[noeud]["demand"] = noeuds_et_demandes[noeud][0]['demande']
    for start in noeuds_et_demandes: 
        for ending in noeuds_et_demandes:
            G.add_edge(start, ending, cost = matrix_durations[eval(start)-1,eval(ending)-1])
    prob = VehicleRoutingProblem(G, load_capacity=2500)
    prob.solve(heuristic_only=True, time_limit= time_limit)
    itineraire = prob.best_routes
    return itineraire


class Route : 
    def __init__(self, depart, arrivee):
        self.depart = depart
        self.arrivee = arrivee
        self.traffic = 1
        self.color = (0,0,0) #On initialise la couleur d'une route en disant qu'elle est noire au départ 
        self.road_type = 'rue' #Au début, pas d'apriori, tout le monde est une rue 
        

    def draw(self, map, liste_routes): 
        point_0 = [Noeuds[self.depart][0], Noeuds[self.depart][1]]
        point_1 = [Noeuds[self.arrivee][0],  Noeuds[self.arrivee][1]]
        latlngs = [point_0, point_1]
        if self.road_type == 'rue':
            max_rue = 0 
            for i in range(len(liste_routes)): 
                for j in range(len(liste_routes)): 
                    if liste_routes[i][j] !=0:
                        if liste_routes[i][j].road_type == 'rue' and liste_routes[i][j].traffic > max_rue : 
                            max_rue = liste_routes[i][j].traffic
            self.traffic = self.traffic/max_rue 
        elif self.road_type == 'avenue': 
            max_avenue = 0 
            for i in range(len(liste_routes)): 
                for j in range(len(liste_routes)): 
                    if liste_routes[i][j] !=0:
                        if liste_routes[i][j].road_type == 'avenue' and liste_routes[i][j].traffic > max_avenue :
                            max_avenue = liste_routes[i][j].traffic
            self.traffic = self.traffic/max_avenue 
        elif self.road_type == 'grand axe': 
            max_grand_axe = 0 
            for i in range(len(liste_routes)): 
                for j in range(len(liste_routes)): 
                    if liste_routes[i][j] !=0:
                        if liste_routes[i][j].road_type == 'grand axe' and liste_routes[i][j].traffic > max_grand_axe :
                            max_grand_axe = liste_routes[i][j].traffic
            self.traffic = self.traffic/max_grand_axe 
        if self.traffic <= 0.5 : 
            color = '#%02x%02x%02x' % (round(2*self.traffic*255), 255,0) 
            folium.PolyLine(latlngs, color = color, weight = 9).add_to(map)
        else : 
            color = '#%02x%02x%02x' % (255, 255 - round(self.traffic*255), 0)
            folium.PolyLine(latlngs, color = color, weight = 9).add_to(map)
        
    

    def other_draw(self, map): 
        point_0 = Noeuds[self.depart]
        point_1 = Noeuds[self.arrivee]
        latlngs = [point_0, point_1]
        if self.road_type == 'rue': 
            color = '#%02x%02x%02x' % (10,10,10) #cette color c'est celle que prendra la case au moment de l'affichage, mais ce n'est pas la couleur de la rue est restée la même.  
            folium.PolyLine(latlngs, color = color, weight = 6).add_to(map)
        elif self.road_type == 'avenue': 
            color = '#%02x%02x%02x' % (130,130,130)
            folium.PolyLine(latlngs, color = color, weight = 9).add_to(map)
        elif self.road_type == 'grand axe':
            color = '#%02x%02x%02x' % (200,200,200)
            folium.PolyLine(latlngs, color = color, weight = 12).add_to(map)
        else :
            color = '#FF0000'
            folium.PolyLine(latlngs, color = color, weight = 10).add_to(map)

        
# ------------------------------------------------------------------------------------------------------------

class image_du_quartier:
    def __init__(self):
        self.zoom = 15
        self.ecart_axes = 0.006
        self.localisation = Noeuds['0']
        self.pix_x_dist, self.pix_y_dist, self.image  = test_echelle(self.zoom, self.localisation, self.ecart_axes)


# ------------------------------------------------------------------------------------------------------------

class quartier : 
    """
    C'est la classe qui définit notre grand quartier.
    Un de ses attributs est justement toutes les routes qui le constitue : on aura crée cette liste au préalable après avoir trouvé les noeuds
    """
    def __init__(self, itineraire):  
        liste_routes = create_liste_route(itineraire)
        self.liste_routes = liste_routes 
        self.image_du_quartier = image_du_quartier()

    def draw(self): 
        map = folium.Map(location=Noeuds['0'],zoom_start= 15) #nodes['0'] c'est les mines de paris 
        for i in range(len(self.liste_routes)): 
            for j in range(len(self.liste_routes)):
                element = self.liste_routes[i][j]
                if element != 0 :
                    route = element #On dit que juste que cet élément est donc en fait bien une route 
                    element.other_draw(map)
        return map 

    def draw_traffic(self): 
        map = folium.Map(location=Noeuds['0'],zoom_start= 15) #nodes['0'] c'est les mines de paris 
        for i in range(len(self.liste_routes)): 
            for j in range(len(self.liste_routes)):
                element = self.liste_routes[i][j]
                if element != 0 :
                    element.draw(map, self.liste_routes)
        return map 
    
    def change_couleur_routes(self):
        im_quart = self.image_du_quartier
        image = im_quart.image
        location = im_quart.localisation
        pix_x_dist = im_quart.pix_x_dist
        pix_y_dist = im_quart.pix_y_dist
        for i in range(len(self.liste_routes)):
            for j in range(len(self.liste_routes)):
                if self.liste_routes[i][j] != 0:
                    self.liste_routes[i][j].color = (0,0,0)
                    N_it = 0
                    while dist_color(self.liste_routes[i][j].color,rgb_blanc) >= 8 and dist_color(self.liste_routes[i][j].color,rgb_jaune) >= 8 and dist_color(self.liste_routes[i][j].color,rgb_orange) >= 8 and dist_color(self.liste_routes[i][j].color,rgb_gris) >= 8 and N_it < 200 :
                        route = self.liste_routes[i][j]
                        x = Noeuds[route.depart]
                        y = Noeuds[route.arrivee]
                        k = rd.random()
                        if k <= 0.90 and k > 0.1 : #Il faut que l'on se place au moins à 10% de la route, et pas à plus de 90% (sinon on est au niveau des noeuds où l'on n'a pas forcément le type de la route que l'on cherche mais celui de celle qui lui est perpendiculaire)
                            point = [k*x[0] + (1-k)*y[0], k*x[1] + (1-k)*y[1]] #C'est un point pris au hasard sur le segment formé par les deux noeuds
                            coor = equivalence_coorGPS_coorimage(image, location, pix_x_dist, pix_y_dist, point)
                            color = quel_couleur(image, coor)
                            self.liste_routes[i][j].color = color #La couleur de la route est bien la couleur EXACTE de la route (et pas un approximation)
                            N_it += 1
                    print(k, N_it)
                    if N_it == 200 : #Si la raison pour laquelle nous sommes sortis de la boucle est que nous avons dépassé le nombre d'itérations acceptable
                        print("Nous n'avons pas réussi à trouver le type de la route reliant le noeud ", i, " et le noeud ", j)
                        #self.liste_routes[i][j].color = rgb_orange #Si jamais nous n'avons pas trouvé le type de la rue : on dit que c'est un grand axe (pour éviter une mauvaise normalisation d'un axe plus important)
                        road_type = 'grand axe'

                    if dist_color(self.liste_routes[i][j].color,rgb_blanc)<=8 or dist_color(self.liste_routes[i][j].color,(0,0,0))<=8 or dist_color(self.liste_routes[i][j].color,rgb_gris)<=8: 
                        road_type = 'rue'
                    elif dist_color(self.liste_routes[i][j].color,rgb_jaune)<=8:
                        road_type = 'avenue'
                    elif dist_color(self.liste_routes[i][j].color,rgb_orange)<=8: 
                        road_type = 'grand axe'
                    self.liste_routes[i][j].road_type = road_type

# ------------------------------------------------------------------------------------------------------------
#La fonction ci-dessous servait autrefois, quand on crééait les classes routes au préalable
"""
def create_matrice_routes(itineraire, nodes):
    matrice_routes = [[0 for i in range(len(nodes))] for j in range(len(nodes))]
    for iti in itineraire :
        liste_noeuds = itineraire[iti]
        for i in range (len(liste_noeuds) - 1) :
            if liste_noeuds[i] == "Source" :
                chemin = liste_iti_noeuds[0][eval(liste_noeuds[i+1])]
            elif liste_noeuds[i+1] == "Sink":
                chemin = liste_iti_noeuds[eval(liste_noeuds[i])][0]
            else : 
                chemin = liste_iti_noeuds[eval(liste_noeuds[i])][eval(liste_noeuds[i+1])]
            for j in range(len(chemin)-1): 
                if matrice_routes[eval(chemin[j])][eval(chemin[j+1])] == 0 :
                    matrice_routes[eval(chemin[j])][eval(chemin[j+1])] = Route(chemin[j], chemin[j+1])
                else : 
                    matrice_routes[eval(chemin[j])][eval(chemin[j+1])].traffic += 1
    return matrice_routes
"""

# ------------------------------------------------------------------------------------------------------------

def create_liste_route(itineraire): 
    i = 0 
    liste_routes = []
    for i in range(len(Noeuds)): 
        liste_routes.append([])
        for j in range(len(Noeuds)): 
            liste_routes[i].append(0)
    for iti in itineraire: 
        print("Nous sommes au trajet numéro ", iti)
        way = itineraire[(iti)]
        for l in range(len(way)-1): 
            if way[l] == 'Source':
                noeud = way[l+1]
                chemin = liste_iti_noeuds[0][eval(noeud)]
                for k in range(len(chemin)-1):
                    a = eval(chemin[k])
                    b = eval(chemin[k+1])
                    if liste_routes[a][b]==0 and liste_routes[b][a]==0: #Si jamais la route n'est pas encore construite: 
                        if a >= b :  #On veut une matrice trigonale supérieure 
                            liste_routes[b][a] = Route(chemin[k], chemin[k+1])
                        else : 
                            liste_routes[a][b] = Route(chemin[k], chemin[k+1])
                    else : 
                        if a >= b : 
                            liste_routes[b][a].traffic += 1
                        else : 
                            liste_routes[a][b].traffic += 1
            elif way[l+1] == 'Sink':
                chemin = liste_iti_noeuds[eval(way[l])][0]
                for k in range(len(chemin)-1):
                    a = eval(chemin[k])
                    b = eval(chemin[k+1])
                    if liste_routes[a][b]==0 and liste_routes[b][a]==0: #Si jamais la route n'est pas encore construite: 
                        if a >= b :  #On veut une matrice trigonale supérieure 
                            liste_routes[b][a] = Route(chemin[k], chemin[k+1])
                        else : 
                            liste_routes[a][b] = Route(chemin[k], chemin[k+1])
                    else : 
                        if a >= b : 
                            liste_routes[b][a].traffic += 1
                        else : 
                            liste_routes[a][b].traffic += 1
            else :
                chemin = liste_iti_noeuds[eval(way[l])][eval(way[l+1])]
                for k in range(len(chemin)-1):
                    a = eval(chemin[k])
                    b = eval(chemin[k+1])
                    if liste_routes[a][b]==0 and liste_routes[b][a]==0: #Si jamais la route n'est pas encore construite: 
                        if a >= b :  #On veut une matrice trigonale supérieure 
                            liste_routes[b][a] = Route(chemin[k], chemin[k+1])
                        else : 
                            liste_routes[a][b] = Route(chemin[k], chemin[k+1])
                    else : 
                        if a >= b : 
                            liste_routes[b][a].traffic += 1
                        else : 
                            liste_routes[a][b].traffic += 1
    return liste_routes

# ------------------------------------------------------------------------------------------------------------

def center(a,b): 
    return [(a[0]+b[0])/2, (a[1]+b[1])/2]

# ------------------------------------------------------------------------------------------------------------

def dist_color(color1, color2): 
    """
    Cette fonction sert à donner la distance entre deux couleurs.
    """
    return np.sqrt((color2[0]-color1[0])**2+(color2[1]-color1[1])**2+(color2[2]-color1[2])**2)

# ------------------------------------------------------------------------------------------------------------

def test_echelle(zoom, location, ecart_axes):
    """
    Cette fonction prend un zoom dans folium et renvoie l'échelle correspondante (attention, on doit adapter la ligne de référence pour qu'elle apparaisse bien dans 
    l'image et séparée du point original)

    Des tests ont été effectué : cette fonction fonctionne correctement. 
    """
    import time
    bas_gauche = [location[0]-0.01, location[1]-ecart_axes]
    haut_gauche_1 = [location[0]+0.01, location[1]-ecart_axes]
    haut_droite = [location[0]+ecart_axes, location[1]+0.01]
    haut_gauche_2 = [location[0]+ecart_axes, location[1]-0.01]

    m = folium.Map(location = location,zoom_start=zoom)
    folium.PolyLine([bas_gauche, haut_gauche_1], color = '#%02x%02x%02x' % (0, 0, 0)).add_to(m)
    folium.PolyLine([haut_gauche_2, haut_droite], color = '#%02x%02x%02x' % (0, 0, 0)).add_to(m)

    mapName = 'test_18h39.html'
    m.save(mapName)
    mapUrl = 'file://{0}/{1}'.format(os.getcwd(), mapName)
    options = webdriver.ChromeOptions()
    #options.add_argument("--start-maximized")
    #options.add_argument('--log-level=3')
    driver = webdriver.Chrome(executable_path="chromedriver",chrome_options=options)
    #driver.set_window_size(1920,1080)

    # wait for 5 seconds for the maps and other assets to be loaded in the browser
    driver.get(mapUrl)
    time.sleep(3)
    driver.save_screenshot('test_18h44.png')
    driver.close()
    print("La capture d'écran a bien été enregistré")

    im = plt.imread('test_18h44.png')
    N_pixel_x = im.shape[0]
    N_pixel_y = im.shape[1]
    pixel_x_courant = N_pixel_x//2
    pixel_y_courant = N_pixel_y//2
    couleur = (int(list(im[pixel_x_courant][pixel_y_courant]*255)[0]), int(list(im[pixel_x_courant][pixel_y_courant]*255)[1]), int(list(im[pixel_x_courant][pixel_y_courant]*255)[2]))
    while couleur != (0,0,0): 
        pixel_x_courant = pixel_x_courant
        pixel_y_courant -= 1
        couleur = (int(list(im[pixel_x_courant][pixel_y_courant]*255)[0]), int(list(im[pixel_x_courant][pixel_y_courant]*255)[1]), int(list(im[pixel_x_courant][pixel_y_courant]*255)[2]))
    delta_y_pixel = N_pixel_y//2 - pixel_y_courant
    distance = dist(location, [location[0], bas_gauche[1]])

    pixel_x_courant = N_pixel_x//2
    pixel_y_courant = N_pixel_y//2
    couleur = (int(list(im[pixel_x_courant][pixel_y_courant]*255)[0]), int(list(im[pixel_x_courant][pixel_y_courant]*255)[1]), int(list(im[pixel_x_courant][pixel_y_courant]*255)[2]))
    while couleur != (0,0,0): 
        pixel_y_courant = pixel_y_courant
        pixel_x_courant -= 1
        couleur = (int(list(im[pixel_x_courant][pixel_y_courant]*255)[0]), int(list(im[pixel_x_courant][pixel_y_courant]*255)[1]), int(list(im[pixel_x_courant][pixel_y_courant]*255)[2]))
    delta_x_pixel = N_pixel_x//2 - pixel_x_courant
    distance = dist(location, [haut_gauche_2[0], location[1]])

    return(distance/delta_x_pixel, distance/delta_y_pixel, im)

# ------------------------------------------------------------------------------------------------------------

def equivalence_coorGPS_coorimage(image, location, pix_x_dist, pix_y_dist, point):
    """
    Prend les coordonnées d'un point (point = [x,y]) et renvoie ses coordonnée sur l'image sous la forme d'une liste [i,j].
    On a accès à location au centre de la carte pour avoir une référence. 

    Des tests ont été effectué : cette fonction fonctionne correctement. 
    """
    N_pixel_x = image.shape[0]
    N_pixel_y = image.shape[1]
    point_origine = [location[0]-(N_pixel_x//2)*pix_x_dist, location[1]-(N_pixel_y//2)*pix_y_dist] #C'est le point de coordonnées sur l'image [0,0]
    distance_en_x = dist(point_origine, [point[0], point_origine[1]])
    distance_en_y = dist(point_origine, [point_origine[0], point[1]])
    return [round(distance_en_x*(1/pix_x_dist)), round(distance_en_y*(1/pix_y_dist))]

def quel_couleur(image, coor): 
    coor = image.shape[0]-coor[0], coor[1]
    temp_color = image[coor[0]][coor[1]]
    return int(temp_color[0]*255), int(temp_color[1]*255), int(temp_color[2]*255)









# ------------------------------------------------------------------------------------------------------------------------------------------------------

itineraire = vrpy_trouver_tournée_coor(liste_coor, Noeuds, time_limit=300)
mon_quartier = quartier(itineraire)
m = mon_quartier.draw_traffic()
folium.Marker(location = Noeuds['0']).add_to(m)

# Il faut modifier mypath par la localisation du dossier où vous avez clone le repo git. 
m.save('mypath/quartier_latin_map_trafic.html')

