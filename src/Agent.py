import socket, time, argparse
from functools import reduce

SIGHT = 5
NORTH = 0
EAST  = 1
SOUTH = 2
WEST  = 3

class Map:
    def __init__(self):
        self.ground = dict()
        self.facing = NORTH
        self.goldpos = None
        self.pos = (0, 0)

    def __getitem__(self, item):
        return self.ground[item]

    def __setitem__(self, key, value):
        self.ground[key] = value

    def __contains__(self, item):
        return item in self.ground

    def __iter__(self):
        for x in self.ground:
            yield x

    def addTile(self, pos, type):
        self[pos] = type

        northTile = Map.north(pos)
        eastTile = Map.east(pos)
        southTile = Map.south(pos)
        westTile = Map.west(pos)
        if northTile not in self:
            self[northTile] = 'N'

        if eastTile not in self:
            self[eastTile] = 'N'

        if southTile not in self:
            self[southTile] = 'N'

        if westTile not in self:
            self[westTile] = 'N'

        if type == '^':
            self.setType(pos, ' ')

        if type == 'g':
            self.goldpos = pos

    def copy(self):
        newMap = Map()
        newMap.ground = self.ground.copy()
        return newMap

    def printMap(self):
        xlist, ylist = zip(*self)
        xmin,xmax,ymin,ymax = min(xlist), max(xlist), min(ylist), max(ylist)
        ret = ''.join([str(x%10) for x in range(xmin-1, xmax+1)])
        for i in range(ymin, ymax+1):
            ret += '\n'+str(i%10)
            for j in range(xmin, xmax+1):
                if (j, i) in self:
                    if self.myPos() == (j, i):
                        direction = {0:'^', 1:'>', 2:'v', 3:'<'}
                        ret += direction[self.getFacing()]
                    else:
                        ret += self[(j,i)]
                else:
                    ret += '?'
        return ret

    def myPos(self):
        return self.pos

    def insertScope(self, scope):
        turnedMap = self.turnMapToNorth(scope)
        x, y = self.myPos()
        for i in range(SIGHT):
            for j in range(SIGHT):
                self.addTile((x + j - SIGHT//2, y + i - SIGHT//2), turnedMap[i][j])

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
        self.pos = pos

    def setFacing(self, facing):
        self.facing = facing%4

    def getFacing(self):
        return self.facing

    def hasGold(self):
        return self.goldpos != None

    def goldPos(self):
        return self.goldpos

    def resourcePos(self):
        return [x for x in self if self[x] in 'kao']

    def stonesOnGround(self):
        return len([x for x in self if self[x] == 'o'])

    def surrondingType(self, pos):
        x, y = pos
        return set([self[(i,j)] for i in range(x-SIGHT//2, x+SIGHT//2 +1)
                                for j in range(y-SIGHT//2, y+SIGHT//2 +1)
                                if (i,j) in self])

    def setType(self, pos, type):
        self[pos] = type

    def getType(self, pos):
        return self.ground[pos]

    def north(pos):
        return (pos[0], pos[1] - 1)

    def east(pos):
        return (pos[0] + 1, pos[1])

    def south(pos):
        return (pos[0], pos[1]+1)

    def west(pos):
        return (pos[0] - 1, pos[1])

    def distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def directionDiff(originPos, targetPos, facing):
        targetd = {( 0, -1): NORTH,
                   ( 1,  0): EAST,
                   ( 0,  1): SOUTH,
                   (-1,  0): WEST}
        return targetd[(targetPos[0]-originPos[0], targetPos[1]-originPos[1])] - facing

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
                    self.goAlong(solutionPath)
                    print('Victory')
                    print('command counter: ',self.commandCounter)
                    break
            print('no solution, expand')
            hasExpand = self.expand()
            if hasExpand:
                while(self.expand()):
                    if self.collectResource():
                        break
            else:
                print('No solution')
                break

    def collectResource(self):
        resources = self.map.resourcePos()
        if resources:
            pathes = self.findConsecutivePathes(resources)
            for path in pathes:
                self.goAlong(path)
        return len(resources) != 0

    def findWay(self, originPos, targetPos, key, axe, stone):
        map = self.mapProcess(self.map, key, axe, stone)
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

            stack.append((path+[Map.north(tilepos)], key, axe, stone, myMap))
            stack.append((path+[Map.east(tilepos)], key, axe, stone, myMap))
            stack.append((path+[Map.south(tilepos)], key, axe, stone, myMap))
            stack.append((path+[Map.west(tilepos)], key, axe, stone, myMap))
        return []

    def mapProcess(self, map, key, axe, stone):
        myMap = map.copy()
        resource = myMap.resourcePos()
        if map.hasGold():
            resource.append(map.goldPos())
        stone += self.map.stonesOnGround()
        originPos = map.myPos()

        walkable = {'g', 'k', 'a', 'o', ' '}
        if key:
            walkable.add('-')
        if axe:
            walkable.add('T')

        area = self.connectedTile(originPos, myMap, walkable)

        walkable.add('~')
        s = set()
        for resPos in resource:
            queue = [(resPos, stone)]
            walked = set()
            while(queue):
                pos , tmpstone = queue[0]
                queue = queue[1:]
                if pos in walked:
                    continue

                if myMap[pos] not in walkable:
                    continue
                walked.add(pos)
                if myMap[pos] == '~':
                    s.add(pos)
                    if tmpstone == 1:
                        continue
                    else:
                        tmpstone -= 1
                if pos in area:
                    break
                queue.append((Map.north(pos), tmpstone))
                queue.append((Map.east(pos), tmpstone))
                queue.append((Map.south(pos), tmpstone))
                queue.append((Map.west(pos), tmpstone))

        for pos in myMap:
            if myMap[pos] == '~' and pos not in s:
                myMap.setType(pos, '*')
        return myMap

    def connectedTile(self, originPos, map, walkable):
        stack = [(originPos)]
        area = set()
        while(stack):
            pos = stack.pop()
            if map[pos] not in walkable:
                continue
            if pos in area:
                continue

            area.add(pos)
            stack.append((Map.north(pos)))
            stack.append((Map.east(pos)))
            stack.append((Map.south(pos)))
            stack.append((Map.west(pos)))
        return area

    def expand(self):
        borderTiles = self.findBorderTiles()
        if borderTiles:
            borderPathes = self.findConsecutivePathes(borderTiles)[0]
            self.goAlong([x for x in borderPathes])
        return len(borderTiles) != 0

    def findBorderTiles(self):
        pos = self.map.myPos()

        walkable = {' ', 'O', 'k', 'a', 'o'}
        if self.hasKey:
            walkable.add('-')
        if self.hasAxe:
            walkable.add('T')

        walked = set()
        stack = [pos]

        borderTile = []
        while(stack):
            pos = stack.pop()

            if pos in walked:
                continue
            walked.add(pos)
            if self.map[pos] not in walkable:
                continue
            if 'N' in self.map.surrondingType(pos):
                borderTile.append(pos)
            stack.append(Map.north(pos))
            stack.append(Map.west(pos))
            stack.append(Map.south(pos))
            stack.append(Map.east(pos))
        return borderTile

    def findConsecutivePathes(self, tiles):
        pathes = [[x] for x in tiles]
        while(True):
            flag = False
            for i in range(len(pathes)):
                for j in range(len(pathes)):
                    if i == j:
                        continue
                    elif Map.distance(pathes[i][-1], pathes[j][0]) == 1:
                        pathes[i] += pathes[j]
                        pathes = pathes[:j] + pathes[j+1:]
                        flag = True
                        break
                    elif Map.distance(pathes[j][-1], pathes[i][0]) == 1:
                        pathes[j] += pathes[i]
                        pathes = pathes[:i] + pathes[i+1:]
                        flag = True
                        break
                if flag:
                    break
            if flag:
                continue
            break
        return [path for path in pathes if len(path) == max([len(path) for path in pathes])]

    def goAlong(self, path):
        head = path[0]
        if head != self.map.myPos():
            leadingPath = self.findWay(self.map.myPos(), head, self.hasKey, self.hasAxe, 0)
            if leadingPath:
                path = leadingPath[:-1] + path
        if path[0] == self.map.myPos():
            for tile in path[1:]:
                self.step(tile)

    def step(self, targetPos):
        command = ''
        myPos = self.map.myPos()

        if Map.distance(myPos,targetPos) != 1:
            raise Exception

        turn = Map.directionDiff(myPos, targetPos, self.map.getFacing())

        if abs(turn) == 2:
            command += 'rr'
        elif turn == 1 or turn == -3:
            command += 'r'
        elif turn == 3 or turn == -1:
            command += 'l'

        targetType = self.map[targetPos]
        if targetType in 'kaoT-~':
            if targetType == 'T':
                command += 'c'
            elif targetType == '-':
                command += 'u'
            elif targetType == '~':
                self.hasStone -= 1
            elif targetType == 'o':
                self.hasStone += 1
            elif targetType == 'a':
                self.hasAxe = True
            elif targetType == 'k':
                self.hasKey = True
            self.map.setType(targetPos, ' ')

        command += 'f'
        for c in command:
            if c == 'r':
                self.map.setFacing(self.map.getFacing()+1)
            elif c == 'l':
                self.map.setFacing(self.map.getFacing()-1)
            elif c == 'f':
                self.map.setPos(targetPos)
            self.commandCounter += 1
            self.pipe.send(c)
            print(self.map.printMap())

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
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, help='port number of server')
    args = parser.parse_args()
    beginTime = time.time()
    a = Agent(args.p)
    a.start()
    endTime = time.time()
    print('running time(s):', endTime - beginTime)
