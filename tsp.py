import pandas as pd
import geopandas
from shapely import wkt
from shapely.geometry import Point, LineString, Polygon
import re
import matplotlib.pyplot as plt

# load the baseball cities into a DataFrame
cities_df = pd.read_csv('BaseballCitiesUS.csv')
cities_df['Coordinates'] = cities_df['Coordinates'].apply(wkt.loads)

#convert the DataFrame into a GeoDataFrame 
cities_gdf= geopandas.GeoDataFrame(cities_df,geometry='Coordinates')

#load the US map
united_states = geopandas.read_file("states.shp")


# build the distance matrix for the selected cities
all_dist_matrix = pd.read_csv("MileageChartAllUS.csv", index_col=0)
d = []
for city_from in cities_df.iterrows():
    i = city_from[0]
    name_i = city_from[1][0]
    di = []
    for city_to in cities_df.iterrows():
        j = city_to[0]
        name_j = city_to[1][0]
        if i == j:
            di += [0]
        else:
            di += [all_dist_matrix[name_i][name_j]]
    d += [di]

    
class Tour:
    def __init__(self, city_lst, miles=0):
        self.city_lst = city_lst
        if (miles>0):
            self.miles = miles
        else:
            self.miles = self.total_miles()
    
    def total_miles(self):
        # initialize the cost with the distance of the final return arc (back to 0-th city)
        t_miles = d[self.city_lst[-1]][self.city_lst[0]]
    
        # add in the costs from each city to the next
        for i in range(len(self.city_lst)-1):
            t_miles += d[self.city_lst[i]][self.city_lst[i+1]]
    
        return t_miles
    
    def delta_miles(self,new_city_lst):
        return 0

def show_map(tour=None, title=""):
    
    # prep the plot using the US map canvas (ax)
    ax = united_states[1:50].plot(
        color='white', edgecolor='gray',figsize=(30,30))
    ax.axis('off')
    
    if tour:
        city_lst = tour.city_lst
        # encode the city_lst for GeoPandas; included the final return arc
        path = LineString([cities_df['Coordinates'][i]  for i in city_lst + [city_lst[0]] ])
        path_gdf = geopandas.GeoSeries(path)
        path_gdf.plot(ax=ax, color='green',linewidth=2)
        
        title += "; Total Distance: "+str(round(tour.miles,1))
    
    # mark and label the cities
    cities_gdf.plot(ax=ax, color='red')
    props = dict(boxstyle='round', facecolor='linen', alpha=1)
    for c in cities_gdf.iterrows():
        ax.annotate(s=c[1][0],xy=(c[1][1].x,c[1][1].y), color="blue",fontsize=8)
    
    plt.title(title, fontdict = {'fontsize':22})
    plt.show()
    
   

def nearest_neighbor(head_idx=0):
    # a practical use of a set comprehension!
    unvisited = {i for i in cities_df.index}
    
    # initialize our city_lst using the head_idx
    city_lst=[head_idx]
    unvisited.remove(head_idx)
    
    # there are len(unvisited) spots to fill in city_lst
    for i in range(len(unused)):
        # find the closest city in unsued to head_indx
        
        # keep track of best move so far; seed with initial values
        best_d = 100000.0
        best_j = 0
        
        # try each unused city for next on the list; keep track of the closest one to the head_idx
        for j in unvisited:
            if d[head_idx][j] < best_d:
                best_d = d[head_idx][j]
                best_j = j
                
        # add the next city to the list; update head_idx and unused accordingly 
        city_lst += [best_j]
        unvisited.remove(best_j)
        head_idx = best_j
        
    return Tour(city_lst)

