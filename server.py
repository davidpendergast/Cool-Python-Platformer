import json
import socket
import threading
import SocketServer

lock = threading.Lock()
users = {}


class ThreadedUDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        lock.acquire()
        try:
            data = json.loads(self.request[0].strip())

            sendback = []
            if data['user'] in users:
                for ghost in users[data['level']]:
                    if ghost['user'] is not data['user']
                        sendback.append(ghost)
                users
            else
                users[data['level']] = [data]
                
            socket = self.request[1]
            socket.sendto(json.dumps(sendback, self.client_address)
        finally:
            lock.release()


class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass


def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect((ip, port))
        sock.sendall(message)
        response = sock.recv(1024)
        print "Received: {}".format(response)
    finally:
        sock.close()


def form_message(uid, level, pos):
    return json.dumps({'user': user, 'level': level, 'pos': pos})


if __name__ == "__main__":
    HOST, PORT = 'localhost', 0
    server = ThreadedUDPServer((HOST, PORT), ThreadedUDPHandler)
    ip, port = server.server_address

    server_thread = threading.Thread(target=server.serve_forever)

    server_thread.daemon = True
    server_thread.start()

    print "Server started at {} {}".format(ip, port)
    print "Server loop running in thread:", server_thread.name

    client(ip, port, "Hello World 1")
    client(ip, port, "Hello World 2")
    client(ip, port, "Hello World 3")

    raw_input("Press Enter to kill server")

    server.shutdown()
    server.server_close()
