import pandas as pd
import geopandas
from shapely import wkt
from shapely.geometry import Point, LineString, Polygon
import re
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.animation as animation
from pathlib import Path
from PIL import Image
from IPython.display import HTML
from matplotlib import animation, rc


# load the baseball cities into a DataFrame
cities_df = pd.read_csv('BaseballCitiesUS.csv')
cities_df['Coordinates'] = cities_df['Coordinates'].apply(wkt.loads)
ncities=cities_df.shape[0]
print(ncities)

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


    
dsym = [[0]*ncities for j in range(ncities)]
for i in range(0,ncities-1):
    for j in range(i+1,ncities):
        dsym[i][j]= min(d[i][j],d[j][i])
        dsym[j][i] = dsym[i][j]

def generate_three_col_dist():
    d_flat = [{'from_city':city_from[1][0], 'to_city':city_to[1][0], 'dist':d[city_from[0]][city_to[0]]} for city_from in cities_df.iterrows() for city_to in cities_df.iterrows()]
    d_flat_df=pd.DataFrame(d_flat)
    d_flat_df.to_csv('MileageThreeColumn.csv', index=False)
    
    
class Tour:
    def __init__(self, city_lst, miles=0):
        self.city_lst = city_lst
        if (miles>0):
            self.miles = miles
        else:
            self.miles = self.total_miles()
    
    def total_miles(self):
        # initialize the cost with the distance of the final return arc (back to 0-th city)
        t_miles=0
        
        # add in the costs from each city to the next
        for i in range(len(self.city_lst)-1):
            t_miles += d[self.city_lst[i]][self.city_lst[i+1]]
        
        t_miles += d[self.city_lst[-1]][self.city_lst[0]]
    
        return t_miles
    


def show_map(subtour=None, title="",closeloop=False, fname=None):
    
    # prep the plot using the US map canvas (ax)
    ax = united_states[1:50].plot(
        color='white', edgecolor='gray',figsize=(30,15))
    ax.axis('off')
    
    if subtour:
        
        #create a list of cities 
        city_lst = list(subtour)
        if closeloop:
            city_lst += [subtour[0]]
        
        # encode the city_lst for GeoPandas
        path_lst = [(cities_df['Coordinates'][i].x,cities_df['Coordinates'][i].y)  for i in city_lst]
        path = LineString(path_lst)
        path_gdf = geopandas.GeoSeries(path)
        path_gdf.plot(ax=ax, color='green',linewidth=2)
        
    
    # mark and label the cities
    cities_gdf.plot(ax=ax, color='red')
    props = dict(boxstyle='round', facecolor='linen', alpha=1)
    for c in cities_gdf.iterrows():
        ax.annotate(s=c[1][0],xy=(c[1][1].x,c[1][1].y), color="blue",fontsize=8)
    
    plt.title(title, fontdict = {'fontsize':22})
    if fname:
        plt.savefig(fname,bbox_inches='tight',pad_inches=0.01)
        plt.close()
    else:
        plt.show()
    

def animate_snapshots(dirpathstr,interval=250):
    snum=0
    ims = []
    #fig = plt.figure(figsize=(30,20),frameon=False)
    fig = plt.figure(figsize=(30,15))
    plt.axis("off")
    
    #plt.margins(x=0,y=0.1)
    while Path(dirpathstr+'/s'+str(snum)+'.png').exists():
        # print(snum)
        img = mpimg.imread(dirpathstr+'/s'+str(snum)+'.png')
        im = plt.imshow(img, animated=True)
        ims.append([im])
        snum +=1
    anim = animation.ArtistAnimation(fig, ims, interval=interval, blit=True)
    plt.close()
    return HTML(anim.to_jshtml())
    




    

         

