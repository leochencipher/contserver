import numpy as np
from scipy.interpolate import griddata
import matplotlib
matplotlib.use("SVG")
import matplotlib.pyplot as plt
import numpy.ma as ma
from numpy.random import uniform, seed
import geojson
from geojson import Feature, Point, FeatureCollection

# make up some randomly distributed data

# def testGen(npts=200, fileid="test01"):
# 	seed(1234)
# 	x = uniform(-2,2,npts)
# 	y = uniform(-2,2,npts)
# 	z = x*np.exp(-x**2-y**2)
# 	# define grid.
# 	xi = np.linspace(-2.1,2.1,100)
# 	yi = np.linspace(-2.1,2.1,100)
# 	# grid the data.
# 	zi = griddata((x, y), z, (xi[None,:], yi[:,None]), method='cubic')
# 	# contour the gridded data, plotting dots at the randomly spaced data points.
# 	CS = plt.contour(xi,yi,zi,15,linewidths=0.5,colors='k')
# 	CS = plt.contourf(xi,yi,zi,15,cmap=plt.cm.jet)
# 	plt.colorbar() # draw colorbar
# 	# plot data points.
# 	plt.scatter(x,y,marker='o',c='b',s=5)
# 	plt.xlim(-2,2)
# 	plt.ylim(-2,2)
# 	plt.title('griddata test (%d points)' % npts)
# 	plt.savefig("./static/"+fileid+".svg")
# 	plt.close()

# conf is 2 level dict for configuration with three top level keys "contour", "contourf" and "clable"
def compute(data,conf):
	# process tool config with default config if not existed
	outputformat = "svg"
	if "outFormat" in conf["toolConfig"]:
		outputformat = conf["toolConfig"]["outFormat"]
	outstyle = "line"
	if "outStyle" in conf["toolConfig"]:
		if conf["toolConfig"]["outStyle"] == "line":
			outstyle = "line"
		else:
			outstyle = "map"
	haslevels = False
	levels=[]
	if "levels" in conf["toolConfig"]:
		if len(conf["toolConfig"]["levels"]) > 0: # TODO ugly ugly
			haslevels = True
			levels = [float(x) for x in conf["toolConfig"]["levels"]]

	#process the data from geojson to point value
	pointdata=data
	numpoint=0
	xdata=[]
	ydata=[]
	valuedata=[]
	# get x y range in the meantime
	xmin=pointdata['features'][0]["geometry"]["coordinates"][0]
	xmax=pointdata['features'][0]["geometry"]["coordinates"][0]
	ymin=pointdata['features'][0]["geometry"]["coordinates"][1]
	ymax=pointdata['features'][0]["geometry"]["coordinates"][1]
	for point in pointdata['features']:
		xnow=float(point["geometry"]["coordinates"][0])
		xdata.append(xnow)
		ynow=float(point["geometry"]["coordinates"][1])
		ydata.append(ynow)
		if xnow < xmin:
			xmin = xnow
		if xnow > xmax:
			xmax = xnow
		if ynow < ymin:
			ymin = ynow
		if ynow > ymax:
			ymax = ynow
		valuedata.append(float(point["properties"]["value"]))
		numpoint = numpoint + 1
	# Create mesh grid
	exppercent = 0.1 # expand percentage
	gridnum = 100 #grid density
	xi = np.linspace(xmin*(1.0-exppercent),xmax*(1.0+exppercent),gridnum)
	yi = np.linspace(ymin*(1.0-exppercent),ymax*(1.0+exppercent),gridnum)
	zi = griddata((xdata, ydata), valuedata, (xi[None,:], yi[:,None]), method='cubic')
	#create plot
	ctfig = None
	if outstyle == "line":
		if haslevels:
			ctfig = plt.contour(xi,yi,zi,levels=levels)
		else:
			ctfig = plt.contour(xi,yi,zi,15)	
	if outstyle == "map":
		if haslevels:
			ctfig = plt.contourf(xi,yi,zi,levels=levels)
		else:
			ctfig = plt.contourf(xi,yi,zi,15)
	plt.colorbar() # draw colorbar
	plt.title('griddata')
	plt.clabel(ctfig, inline=1, fontsize=10)
	plt.savefig("./static/"+conf["jobId"]+"."+outputformat)
	plt.close()
	with open("./static/"+conf["jobId"]+"."+outputformat,"r") as f:
		buffer = f.read()
		f.close()
		return (buffer,"Finish Processing Contour Graph with "+str(numpoint)+" points.",0)
	# memory not working right now cause pil not support svg, may need to break the package of pyplot function savefig later
	# buffer = StringIO.StringIO()
 #    canvas = plt.get_current_fig_manager().canvas
 #    canvas.draw()
 #    pil_image = PIL.Image.fromstring('RGB', canvas.get_width_height(), 
 #                 canvas.tostring_rgb())
 #    pil_image.save(buffer, outputformat)
 #    plt.close()
	return ("","error reading file",1)


def test():
	with open("tempgeojson.json","r") as f:
		rawdata=f.read()
		data=geojson.loads(rawdata,object_hook=geojson.GeoJSON.to_instance)
		conf={}
		conf["jobId"]="coutest"
		conf["toolConfig"]={}
		conf["toolConfig"]["outFormat"]="svg"
		conf["toolConfig"]["outStyle"]="map"
		print compute(data,conf)

if __name__ == '__main__':
	test()
		
