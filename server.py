import json
import socket
import threading
import SocketServer

SERVER_IP   = "ec2-52-34-39-179.us-west-2.compute.amazonaws.com"
SERVER_PORT = 50069

lock = threading.Lock()
users = {}

class ThreadedUDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        lock.acquire()
        try:
            # format: {'user': .., 'level': .., 'pos: (.., ..)}
            data = json.loads(self.request[0].strip())
            users[data['user']] = data

            sendback = []
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
    try:
        sock.connect((SERVER_IP, SERVER_PORT))
        sock.sendall(json.dumps({'user': user, 'level': level, 'position': position}))
        return json.loads(sock.recv(1024))
    finally:
        sock.close()
        return {}


if __name__ == "__main__":
    server = ThreadedUDPServer((SERVER_IP, SERVER_PORT), ThreadedUDPHandler)
    ip, port = server.server_address

    server_thread = threading.Thread(target=server.serve_forever)

    server_thread.daemon = True
    server_thread.start()

    print "Server started at {} {}".format(ip, port)
    raw_input("Press Enter to kill server")

    server.shutdown()
    server.server_close()
