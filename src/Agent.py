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

    def getType(self):
        return self.__type

    def setType(self, type):
        self.__type = type

class Map:
    def __init__(self):
        self.ground = dict()
        self.x = 0
        self.y = 0
        self.facing = 0
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
            # tile.walked()
            self.wentTile.add((x, y))
            tile.setType(' ')

        if type == 'g':
            self.hasgold = True

    def getTile(self, pos):
        if pos in self.ground:
            return self.ground[pos]
        else:
            return None

    def copy(self):
        newMap = Map()
        for tile in self.ground:
            x, y = tile
            type = self.ground[tile].getType()
            newMap.addTile(x, y, type)
        return newMap

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

    def setPos(self, pos):
        self.x = pos[0]
        self.y = pos[1]
        self.wentTile.add(pos)

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

    def surrondingType(self, pos):
        x, y = pos
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

    def setType(self, pos, type):
        self[pos].setType(type)

    def getType(self, pos):
        return self.ground[pos].getType()

    def distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

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

            tileType = map.getType(tilepos)

            if tileType not in walkable:
                continue

            if tileType in 'koa~':
                myMap = map.copy()
                if tileType == 'k':
                    key = True
                    myMap.setType(tilepos, ' ')
                if tileType == 'o':
                    stone += 1
                    myMap.setType(tilepos, ' ')
                if tileType == 'a':
                    axe = True
                    myMap.setType(tilepos, ' ')
                if tileType == '~':
                    stone -= 1
                    myMap.setType(tilepos, 'O')
            else:
                myMap = map

            if (tilepos, key, axe, stone, myMap) in went:
                continue
            went.add((tilepos, key, axe, stone, myMap))

            stack.append((path+[myMap.north(tilepos)], key, axe, stone, myMap))
            stack.append((path+[myMap.east(tilepos)], key, axe, stone, myMap))
            stack.append((path+[myMap.south(tilepos)], key, axe, stone, myMap))
            stack.append((path+[myMap.west(tilepos)], key, axe, stone, myMap))
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
            pos = stack.pop()
            if myMap[pos] not in walkable:
                continue
            if pos in area:
                continue

            area.add(pos)
            stack.append((myMap.north(pos)))
            stack.append((myMap.east(pos)))
            stack.append((myMap.south(pos)))
            stack.append((myMap.west(pos)))

        walkable.add('~')
        s = set()
        for resPos in resource:
            stack = [(resPos, stone)]
            walked = set()
            while(stack):
                pos , tmpstone = stack.pop()
                if pos in walked:
                    continue

                tileType = myMap[pos].getType()
                if tileType not in walkable:
                    continue
                walked.add(pos)
                if tileType == '~':
                    s.add(pos)
                    if tmpstone == 1:
                        continue
                    else:
                        tmpstone -= 1
                if pos in area:
                    break
                stack.append((myMap.north(pos), tmpstone))
                stack.append((myMap.east(pos), tmpstone))
                stack.append((myMap.south(pos), tmpstone))
                stack.append((myMap.west(pos), tmpstone))

        for pos in myMap.ground:
            if myMap[pos].getType() == '~' and pos not in s:
                myMap.setType(pos, '*')
        return myMap

    def expand(self):
        borderTiles = self.findBorderTiles()
        if borderTiles:
            borderPathes = self.findConsecutivePathes(borderTiles)
            self.goAlong([x for x in borderPathes])
        return len(borderTiles) != 0

    def findBorderTiles(self):
        pos = self.map.myPos()

        walkable = {' ', 'O', 'k', 'a', 'o'}
        if self.hasKey:
            walkable.add('-')
        if self.hasAxe:
            walkable.add('T')

        walked = [pos]
        stack = [pos]

        borderTile = []
        while(stack):
            pos = stack.pop()
            walked.append(pos)
            if self.map.getType(pos) not in walkable:
                continue
            north = self.map.north(pos)
            west = self.map.west(pos)
            south = self.map.south(pos)
            east = self.map.east(pos)

            if 'N' in self.map.surrondingType(pos):
                borderTile.append(pos)

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
                    pos1 = pathes[i][-1]
                    pos2 = pathes[j][0]
                    if self.map.distance(pos1, pos2) == 1:
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
        myPos = self.map.myPos()
        targetPos = pos
        d = self.map.distance(myPos,targetPos)
        myDirection = self.map.getFacing()

        if d > 1:
            raise Exception
        elif d == 0:
            return
        targetd = {( 0, -1): 0, #North
                   ( 1,  0): 1, #East
                   ( 0,  1): 2, #South
                   (-1,  0): 3} #West
        targetDirection = targetd[(targetPos[0]-myPos[0], targetPos[1]-myPos[1])]
        turn = targetDirection - myDirection


        if abs(turn) == 2:
            command += 'rr'
        elif turn == 1 or turn == -3:
            command += 'r'
        elif turn == 3 or turn == -1:
            command += 'l'

        targetType = self.map.getType(targetPos)
        if targetType == 'T':
            command += 'c'
            self.map.setType(targetPos, ' ')
        elif targetType == '-':
            command += 'u'
            self.map.setType(targetPos, ' ')
        elif targetType == '~':
            self.hasStone -= 1
            self.map.setType(targetPos, 'O')
        elif targetType == 'o':
            self.hasStone += 1
            self.map.setType(targetPos, ' ')
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
                self.map.setPos(targetPos)
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
