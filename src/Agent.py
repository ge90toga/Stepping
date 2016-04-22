import socket, threading



class Tile:
    def __init__(self, x, y, type = 'N'):
        self.__x = x
        self.__y = y
        self.__north = None
        self.__east  = None
        self.__west  = None
        self.__south = None
        self.__type  = type
        self.__walked = False

    def pos(self):
        return (self.__x, self.__y)

    def getNorth(self):
        return self.__north

    def getEast(self):
        return self.__east

    def getWest(self):
        return self.__west

    def getSouth(self):
        return self.__south

    def getType(self):
        return self.__type

    def walked(self):
        self.walked = True

    def setType(self, type):
        self.__type = type

    def setNorth(self, tile):
        self.__north = tile

    def setWest(self, tile):
        self.__west = tile

    def setEast(self, tile):
        self.__east = tile

    def setSouth(self, tile):
        self.__south = tile

class Map:
    def __init__(self, dimension = 80):
        self.ground = dict()
        for i in range(-dimension, dimension + 1):
            for j in range(-dimension, dimension + 1):
                self.ground[(i,j)] = Tile(i, j)

        for i in range(-dimension, dimension + 1):
            for j in range(-dimension, dimension + 1):
                if (i,j-1) in self.ground:
                    self.ground[(i,j)].setNorth(self.ground[(i,j-1)])
                if (i+1,j) in self.ground:
                    self.ground[(i,j)].setEast(self.ground[(i+1,j)])
                if (i-1,j) in self.ground:
                    self.ground[(i,j)].setWest(self.ground[(i-1,j)])
                if (i,j+1) in self.ground:
                    self.ground[(i,j)].setSouth(self.ground[(i,j+1)])

    def addTile(self, x, y, type):
        if type != '^':
            self.ground[(x, y)].setType(type)
        else:
            self.ground[(x, y)].walked()
            if self.ground[(x, y)].getType() == 'N':
                self.ground[(x, y)].setType(' ')

    def getTile(self, x, y):
        if (x, y) in self.ground:
            return self.ground[(x, y)]
        else:
            return None



class Agent:
    SIGHT = 5
    def __init__(self, port):
        self.x = 0
        self.y = 0
        self.facing = 'S'
        self.map = Map()
        # self.pipe = Pipe(port)
        self.hasStone = 0
        self.hasAxe = 0
        self.hasKey = 0

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
        # initMap = self.pipe.receive()
        # print(initMap)
        initMap = [[' ', ' ', 'o', ' ', ' '],
                   [' ', ' ', ' ', ' ', ' '],
                   [' ', ' ', '^', ' ', ' '],
                   [' ', ' ', ' ', ' ', ' '],
                   [' ', ' ', ' ', ' ', ' ']]
        turnedMap = self.turnMapToNorth(initMap)
        for i in range(self.SIGHT):
            for j in range(self.SIGHT):
                # print(i - self.SIGHT//2, j - self.SIGHT//2, turnedMap[i][j])
                self.map.addTile(i - self.SIGHT//2, j - self.SIGHT//2, turnedMap[i][j])
        # self.traversal()
        # while(True):
        #     goalPath = self.findGoldPath()
        #     nearestUnknow = self.findAnUnknown()
        #     if goalPath:
        #         self.goTo(goalPath)
        #         print('Victory')
        #         break
        #     elif nearestUnknow:
        #         self.goTo(nearestUnknow)
        #     else:
        #         print('No Path Found')
        #         break
        # print(b)

        borderTiles = self.findBorderTiles()
        consecutivePathes = self.findConsecutivePathes(borderTiles)
        # print(consecutivePathes)
        # print(b)
        print([(x.pos(), x.getType()) for y in consecutivePathes for x in y])

        # for t in borderTiles:
        #     self.gotoWithCare(t)

    # def traversal(self):
    #     borderMap = self.getBorderMap(self)
    #     originTile = self.map.getTile(self.x, self.y)


    # def findAnUnknown(self):
    #     originTile = self.map.getTile(self.x, self.y)
    #     stack = [originTile]
    #     wentTile = [originTile]
    #     while(stack):
    #         if originTile.getNorth() not in wentTile:



    def DFS(self, x, y, stack):
        pass


    def findBorderTiles(self):
        x, y = self.x, self.y
        walkable = [' ', 'O', 'k', 'a', '^']
        walked = [self.map.getTile(x, y)]
        stack = [self.map.getTile(x, y)]
        borderTile = []
        while(stack):
            tile = stack.pop()
            walked.append(tile)
            if tile.getType() not in walkable:
                continue
            north = tile.getNorth()
            west = tile.getWest()
            south = tile.getSouth()
            east = tile.getEast()
            if any([x.getType() not in walkable for x in [north, west, south, east]]):
                borderTile.append(tile)

            if north not in walked:
                stack.append(north)
            if west not in walked:
                stack.append(west)
            if south not in walked:
                stack.append(south)
            if east not in walked:
                stack.append(east)
        return borderTile

    def findConsecutivePathes(self, tiles):
        pathes = [[tiles[0]]]
        for i in range(1,len(tiles)):
            pos1 = tiles[i].pos()
            pos2 = tiles[i-1].pos()
            distance = abs(pos1[0]-pos2[0]) + abs(pos1[1]-pos2[1])
            if distance != 1:
                pathes.append([])
            pathes[-1].append(tiles[i])
        return pathes

    # def gotoWithCare(self, tile):
    #     walkable = [' ', 'O', 'k', 'a', '^']
    #     pathes = [[tile]]
    #     walked = [tile]
    #     while(True):
    #         newPaht = []
    #         for path in pathes:
    #             tail = path[-1]
    #             if tail in walked:
    #
    #             north = tail.getNorth()
    #             east = tail.getEast()
    #             south = tail.getSouth()
    #             west = tail.getWest()

    # def goAlong(self, path):
    #     self.goWithCare(path[0])


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
    a.start()
    # print(p.receive())
    # order = ['f', 'f', 'r', 'r', 'f', 'f', 'r', 'f', 'f', 'f', 'f', 'l', 'f', 'f','r', 'f', 'f']
    # for o in order:
    #     p.messenger(o)