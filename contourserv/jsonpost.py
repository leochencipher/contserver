import urllib2

def jsonpost(url,data):
    #post data to remote url using application/json header and return response code  
    try:
        clen=len(data)
        req = urllib2.Request(url, data, {'Content-Type': 'application/json', 'Content-Length': clen})
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
        return response.getcode()
    except urllib2.HTTPError, e:
        return e.getcode()
