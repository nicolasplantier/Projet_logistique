# Projet_logistique

Bienvenue dans notre projet de logistique. Les documents compris dans ces dossiers vont vous permettre d'afficher les cartes de flux dans la zone que vous désirée. 

Dans un premier temps, vous devrez télécharger l'environnement : **environnement.yml** nécessaire à la bonne exécution des scripts python. Pour cela, il vous suffira d'ouvrir un terminal dans le dossier où vous aurez clone ce repository et d'exécuter les commandes suivantes : 

1)  conda env create -f environment.yml -n projet_logistique
2)  conda activate projet_logistique 

Nous avons choisi le cas du quartier latin pour tracer les cartes de flux, mais libre à vous de décider de tracer les cartes de flux pour n'importe laquelle des zones de Paris. Nous avons laissé ici uniquement les scripts python nécessaires pour la réalisation des cartes de flux. 

Voici l'ordre dans lequelle exécuter les scipts python : 
1) Dans un premier temps, vous pourrez exécuter le script python qui vous permettra de trouver tous les noeuds de la zone considérée. Ce premier script est **quartier_latin_find_all_nodes_write_file_final.py**. Vous pourrez modifier les coordonnées de la zone considérée (variable quartier_latin) qui correspondent aux coordonnées des extremités inférieure gauche et supérieure droite de la zone considérée. 
2) 



