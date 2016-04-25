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

    def __getitem__(self, item):
        return self.ground[item]

    def __setitem__(self, key, value):
        if key in self:
            self.ground[key] = value

    def __contains__(self, item):
        return item in self.ground

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

    def north(self, pos):
        return (pos[0], pos[1] - 1)

    def east(self, pos):
        return (pos[0] + 1, pos[1])

    def south(self, pos):
        return (pos[0], pos[1]+1)

    def west(self, pos):
        return (pos[0] - 1, pos[1])

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
            if self.map.hasGold():
                print('looking for solution...')
                solutionPath = self.findWay(self.map.myPos(), self.map.goldPos(), self.hasKey, self.hasAxe, self.hasStone)
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
                        pathToResource = self.findWay(self.map.myPos(), pos, self.hasKey, self.hasAxe, 0)
                        if pathToResource:
                            self.goAlong(pathToResource)
                    if resources:
                        break
            else:
                print('No solution')
                break

    def findWay(self, originPos, targetPos, key, axe, stone):
        map = self.mapProcess(self.map, key, axe, stone)
        print('processed map')
        print(map.printMap())
        stack = [([originPos], key, axe, stone, map)]
        went = set()
        while(stack):
            path, key, axe, stone, map = stack[0]
            stack = stack[1:]
            tilepos = path[-1]
            if tilepos == targetPos:
                return path

            walkable = {' ', 'O', 'k', 'a', 'o'}
            if key:
                walkable.add('-')
            if axe:
                walkable.add('T')
            if stone:
                walkable.add('~')


            tile = map.getTile(*tilepos)
            tileType = tile.getType()

            if tileType not in walkable:
                continue

            if tileType in 'koa~':
                myMap = map.copy()
                tile = myMap.getTile(*tilepos)
                if tileType == 'k':
                    key = True
                    tile.setType(' ')
                if tileType == 'o':
                    stone += 1
                    tile.setType(' ')
                if tileType == 'a':
                    axe = True
                    tile.setType(' ')
                if tileType == '~':
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

    def mapProcess(self, map, key, axe, stone):
        myMap = map.copy()
        resource = myMap.resourcePos()
        if map.hasGold():
            resource.append(map.goldPos())
        walkable = {'g', 'k', 'a', 'o', ' '}
        if key:
            walkable.add('-')
        if axe:
            walkable.add('T')
        stone += self.map.stonesOnGround()
        originPos = map.myPos()
        stack = [(originPos)]
        area = set()
        while(stack):
            x, y = stack.pop()
            if myMap.getTile(x, y).getType() not in walkable:
                continue
            if (x, y) in area:
                continue

            area.add((x,y))
            stack.append((x+1, y))
            stack.append((x-1, y))
            stack.append((x, y+1))
            stack.append((x, y-1))

        walkable.add('~')
        s = set()
        for x, y in resource:
            stack = [(x,y, stone)]
            walked = set()
            while(stack):
                x0, y0, tmpstone = stack.pop()
                if (x0, y0) in walked:
                    continue

                tileType = myMap.getTile(x0, y0).getType()
                if tileType not in walkable:
                    continue
                walked.add((x0,y0))
                if tileType == '~':
                    s.add((x0, y0))
                    if tmpstone == 1:
                        continue
                    else:
                        tmpstone -= 1
                if (x0, y0) in area:
                    break
                stack.append((x0, y0-1, tmpstone))
                stack.append((x0, y0+1, tmpstone))
                stack.append((x0-1, y0, tmpstone))
                stack.append((x0+1, y0, tmpstone))

        for x, y in myMap.ground:
            if myMap.getTile(x, y).getType() == '~' and (x, y) not in s:
                myMap.getTile(x, y).setType('*')
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

    def goAlong(self, path):
        head = path[0]
        if head != (self.map.myPos()):
            leadingPath = self.findWay(self.map.myPos(), head, self.hasKey, self.hasAxe, 0)
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
