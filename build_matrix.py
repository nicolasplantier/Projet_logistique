"""
Ce document vient construire les matrices : 
    - liste iti noeuds = telle que liste_iti_noeuds[i][j] renvoie la liste des noeuds par lesquels on va devoir passer pour aller de i vers j 
    - matrix_durations = telle que matrix_durations[i][j] renvoie le temps de trajet necessaire pour aller du noeud i vers le noeud j. On appellera cette matrice lors des calculs de vrpy. 

Ce travail de construction de matrices est un travail préliminaire : il dépend simplement du découpage en sous cluster et ne dépend pas du trafic dans les axes considérés. 

"""

import find_all_nodes as toolbox 

