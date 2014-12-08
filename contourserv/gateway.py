import gevent
# use uuid as job id
import uuid
from gevent.wsgi import WSGIServer
from gevent.queue import Queue

from flask import Flask, Response, request, render_template, session, redirect, url_for, json
import base64
import jsonpost
# use static import for now
import contour
# local ip check
import gethostip

# handle gzipped response
from flask import after_this_request, request
from cStringIO import StringIO as IO
import gzip
import functools 


def gzipped(f):
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                response.status_code >= 300 or
                'Content-Encoding' in response.headers):
                return response
            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb', 
                                      fileobj=gzip_buffer)
            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func

class ServerSentEvent(object):
    def __init__(self, data,event=None,sseid=None):
        self.data = data
        self.event = event
        self.id = sseid
        self.desc_map = {
            self.data : "data",
            self.event : "event",
            self.id : "id"
        }

    def encode(self):
        if not self.data:
            return ""
        lines = ["%s: %s" % (v, k) 
                 for k, v in self.desc_map.iteritems() if k]        
        return "%s\n\n" % "\n".join(lines)

# job dict with job id as key
# jobid: [jobstatus(s,r,f),event_queue for sse,Greenlet for job management]
JobPool = {}

#testing dynamic loading
# class ComputeModule:
#     def __init__(self, module_name, conf):
#         self.module = __import__(module_name)
#         self.conf = conf

#     def compute():
#         return self.module.compute(self.conf)

app = Flask(__name__)


# Debug doc
@app.route('/tools/contour/debug', methods=["GET"])
def returnAPIDoc():
    return render_template("api.html")

# method switch
@app.route('/tools/contour', methods=['GET', 'POST'])
@gzipped
def apiSwitch():
    if request.method == 'GET':
        return render_template("api.html")
    elif request.method == 'POST':
        if request.headers['Content-Type'] == 'application/json':
            return submitJob(request.json)

def submitJob(para_dict):
    # Create the job id and registe to job pool
    jobid=str(uuid.uuid4())
    para_dict["jobId"]=jobid
    JobPool[jobid]=['s',[],None]  # registe job as started
    if para_dict["async"] == "yes":
        JobPool[jobid][2]=gevent.spawn(asyncCompute,para_dict)
        data = {'jobId'  : jobid,
            'result' : '',
            'processingLog' : '',
            'sseUrl': 'tools/contour/'+jobid+'/event' # TODO fix the complete url later
            }
        js = json.dumps(data)
        resp = Response(js, status=200, mimetype='application/json')
        return resp
    else:
        # the default is block processing
        JobPool[jobid][0]='r'
        (imagedata,processlog,exitcode) = contour.compute(para_dict["input"],para_dict)
        JobPool[jobid][0]='f'
        if exitcode == 0:
            data = {'jobId'  : jobid,
            'result' : base64.b64encode(imagedata),
            'processingLog' : base64.b64encode(processlog),
            'base64Encoded' : ['result','processingLog']
            }
            js = json.dumps(data)
            resp = Response(js, status=200, mimetype='application/json')
            JobPool.pop(jobid,None)
            return resp
        else:
            JobPool.pop(jobid,None)
            return Response("",status=500) # TODO return server error for now
        JobPool.pop(jobid,None)
        return Response("",status=400) # Computation error?

def asyncCompute(para_dict):
    jobid=para_dict["jobId"]
    publishsse(jobid,"Job started")
    JobPool[jobid][0]='r'
    (imagedata,processlog,exitcode) = contour.compute(para_dict["input"],para_dict)
    JobPool[jobid][0]='f'
    publishsse(jobid,"Computation finished")
    if exitcode == 0:
            data = {'jobId'  : jobid,
            'result' : base64.b64encode(imagedata),
            'base64Encoded':['result']
            }
            js = json.dumps(data)
            publishsse(jobid,"Post result to remote url")
            jsonpost.jsonpost(para_dict["resultUrl"],js)
            publishsse(jobid,"Post processing log to remote url")
            data = {'jobId'  : jobid,
            'processingLog' : base64.b64encode(processlog),
            'base64Encoded':['processingLog']
            }
            js = json.dumps(data)
            jsonpost.jsonpost(para_dict["processLogUrl"],js)
            publishsse(jobid,"Job done")
            JobPool.pop(jobid,None)
            return 0
    else:
        publishsse(jobid,"Computation module error")
        publishsse(jobid,"Post processing log to remote url")
        data = {'jobId'  : jobid,
            'processingLog' : processlog,
            }
        js = json.dumps(data)
        jsonpost.jsonpost(para_dict["processLogUrl"],js)
        publishsse(jobid,"Job done")
        JobPool.pop(jobid,None)
        return 1 # TODO return server error for now

#publish message in jobid channel
def publishsse(jobid, message):
    for sub in JobPool[jobid][1]:
        sub.put(message)

@app.route('/tools/contour/<job_id>')
def jobAPISwitch():
    if request.method == 'GET':
        if job_id in JobPool:
            return "Job status is"+JobPool[job_id][0]
        else:
            return "Job not found"
    elif request.method == 'POST':
        return "Change job status, in construction" #TODO and job cancel throught greenlet cancel
    
@app.route('/tools/contour/<job_id>/event')
def subscribe():
    def gen():
        q = Queue()
        JobPool[job_id][1].append(q)
        try:
            while True:
                result = q.get()
                ev = ServerSentEvent(str(result))
                yield ev.encode()
        except GeneratorExit: # Or maybe use flask signals
            JobPool[job_id][1].remove(q)
    return Response(gen(), mimetype="text/event-stream")

if __name__ == '__main__':
    portnum = 5000
    app.debug = True
    server = WSGIServer(("0.0.0.0", portnum), app)
    print "Starting server at http://"+gethostip.ip()+":"+str(portnum)
    server.serve_forever()

