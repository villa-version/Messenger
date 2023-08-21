import select
from socket import socket, AF_INET, SOCK_STREAM
from signal import signal, SIGINT

HOST = ''
PORT = 8432
stop = False


class User:
    client = None
    client_ip = None
    data = None


users = []


def read(sockets, host):
    global users
    for s in sockets:
        if s is host:
            user = User()
            user.client, user.client_ip = s.accept()
            users.append(user)
            print('Client connected ' + user.client_ip[0])
        else:
            for user in users[:]:
                if s is user.client:
                    recv_string = ''
                    while True:
                        recv_byte = user.client.recv(1).decode()
                        if len(recv_byte) == 0:
                            user.client.close()
                            print('Client disconnected ' + user.client_ip[0])
                            users.remove(user)
                            break
                        elif recv_byte == '\n':
                            user.data = recv_string
                            break
                        recv_string += recv_byte


def write(sockets):
    global users
    for s in sockets:
        senders = users[:]
        recipient = None
        for user in users:
            if user.client is s:
                recipient = user
                senders.remove(recipient)
                break
        for sender in senders:
            if sender.data is not None:
                if len(sender.data) != 0:
                    recipient.client.send((sender.data + '\n').encode())


def update_data():
    global users
    for user in users:
        if user.data is not None:
            user.data = None


def main():
    global users, stop

    max_player = 2

    server = socket(AF_INET, SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(max_player)
    while True:
        clients = [user.client for user in users]
        sockets_reading, sockets_writing, _ = select.select([server] + clients, clients, [], 1)
        read(sockets_reading, server)
        write(sockets_writing)
        update_data()

        if stop:
            break

    server.close()


def signal_handler(_, __):
    global stop
    print('Server closing...')
    stop = True


if __name__ == '__main__':
    signal(SIGINT, signal_handler)
    main()