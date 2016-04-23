import socket
from functools import reduce

SIGHT = 5

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

    def beenHere(self):
        return self.__beenHere

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
        self.x = 0
        self.y = 0
        self.facing = 0
        self.lock = False

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
        xlist, ylist = zip(*[x for x in self.ground])
        xmin,xmax,ymin,ymax = min(xlist), max(xlist), min(ylist), max(ylist)

        ret = [[str(x%10) for x in range(xmin-1, xmax+1)]]
        for i in range(ymin, ymax+1):
            ret.append([str(i%10)])
            for j in range(xmin, xmax+1):
                if (j, i) in self.ground:
                    if self.myPos() == (j, i):
                        direction = {0:'^', 1:'>', 2:'v', 3:'<'}
                        ret[-1].append(direction[self.getFacing()])
                    else:
                        ret[-1].append(self.ground[(j,i)].getType())
                else:
                    ret[-1].append('?')
        return reduce(lambda x, y:'{}\n{}'.format(x, y), [''.join(x) for x in ret])

    def myPos(self):
        return (self.x, self.y)

    def insertScope(self, scope):
        turnedMap = self.turnMapToNorth(scope)
        x, y = self.myPos()
        for i in range(SIGHT):
            for j in range(SIGHT):
                self.addTile(x + j - SIGHT//2, y + i - SIGHT//2, turnedMap[i][j])

    def turnMapToNorth(self, scope):
        facing = self.facing
        newscope = scope
        for i in range(facing):
            newscope = self.counterclockwiseRotate(newscope)
        return newscope

    #TBD
    def counterclockwiseRotate(self, map):
        ret = map
        for i in range(3):
            ret = tuple(zip(*ret))[::-1]
        return ret
        # return tuple(zip(*map))[::-1]

    def setPos(self, x, y):
        self.x = x
        self.y = y

    def setFacing(self, facing):
        self.facing = facing%4

    def getFacing(self):
        return self.facing

class Agent:
    SIGHT = 5
    def __init__(self, port):
        self.map = Map()
        self.pipe = Pipe(port, self.map)
        self.hasStone = 0
        self.hasAxe = False
        self.hasKey = False


    def start(self):
        while(True):
            print('looking for solution...')
            solutionPath = self.findGold([(self.map.myPos(), self.hasKey, self.hasAxe, self.hasStone)], self.map, set())
            if solutionPath:
                self.goAlong([x[0] for x in solutionPath])
                print('Victory')
                break
            else:
                print('no solution, expand')
                hasExpand = self.expand()
                if hasExpand:
                    self.expand()
                else:
                    print('No solution')
                    break

    def findGold(self, stack, map, went):
        if stack:
            if stack[-1] in went:
                return []
            went.add(stack[-1])
            tilepos, key, axe, stone = stack[-1]
            x, y = tilepos

            if tilepos not in self.map.ground:
                return []

            tile = map.getTile(*tilepos)

            if tile.getType() in ['*', 'N', '.']:
                return []
            if tile.getType() == 'g':
                return stack
            if tile.getType() == 'T' and not axe:
                return []
            if tile.getType() == '-' and not key:
                return []
            if tile.getType() == '~' and stone == 0:
                return []

            if tile.getType() in 'koa~-T':
                myMap = map.copy()
                tile = myMap.getTile(*tilepos)
                if tile.getType() == 'k':
                    # print(stack)
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
            else:
                myMap = map
                tile = map.getTile(*tilepos)

            nPath = self.findGold(stack+[((x, y-1), key, axe, stone)], myMap, went)
            if nPath:
                return nPath
            ePath = self.findGold(stack+[((x+1, y), key, axe, stone)], myMap, went)
            if ePath:
                return ePath

            sPath = self.findGold(stack+[((x, y+1), key, axe, stone)], myMap, went)
            if sPath:
                return sPath

            wPath = self.findGold(stack+[((x-1, y), key, axe, stone)], myMap, went)
            if wPath:
                return wPath
        return []

    def expand(self):
        borderTiles = self.findBorderTiles()
        if borderTiles:
            borderPathes = self.findConsecutivePathes(borderTiles)
            for path in borderPathes:
                self.goAlong([x.pos() for x in path])
        return len(borderTiles) != 0

    def findBorderTiles(self):
        x, y = self.map.myPos()

        walkable = [' ', 'O', 'k', 'a', 'o']
        if self.hasKey:
            walkable.append('-')
        if self.hasAxe:
            walkable.append('T')

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
            if any([x.getType() not in walkable for x in [north, west, south, east]]) and not tile.beenHere():
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
        if head != (self.map.myPos()):
            leadingPath = self.findWay(self.map.myPos(), head)
            if leadingPath:
                path = leadingPath[:-1] + path
        print('Go along path:')
        print(path)
        for tile in path[1:]:
            self.step(tile)

    def step(self, pos):
        command = ''
        x1, y1 = self.map.myPos()
        x2, y2 = pos
        myDirection = self.map.getFacing()
        targetTile = self.map.getTile(x2, y2)
        if abs(x2-x1)+abs(y2-y1) > 1:
            raise Exception
        elif abs(x2-x1)+abs(y2-y1) == 0:
            return
        targetd = {( 0, -1): 0, #North
                   ( 1,  0): 1, #East
                   ( 0,  1): 2, #South
                   (-1,  0): 3} #West
        targetDirection = targetd[(x2-x1, y2-y1)]
        turn = targetDirection - myDirection


        if abs(turn) == 2:
            command += 'rr'
        elif turn == 1 or turn == -3:
            command += 'r'
        elif turn == 3 or turn == -1:
            command += 'l'

        targetType = targetTile.getType()I
        if targetType == 'T':
            command += 'c'
            targetTile.setType(' ')
        elif targetType == '-':
            command += 'u'
            targetTile.setType(' ')
        elif targetType == '~':
            self.hasStone -= 1
            targetTile.setType('O')
        elif targetType == 'o':
            self.hasStone += 1
            targetTile.setType(' ')
        elif targetType == 'a':
            self.hasAxe = True
        elif targetType == 'k':
            self.hasKey = True

        command += 'f'
        for c in command:
            print(self.map.myPos(), self.map.getFacing(), 'command: '+c)
            print('key',self.hasKey,'axe',self.hasAxe,'stone', self.hasStone)
            if c == 'r':
                self.map.setFacing(self.map.getFacing()+1)
            elif c == 'l':
                self.map.setFacing(self.map.getFacing()-1)
            elif c == 'f':
                self.map.setPos(x2, y2)
                self.map.getTile(x2, y2).walked()
            self.pipe.send(c)

class Pipe:
    def __init__(self, port, map):
        self.port = port
        self.conn = None
        self.map = map

        self.connection()

    def connection(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(('127.0.0.1', self.port))
        self.receiver()

    def send(self, message):
        m = str.encode(message)
        self.conn.send(m)
        self.receiver()

    def receiver(self):
        d = b''
        while(True):
            d += self.conn.recv(1024)
            if len(d) == 24:
                nodelist = list(d.decode('utf-8'))
                tmpdata = nodelist[:12] + ['^'] + nodelist[12:]
                grid = [tmpdata[5*i:5*i+5] for i in range(5)]
                self.map.insertScope(grid)
                print(self.map.printMap())
                break

if __name__ == '__main__':
    a = Agent(31415)
    a.start()

