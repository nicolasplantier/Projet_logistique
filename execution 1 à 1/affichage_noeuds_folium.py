import folium 
import pickle 
import random as rd 
from folium.features import DivIcon


with open ('Liste des dictionnaires des noeuds dans le cluster 2, découpé en sous-clusters', 'rb') as temp:
    Noeuds_cluster = pickle.load(temp) #Attention, ici : Noeuds_liste[0] c'est le dictionnaire des noeuds dans le premier cluster, origine comprise. C'est ce que l'on appelle "Noeuds". 


m = folium.Map(location =[48.845553847446546, 2.3398328515404336], zoom_start= 14)

k = 1 
for sub_clusters in Noeuds_cluster: 
    if k != 3 : 
        color = '#%02x%02x%02x' % (int(rd.randint(1,255)), int(rd.randint(1,255)), int(rd.randint(1,255)))
    else : 
        color = '#%02x%02x%02x' % (0,0,0)
    for noeud in sub_clusters:
        folium.Circle(location = sub_clusters[noeud], radius = 10, color = color).add_to(m)
        folium.map.Marker(sub_clusters[noeud],
        icon=DivIcon(
            icon_size=(250,36),
            icon_anchor=(0,0),
            html='<div style="font-size: 10">'+ noeud+ '</div>'
            )
        ).add_to(m)
    if k == 3: #C'est le quartier où l'on va faire des tests, il faut donc qu'il soit reconnaissable
        folium.Marker(location = sub_clusters['1']).add_to(m)
    k +=1 

m.save('/Users/nicolasplantier/Documents/Mines Paris/UE 22 - Ingénieurie logicielle/Projet_logistique/execution 1 à 1/affichage_noeuds_folium.html')