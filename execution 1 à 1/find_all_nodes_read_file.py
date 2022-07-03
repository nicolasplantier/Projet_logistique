import pickle

with open ('Liste des dictionnaires des noeuds dans le cluster 2, découpé en sous-clusters', 'rb') as temp:
    items = pickle.load(temp)

print(items)