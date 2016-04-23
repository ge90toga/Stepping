import socket, threading
from functools import reduce



class Tile:
    def __init__(self, x, y, type):
        self.__x = x
        self.__y = y
        self.__north = None
        self.__east  = None
        self.__west  = None
        self.__south = None
        self.__type  = type
        self.__beenHere = False

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
        self.__beenHere = True

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
    def __init__(self):
        self.ground = dict()

    def addTile(self, x, y, type):
        if (x, y) not in self.ground:
            tile = Tile(x, y, type)
        else:
            tile = self.ground[(x, y)]
            tile.setType(type)
        self.ground[(x, y)] = tile

        if (x,y-1) not in self.ground:
            self.ground[(x,y-1)] = Tile(x, y-1, 'N')
        tile.setNorth(self.ground[(x,y-1)])

        if (x+1,y) not in self.ground:
            self.ground[(x+1,y)] = Tile(x+1,y, 'N')
        tile.setEast(self.ground[(x+1,y)])

        if (x-1,y) not in self.ground:
            self.ground[(x-1,y)] = Tile(x-1,y, 'N')
        tile.setWest(self.ground[(x-1,y)])

        if (x,y+1) not in self.ground:
            self.ground[(x,y+1)] = Tile(x,y+1, 'N')
        tile.setSouth(self.ground[(x,y+1)])

        if type == '^':
            tile.walked()
            tile.setType(' ')

    def getTile(self, x, y):
        if (x, y) in self.ground:
            return self.ground[(x, y)]
        else:
            return None

    def copy(self):
        newMap = Map()
        for tile in self.ground:
            x, y = tile
            type = self.ground[tile].getType()
            newMap.addTile(x, y, type)
        return newMap

    def findTile(self, type):
        return [x.pos for x in self.ground if x.getType == type]

    def printMap(self):
        ret = []
        xlist, ylist = zip(*[x for x in self.ground])
        xmin,xmax,ymin,ymax = min(xlist), max(xlist), min(ylist), max(ylist)
        for i in range(xmin, xmax+1):
            ret.append([])
            for j in range(ymin, ymax+1):
                if (i, j) in self.ground:
                    ret[-1].append(self.ground[(i,j)].getType())
                else:
                    ret[-1].append('?')
        return reduce(lambda x, y:'{}\n{}'.format(x, y), [''.join(x) for x in ret])

class Agent:
    SIGHT = 5
    def __init__(self, port):
        self.x = 0
        self.y = 0
        self.facing = 2
        self.map = Map()
        # self.pipe = Pipe(port)
        self.hasStone = 0
        self.hasAxe = False
        self.hasKey = False

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
        initMap = [['~', '~', 'k', '~', 'g'],
                   [' ', '~', '~', '~', '-'],
                   [' ', 'o', '^', 'T', ' '],
                   [' ', ' ', ' ', '*', '*'],
                   [' ', ' ', ' ', '-', 'a']]
        # turnedMap = self.turnMapToNorth(initMap)
        turnedMap = initMap
        for i in range(self.SIGHT):
            for j in range(self.SIGHT):
                self.map.addTile(i - self.SIGHT//2, j - self.SIGHT//2, turnedMap[i][j])


        print(self.map.printMap())

        # result = self.findGold([((self.x,self.y), self.hasKey, self.hasAxe, 0)], self.map)
        # result = self.findWay((self.x,self.y), (2, -2))
        # print(result)
        # for x in result:
        #     print(x[0], self.map.getTile(*x[0]).getType())

        self.expand()
        # while(True):
        #     solutionPath = self.findGold(((self.x,self.yr), False, False, 0), self.map)
        #     if solutionPath:
        #         self.goAlong(solutionPath)
        #     else:
        #         hasExpand = self.Expand()
        #         if hasExpand:
        #             self.expand()
        #         else:
        #             print('No solution')
        #             break


    def findGold(self, stack, map):
        if stack:
            if stack[-1] in stack[:-1]:
                return []

            tilepos, key, axe, stone = stack[-1]
            x, y = tilepos

            if tilepos not in self.map.ground:
                return []

            tile = map.getTile(*tilepos)

            if tile.getType() in ['*', 'N']:
                return []
            if tile.getType() == 'g':
                return stack
            if tile.getType() == 'T' and not axe:
                return []
            if tile.getType() == '-' and not key:
                return []
            if tile.getType() == '~' and stone == 0:
                return []

            #Performance can be imporved by lazy copying map. TBD
            myMap = map.copy()
            tile = myMap.getTile(*tilepos)

            if tile.getType() == 'k':
                key = True
                tile.setType(' ')
            if tile.getType() == 'o':
                stone += 1
                tile.setType(' ')
            if tile.getType() == 'a':
                axe = True
                tile.setType(' ')
            if tile.getType() == '~':
                stone -= 1
                tile.setType('O')
            if tile.getType() == '-':
                tile.setType(' ')
            if tile.getType() == 'T':
                tile.setType(' ')

            nPath = self.findGold(stack+[((x, y-1), key, axe, stone)], myMap)
            if nPath:
                return nPath
            ePath = self.findGold(stack+[((x+1, y), key, axe, stone)], myMap)
            if ePath:
                return ePath

            sPath = self.findGold(stack+[((x, y+1), key, axe, stone)], myMap)
            if sPath:
                return sPath

            wPath = self.findGold(stack+[((x-1, y), key, axe, stone)], myMap)
            if wPath:
                return wPath

        return []

    def expand(self):
        borderTiles = self.findBorderTiles()
        borderPathes = self.findConsecutivePathes(borderTiles)
        for path in borderPathes:
            self.goAlong([x.pos() for x in path])

    def findBorderTiles(self):
        x, y = self.x, self.y
        walkable = [' ', 'O', 'k', 'a', 'o']
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

    def findWay(self, originpos, targetpos):
        walkable = [' ', 'O', 'k', 'a', 'o']
        queue = [[originpos]]
        walked = []
        while(queue):
            path = queue[0]
            queue = queue[1:]
            tile = self.map.getTile(*path[-1])
            if tile.getType() not in walkable:
                continue
            elif tile.pos() in walked:
                continue
            elif tile.pos() == targetpos:
                return path
            walked.append(tile.pos())
            queue.append(path+[tile.getNorth().pos()])
            queue.append(path+[tile.getEast().pos()])
            queue.append(path+[tile.getSouth().pos()])
            queue.append(path+[tile.getWest().pos()])
        return []

    def goAlong(self, path):
        head = path[0]
        if head != (self.x, self.y):
            leadingPath = self.findWay((self.x, self.y), head)
            if leadingPath:
                path = leadingPath[:-1]+path

        command = []
        for tile in path[1:]:
            self.goto(tile)

    def goto(self, pos):
        command = ''
        direction = {'N':0, 'E':1, 'S':2, 'W':3}
        x1, y1 = self.x, self.y
        x2, y2 = pos
        myDirection = direction[self.facing]
        if abs(x2-x1)+abs(y2-y1) != 1:
            raise Exception
        targetd = {(0,-1):0, (1,0):1, (0,1):2, (-1,0):3}
        targetDirection = targetd[(x2-x1, y2-y1)]

        turn = (targetDirection - myDirection)%(4*(-myDirection/myDirection))
        if turn != 0:
            if turn < 0:
                leftright = 'l'
                turn = -turn
            else:
                leftright = 'r'
            command += leftright * turn
            self.facing = targetDirection

        targetType = self.map.getTile(x2, y2).getType()
        if targetType == 'T':
            command += 'c'
        elif targetType == '-':
            command += 'u'
        command += 'f'
        self.pipe.send(command)





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