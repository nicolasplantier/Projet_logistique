import pickle

with open ('Matrice des noeuds pour le cluster', 'rb') as temp:
    items = pickle.load(temp)

# with open ('Matrice des temps pour le cluster', 'rb') as temp:
#     items_temps = pickle.load(temp)

print(items)
