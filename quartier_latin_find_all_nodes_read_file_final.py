import folium
from folium.features import DivIcon

with open('Noeuds dans le quartier latin', 'r') as opfile: 
    Noeuds = eval(opfile.read())

m = folium.Map(location = Noeuds['0'], zoom_start=15)
for noeud in Noeuds: 
    if noeud == '0': 
        folium.Circle(location = Noeuds[noeud], radius = 10, color = 'green').add_to(m)
        folium.Circle(location = Noeuds[noeud], radius = 5, color = 'green').add_to(m)
        folium.Circle(location = Noeuds[noeud], radius = 2, color = 'green').add_to(m)
    else :
        folium.Circle(location = Noeuds[noeud], radius = 5, color = 'red').add_to(m)
        folium.Circle(location = Noeuds[noeud], radius = 2, color = 'red').add_to(m)
    # folium.map.Marker(Noeuds[noeud], icon=DivIcon(icon_size=(250,36), icon_anchor=(0,0), html='<div style="font-size: 10pt">' + noeud + '</div>')).add_to(m)



# il faut modifier mypath par la localisation du ficher que vous avez clone
m.save('mypath/affichage_noeuds_folium.html')