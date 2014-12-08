# author: oskar.blom@gmail.com
#
# Make sure your gevent version is >= 1.0
import gevent
from gevent.wsgi import WSGIServer
from gevent.queue import Queue
import uuid
from flask import Flask, Response, request, render_template,session,redirect,url_for
import contour


# SSE "protocol" is described here: http://mzl.la/UPFyxY

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

app = Flask(__name__)
subscriptions = []

@app.route('/')
def index():
    if 'username' in session:
        jobid=str(uuid.uuid4())
        return render_template("dataform.html",username=session['username'],jobid=jobid)
    return 'You are not logged in'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return '''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
    '''



@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'




@app.route("/debug")
def debug():
    resp = []
    resp.append("Currently %d subscriptions" % len(subscriptions))
    for que in subscriptions:
        resp.append("message number:"+str(que.qsize()))
    return "<br>".join(resp)


@app.route("/publish")
def publish():
    #Dummy data - pick up from request for real data
    def notify():
        msg = "test pub"
        for sub in subscriptions[:]:
            sub.put(msg)
    
    gevent.spawn(notify)
    
    return "OK"

######
@app.route("/ContourData",methods=["POST"])
def getData():
    assert request.method == "POST"
    filename=request.form['jobid']
    pointdata=int(request.form['pointdata'])
    def calculate(filename,jobid,pointdata):
        contour.testGen(npts=pointdata,fileid=filename)
        print ServerSentEvent(filename).encode()
        print len(subscriptions)
        for sub in subscriptions:
            sub.put(filename)
            print sub.qsize()
    gevent.spawn_later(2,calculate,filename,request.form['jobid'],pointdata)
    return render_template("dataresult.html",jobid=(request.form['jobid']))

@app.route("/subscribe")
def subscribe():
    def gen():
        q = Queue()
        subscriptions.append(q)
        try:
            while True:
                result = q.get()
                ev = ServerSentEvent(str(result))
                yield ev.encode()
        except GeneratorExit: # Or maybe use flask signals
            subscriptions.remove(q)
    return Response(gen(), mimetype="text/event-stream")

if __name__ == "__main__":
    # app.debug = True
    server = WSGIServer(("0.0.0.0", 5000), app)
    server.serve_forever()
    # Then visit http://localhost:5000 to subscribe 
    # and send messages by visiting http://localhost:5000/publish