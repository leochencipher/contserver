from flask import Flask
from flask import request,Response

app = Flask(__name__)

@app.route('/')
def hello_world():
	return 'Hello World!'

@app.route('/reader',methods=['GET','POST'])
def readGeoData():
	if request.method == 'POST':
		gotData()
	else:
		return 'Non Data Provided'
def gotData():
	return "process the data here"

if __name__ == '__main__':
	app.run()