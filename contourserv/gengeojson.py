# This tool generate random geojson file for x and y from 0 to 10 and feature value accord to funcion
# func plus a error function
# Shuo Chen (leo.chen.cipher@outlook.com)

import geojson
from geojson import Feature, Point, FeatureCollection

import numpy as np
from scipy.interpolate import griddata
import numpy.ma as ma
from numpy.random import rand, seed

filename = "tempgeojson.json"
pointnum = 200

def func(xy):
    return xy[0]*np.exp(-xy[0]**2-xy[1]**2)*(1.0+np.random.normal(0.0,0.1))

def geojsongen(filename="tempgeojson.json",pointnum=100):
    xy=[(rand(),rand()) for x in range(0,pointnum)]
    featurecoll = []
    for point in xy:
        my_point = Point(point)
        value = func(point)
        featurecoll.append(Feature(geometry=my_point, properties={"value": value }))
    geojsoncontent = FeatureCollection(featurecoll)
    print geojson.dumps(geojsoncontent)
    with open(filename, "w") as f:
        f.write(geojson.dumps(geojsoncontent))
        f.close()


if __name__ == "__main__":
    geojsongen(filename, pointnum)


