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
    
def two_opt_swap(tour, a_idx, b_idx):
    
    '''
        a_idx and b_idx are distinct indexes > 0 and < #cities
    '''
    
    ncities = len(tour.city_lst)
    
    # shirt circuit if there is no effect or there is an error
    if a_idx == b_idx or a_idx <= 0 or b_idx <= 0 or a_idx >= ncities or b_idx >= ncities:
        return tour # not a valid swap; maybe should throw an error? 
    
    # use the smallest as the left_idx and the biggest as the right_idx
    left_idx = min(a_idx,b_idx)
    right_idx = max(a_idx,b_idx)
    
    # make a closed loop of cities (with the first and last city the same)
    city_lst = list(tour.city_lst)+[tour.city_lst[0]]
    
    
        
    # update the mileage to match the new order
    t_miles = tour.miles
        
    t_miles -= d[city_lst[left_idx]][city_lst[left_idx-1]]
    t_miles -= d[city_lst[right_idx],city_lst[right_idx+1]]
    
    t_miles += d[city_lst[right_idx]][city_lst[left_idx-1]]
    t_miles += d[city_lst[left_idx],city_lst[right_idx+1]]
    
    
    # reverse the cities between left_idx and right_idx
    while left_idx < right_idx:
        t = city_lst[left_idx]
        city_lst[left_idx] = city_lst[right_idx]
        city_lst[right_idx] = t 
        left_idx += 1
        right_idx -= 1
    
    # return a tour
    return Tour(city_lst, t_miles)

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
    

def animate_snapshots(dirpathstr):
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
    anim = animation.ArtistAnimation(fig, ims, interval=50, blit=True,repeat_delay=1000)
    plt.close()
    #anim=animate_snapshots('nn_snapshots')
    #HTML(anim.to_jshtml(fps=5))
    return HTML(anim.to_jshtml(fps=5))
    

def nearest_neighbor(head_idx=0, snapshots=False):
    
    totaldist = 0
    
    # a practical use of a set comprehension!
    unvisited = {i for i in cities_df.index}
    
    # initialize our city_lst using the head_idx
    city_lst=[head_idx]
    unvisited.remove(head_idx)
    
    # there are len(unvisited) spots to fill in city_lst
    for i in range(len(unvisited)):
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
        totaldist += best_d
        unvisited.remove(best_j)
        head_idx = best_j
        
        if snapshots:
            title = "Pass "+str(i)+": Distance = "+str(round(totaldist,2))
            show_map(subtour=city_lst,title=title,closeloop=False,fname="nn_snapshots/s"+str(i))
    
    if snapshots:
        totaldist += d[head_idx][city_lst[0]]
        title = "Complete Tour: Distance = "+str(round(totaldist,2))
        show_map(subtour=city_lst+[city_lst[0]],title=title,closeloop=False,fname="nn_snapshots/s"+str(len(city_lst)-1))
    
    return Tour(city_lst)

class ANode:
    def __init__(self, city,  f, g, n_cities=1, ancestor=None):
        self.ancestor = ancestor
        self.f_value = f_value
        self.g_value = g_value
        self.n_cities = n_cities
        self.ancestor = ancestor
        
    def __lt__(self, other):
        return self.f_value < other.f_value
    
    def subtour(self):
        t = []
        t_node = self
        while t_node.ancestor:
            t = [node.city] + t
            t_node = t_node.ancestor
        return t
    
def expand_node(visited, num_cities):
    return [i for i in range(num_cities) if i not in visited]

def h(new_city_idx, unvisited):
    # minimim spanning tree including new_city_idx
    return 0;
    
    
def best_first_search(head_idx,num_cities):
    # OPEN list
    open_heap = []
    # CLOSED list not needed for an acyclic search graph
    # closed_set = {}
    
    # seed the search tree with the head_idx
    head_node = ANode(head_idx,0)
    heap_push(open_heap,ANode(head_idx,0))
    
    # continue seaching until open_lst is empty
    while open_heap:
        
        # pop the head_node from OPEN and push onto CLOSED  
        head_node = heappop(open_heap)
        #heappush(closed_set,head_node)
        
        # exit wth success if head_node is a complete tour
        visited = head_node.subtour()
        if head_node.n_cities == num_cities:
            return Tour(head_node.subtour())
        
        base_tour = head_node.subtour()
        for new_city_idx in expand_node(base_tour,num_cities):
            # evaluate the newly extended subtour
            new_subtour = base_tour + [new_city_idx]
            new_g = head_node.g + d[head_node.city][new_city_idx]
            new_h = h(new_city_idx, expand_node(new_subtour,num_cities))
            new_f = new_g + new_h
            
            # create a node for the subtour
            new_node = ANode(new_tour,new_f,new_g,head_node.n_cities+1,head_node)
            heappush(open_heap, new_node)
            
    return False;
         

