# Projet_logistique

**NB** : Notre projet utilise de nombreux API gratuits très utilisés. Nous vous recommendons d'exécuter les différents scipts en dehors de heures de pointes : préférentiellement entre 11h et 14h et après 19h. Le week-end, les API repondent rapidement peu importe l'heure.  

Bienvenue dans notre projet de logistique. Les documents compris dans ces dossiers vont vous permettre d'afficher les cartes de flux dans la zone que vous désirée. 

Dans un premier temps, vous devrez télécharger l'environnement : **environnement.yml** nécessaire à la bonne exécution des scripts python. Pour cela, il vous suffira d'ouvrir un terminal dans le dossier où vous aurez clone ce repository et d'exécuter les commandes suivantes : 

1)  conda env create -f environment.yml -n projet_logistique
2)  conda activate projet_logistique 

Nous avons choisi le cas du quartier latin pour tracer les cartes de flux, mais libre à vous de décider de tracer les cartes de flux pour n'importe laquelle des zones de Paris. Nous avons laissé ici uniquement les scripts python nécessaires pour la réalisation des cartes de flux. 

Voici l'ordre dans lequelle exécuter les scipts python : 
1) Dans un premier temps, vous pourrez exécuter le script python qui vous permettra de trouver tous les noeuds de la zone considérée. Ce premier script est **quartier_latin_find_all_nodes_write_file_final.py**. Vous pourrez modifier les coordonnées de la zone considérée (variable quartier_latin) qui correspondent aux coordonnées des extremités inférieure gauche et supérieure droite de la zone considérée. N'oubliez pas de modifier "my_path" pour enregistrer correctement les données que vous venez de trouver dans le fichier où vous avez clone ce repo. 
2) Vous pourrez ensuite exécuter la fonction **quartier_latin_find_all_nodes_read_file_final.py**. Elle va notamment créer le html sur lequel vous pourrez observer tous les noeuds que vous venez de trouver. De même modifier my_path pour que ce dossier soit enregistré là où vous le souhaitez. Vous pourrez aussi consulter un exemple dans le dossier de base enregistré sous le nom : **affichage_noeuds_folium_test.html**
3) Une fois que nous avons tous les noeuds, il faut calculer les temps de trajet (tel que matrix_durations[i][j] = 134 : on met 134 secondes pour aller du noeud i au noeud j) entre ces noeuds et les itinéraires entre ces noeuds (tel que liste_itineraires[i][j] = ["i", "3", "4", "j"] par exemple : pour aller du noeud i au noeud j on passe par les noeuds 3 et 4). Vous pourrez pour cela exécuter le sript **quartier_latin_write_matrix_with_multiprocessing_final.py**. On utilise ici du multiprocessing pour être plus efficace en temps de calculs.
4) Vous pourrez ensuite exécuter le script **quartier_latin_read_matrix_with_multiprocessing_final.py** pour accéder aux données que vous venez de calculer. 
5) Enfin, vous pourrez créer des cartes de flux à partir de toutes les données que vous venez de calculer, et les données de demandes en marchandises des bâtiments enregistrés dans le dossier output, grâce à la fonction **quartier_latin_create_heatmap_final.py**. N'oubliez pas de changer les informations de localisation du dossier en modifiant : "mypath". 
6) Vous pouvez maintenant lire les cartes de flux du dossier : **quartier_latin_map_trafic_.html**. Si jamais vous n'avez pas le temps d'exécuter les scripts, vous pourrez observer un test de carte de flux dans le document : **quartier_latin_map_trafic_test.hmtl**. 


Nous espérons que vous apprécierez notre travail et remercions une fois encore Émilienne Lardy du CGS des Mines pour son aide et ses conseils au cours de ce projet d'informatique. 

Nicolas Plantier, Marion Stenta, Blandine Geisler et Augustin Le Corre. 


