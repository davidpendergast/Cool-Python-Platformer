import json
import socket
import threading
import SocketServer

SERVER_IP = "52.34.151.88"
SERVER_PORT = 50069

lock = threading.Lock()
users = {}
next_uid = 0


class ThreadedUDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
	global next_uid
        lock.acquire()
        try:
            # format: {'user': .., 'level': .., 'pos: (.., ..)}
            # to get an id: {'user': '__NEWUSER__'}
            # to disconnect: {'user': .., 'level': None ...}
            data = json.loads(self.request[0].strip())

            sendback = []

            if data['user'] == '__NEWUSER__':
		print "new user! ", next_uid
                sendback = next_uid
                next_uid += 1
            else:
                if data['level'] is None:
                    try:
			print "disconnect! ", data['user']
                        del users[data['user']]
                    except:
                        pass
		else:
	                users[data['user']] = data
        	        for user in users:
                	    if user is not data['user'] \
	                      and users[user]['level'] is data['level']:
        	                sendback.append(users[user])
            socket = self.request[1]
            socket.sendto(json.dumps(sendback), self.client_address)
        finally:
            lock.release()


class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass


def send(user, level, position):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    sock.sendall(json.dumps({
        'user': user,
        'level': level,
        'position': position}))
    r = json.loads(sock.recv(1024))
    sock.close()
    return r

def connect():
    return send('__NEWUSER__', None, None)

def disconnect(user):
    send(user, None, None)


def _SET_SERVER_IP(server):
    SERVER_IP = server


if __name__ == "__main__":
    server = ThreadedUDPServer(('0.0.0.0', SERVER_PORT), ThreadedUDPHandler)
    ip, port = server.server_address

    server_thread = threading.Thread(target=server.serve_forever)

    server_thread.daemon = True
    server_thread.start()

    print "Server started at {} {}".format(ip, port)
    raw_input("Press Enter to kill server\n")

    server.shutdown()
    server.server_close()
