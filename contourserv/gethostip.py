import socket

#return localhost ip by ping to google dns ip address
testingip="8.8.8.8"
def ip():
    return [(s.connect((testingip, 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

