import socket, threading


class Agent:
    def __init__(self):
        pass








if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 31415))

    buffer = []
    data = b''
    while True:
        d = s.recv(1024)
        buffer.append(d)
        data = b''.join(buffer)
        if len(data) == 24:
            print(list(data.decode('utf-8')))
            print('{}{}{}{}{}\n{}{}{}{}{}\n{}{}^{}{}\n{}{}{}{}{}\n{}{}{}{}{}\n'.format(*list(data.decode('utf-8'))))

