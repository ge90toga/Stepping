import socket, hashlib
from functools import reduce

SIGHT = 5


class Tile:
    def __init__(self, x, y, type, map):
        self.__x = x
        self.__y = y
        self.__type  = type
        self.__beenHere = False
        self.map = map

    def pos(self):
        return (self.__x, self.__y)

    def getNorth(self):
        return self.map.ground[(self.__x, self.__y - 1)]

    def getEast(self):
        return self.map.ground[(self.__x + 1, self.__y)]

    def getWest(self):
        return self.map.ground[(self.__x - 1, self.__y)]

    def getSouth(self):
        return self.map.ground[(self.__x, self.__y + 1)]

    def getType(self):
        return self.__type

    def beenHere(self):
        return self.__beenHere

    def walked(self):
        self.__beenHere = True

    def setType(self, type):
        self.__type = type

class Map:
    def __init__(self):
        self.ground = dict()
        self.x = 0
        self.y = 0
        self.facing = 0
        self.lock = False
        self.hasgold = False
        self.wentTile = {(0,0)}

    def addTile(self, x, y, type):
        if (x, y) not in self.ground:
            tile = Tile(x, y, type, self)
        else:
            tile = self.ground[(x, y)]
            tile.setType(type)
        self.ground[(x, y)] = tile

        if (x,y-1) not in self.ground:
            self.ground[(x,y-1)] = Tile(x, y-1, 'N', self)

        if (x+1,y) not in self.ground:
            self.ground[(x+1,y)] = Tile(x+1,y, 'N', self)

        if (x-1,y) not in self.ground:
            self.ground[(x-1,y)] = Tile(x-1,y, 'N', self)

        if (x,y+1) not in self.ground:
            self.ground[(x,y+1)] = Tile(x,y+1, 'N', self)

        if type == '^':
            tile.walked()
            tile.setType(' ')

        if type == 'g':
            self.hasgold = True

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
        print(self.printMap())

    def turnMapToNorth(self, scope):
        facing = self.facing
        newscope = scope
        if facing == 1:
            newscope = self.clockwiseRotate([x[::-1] for x in newscope][::-1])
        elif facing == 2:
            newscope = [x[::-1] for x in newscope][::-1]
        elif facing == 3:
            newscope = self.clockwiseRotate(newscope)
        return newscope

    def clockwiseRotate(self, map):
        return tuple(zip(*map))[::-1]

    def setPos(self, x, y):
        self.x = x
        self.y = y
        self.wentTile.add((x,y))

    def setFacing(self, facing):
        self.facing = facing%4

    def getFacing(self):
        return self.facing

    def hasGold(self):
        return self.hasgold

    def goldPos(self):
        return [x for x in self.ground if self.ground[x].getType() == 'g'][0]

    def resourcePos(self):
        return [x for x in self.ground if self.ground[x].getType() in 'kao']

    def mapIndex(self):
        return hashlib.sha224(u''.join([self.ground[x].getType() for x in self.ground]).encode('utf-8')).hexdigest()

    def stonesOnGround(self):
        return len([x for x in self.ground if self.ground[x].getType() == 'o'])

    def surrondingType(self, x, y):
        ret = set()
        for i in range(x-SIGHT//2, x+SIGHT//2 +1):
            for j in range(y-SIGHT//2, y+SIGHT//2 +1):
                if (i,j) in self.ground:
                    ret.add(self.ground[(i,j)].getType())
        return ret

    def beenHere(self, x, y):
        return (x, y) in self.wentTile

class Agent:
    SIGHT = 5
    def __init__(self, port):
        self.map = Map()
        self.pipe = Pipe(port, self.map)
        self.hasStone = 0
        self.hasAxe = False
        self.hasKey = False
        self.commandCounter= 0

    def start(self):
        while(True):
            print('looking for solution...')
            if self.map.hasGold():
                solutionPath = self.findGold()
                if solutionPath:
                    self.goAlong([x for x in solutionPath])
                    print('Victory')
                    print('command counter: ',self.commandCounter)
                    break
            print('no solution, expand')
            hasExpand = self.expand()
            if hasExpand:
                while(self.expand()):
                    resources = self.map.resourcePos()
                    for pos in resources:
                        pathToResource = self.findWay(self.map.myPos(), pos)
                        if pathToResource:
                            self.goAlong(pathToResource)
                    if resources:
                        break
            else:
                print('No solution')
                break

    def findGold(self):
        map = self.mapProcess(self.map)
        print('processed map')
        print(map.printMap())
        stack = [([self.map.myPos()], self.hasKey, self.hasAxe, self.hasStone, map)]
        went = set()
        while(stack):
            path, key, axe, stone, map = stack[0]
            stack = stack[1:]
            tilepos = path[-1]

            if tilepos not in map.ground:
                continue

            tile = map.getTile(*tilepos)

            if tile.getType() in '*N.':
                continue
            elif tile.getType() == 'g':
                return path
            elif tile.getType() == 'T' and not axe:
                continue
            elif tile.getType() == '-' and not key:
                continue
            elif tile.getType() == '~' and stone == 0:
                continue

            if tile.getType() in 'koa~':
                myMap = map.copy()
                tile = myMap.getTile(*tilepos)
                if tile.getType() == 'k':
                    key = True
                if tile.getType() == 'o':
                    stone += 1
                    tile.setType(' ')
                if tile.getType() == 'a':
                    axe = True
                    tile.setType(' ')
                if tile.getType() == '~':
                    stone -= 1
                    tile.setType('O')
            else:
                myMap = map

            if (tilepos, key, axe, stone, myMap) in went:
                continue
            went.add((tilepos, key, axe, stone, myMap))

            x, y = tilepos
            stack.append((path+[(x, y-1)], key, axe, stone, myMap))
            stack.append((path+[(x+1, y)], key, axe, stone, myMap))
            stack.append((path+[(x, y+1)], key, axe, stone, myMap))
            stack.append((path+[(x-1, y)], key, axe, stone, myMap))
        return []

    def mapProcess(self, map):
        return map
        myMap = map.copy()
        x1, y1 = myMap.goldPos()
        stone = self.hasStone + myMap.stonesOnGround()
        resource = map.resourcePos()
        s = {(x1, y1)}
        for x, y in resource:
            for i in range(x-stone, x+stone+1):
                for j in range(x-stone, x+stone+1):
                    s.add((i,j))
        for x2, y2 in myMap.ground:
            if myMap.getTile(x2, y2).getType() == '~' and (x2, y2) not in s:
                myMap.getTile(x2, y2).setType('*')
        return myMap

    def expand(self):
        borderTiles = self.findBorderTiles()
        if borderTiles:
            borderPathes = self.findConsecutivePathes(borderTiles)
            self.goAlong([x.pos() for x in borderPathes])
        return len(borderTiles) != 0

    def findBorderTiles(self):
        x, y = self.map.myPos()

        walkable = {' ', 'O', 'k', 'a', 'o'}
        if self.hasKey:
            walkable.add('-')
        if self.hasAxe:
            walkable.add('T')

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
            # if any([x.getType() not in walkable for x in [north, west, south, east]]) and not self.map.beenHere(*tile.pos()):
            #     borderTile.append(tile)
            # print(self.map.surrondingType(*tile.pos()))
            if 'N' in self.map.surrondingType(*tile.pos()):
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
        pathes = [[x] for x in tiles]
        while(True):
            flag = False
            for i in range(len(pathes)):
                for j in range(len(pathes)):
                    if i == j:
                        continue
                    x1, y1 = pathes[i][-1].pos()
                    x2, y2 = pathes[j][0].pos()
                    if abs(x1-x2) + abs(y1-y2) == 1:
                        pathes[i] += pathes[j]
                        pathes = pathes[:j] + pathes[j+1:]
                        flag = True
                        break
                if flag:
                    break
            if flag:
                continue
            break

        return [path for path in pathes if len(path) == max([len(path) for path in pathes])][0]

    #WFS to find shorttest way
    def findWay(self, originpos, targetpos):
        walkable = {' ', 'O', 'k', 'a', 'o'}
        if self.hasKey:
            walkable.add('-')
        if self.hasAxe:
            walkable.add('T')
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

        targetType = targetTile.getType()
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
            self.commandCounter += 1
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
                break

if __name__ == '__main__':
    a = Agent(31415)
    a.start()
