import socket, threading





class Map:
    class tile:
        def __init__(self, x, y, type = None):
            self.north = None
            self.east  = None
            self.west  = None
            self.south = None
            self.type  = type

        def pos(self):
            return (self.x, self.y)

    def __init__(self, dimension = 80):
        self.ground = dict()
        for i in range(-dimension, dimension + 1):
            for j in range(-dimension, dimension + 1):
                self.ground[(i,j)] = self.tile(i, j)

        for i in range(-dimension, dimension + 1):
            for j in range(-dimension, dimension + 1):
                if (i,j-1) in self.ground:
                    self.ground[(i,j)].north = self.ground[(i,j-1)]
                if (i+1,j) in self.ground:
                    self.ground[(i,j)].east  = self.ground[(i+1,j)]
                if (i-1,j) in self.ground:
                    self.ground[(i,j)].west  = self.ground[(i-1,j)]
                if (i,j+1) in self.ground:
                    self.ground[(i,j)].south = self.ground[(i,j+1)]

    def addTile(self, x, y, type):
        if type != '^':
            self.ground[(x, y)] = type



class Agent:
    SIGHT = 5
    def __init__(self, port):
        self.x = 0
        self.y = 0
        self.facing = 'S'
        self.map = Map()
        self.pipe = Pipe(port)
        self.hasStone = 0
        self.hasAxe = 0
        self.hasKey = 0
        initMap = self.pipe.receive()
        turnedMap = self.turnMapToNorth(initMap)
        for i in range(-self.SIGHT//2+1, self.SIGHT//2+1):
            for j in range(-self.SIGHT//2+1, self.SIGHT//2+1):
                self.map.addTile(i, j, turnedMap[i+self.SIGHT//2][j+self.SIGHT//2])

    def turnMapToNorth(self, map):
        tmpmap = map
        facing = self.facing
        if facing == 'W':
            tmpmap = self.counterclockwiseRotate(tmpmap)
            facing = 'S'
        if facing == 'S':
            tmpmap = self.counterclockwiseRotate(tmpmap)
            facing = 'E'
        if facing == 'E':
            tmpmap = self.counterclockwiseRotate(tmpmap)
            facing = 'N'
        if facing == 'N':
            return tmpmap

    def counterclockwiseRotate(self, map):
        return tuple(zip(*map))

    def start(self):
        while(True):
            goalPath = self.findGoldPath()
            nearestUnknow = self.findNearestUnknown()
            if goalPath:
                self.goTo(goalPath)
                print('Victory')
                break
            elif nearestUnknow:
                self.goTo(nearestUnknow)
            else:
                print('No Path Found')
                break

    def findNearestUnknown(self):
        









class Pipe:
    def __init__(self, port):
        self.data = []
        self.newDataFlag = threading.Event()
        self.port = port
        self.conn = None
        t = threading.Thread(target=self.connection)
        t.setDaemon(True)
        t.start()

    def connection(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(('127.0.0.1', self.port))
        d = b''
        while(True):
            d += self.conn.recv(1024)
            if len(d) == 24:
                nodelist = list(d.decode('utf-8'))
                tmpdata = nodelist[:12] + ['^'] + nodelist[12:]
                grid = [tmpdata[5*i:5*i+5] for i in range(5)]
                self.data = grid
                self.newDataFlag.set()
                d = b''

    def receive(self):
        if self.newDataFlag.wait(1):
            self.newDataFlag.clear()
            return self.data
        return None

    def send(self, message):
        m = str.encode(message)
        self.conn.send(m)

    def messenger(self, message):
        self.send(message)
        if self.newDataFlag.wait(1):
            return self.receive()


if __name__ == '__main__':
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.connect(('127.0.0.1', 31415))
    #
    # buffer = []
    # data = b''
    # while True:
    #     d = s.recv(1024)
    #     buffer.append(d)
    #     data = b''.join(buffer)
    #     if len(data) == 24:
    #         print(list(data.decode('utf-8')))
    #         print('{}{}{}{}{}\n{}{}{}{}{}\n{}{}^{}{}\n{}{}{}{}{}\n{}{}{}{}{}\n'.format(*list(data.decode('utf-8'))))

    # p = Pipe(31415)
    a = Agent(31415)
    # print(p.receive())
    # order = ['f', 'f', 'r', 'r', 'f', 'f', 'r', 'f', 'f', 'f', 'f', 'l', 'f', 'f','r', 'f', 'f']
    # for o in order:
    #     p.messenger(o)