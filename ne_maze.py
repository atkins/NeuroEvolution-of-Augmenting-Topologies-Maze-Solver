import random

rand = random.Random()
logging = False
DEFAULT_HEIGHT = 25
DEFAULT_WIDTH = 35
START_X = 0
START_Y = 0
JAGGED_FACTOR = 0.2
SPLIT_FACTOR = 0.05
DIE_FACTOR = 0.2

PASSABLE = '.'
IMPASSABLE = '@'
PLAYER = '\02'

PASS_VALUE = 1
IMPASS_VALUE = 0

def randBool():
    return rand.choice([True,False])

def randDirection(source = None):
    if (source == None):
        return rand.choice(['up','down','left','right'])
    if (source == 'up'):
        return rand.choice(['down','left','right'])
    if (source == 'down'):
        return rand.choice(['up','left','right'])
    if (source == 'left'):
        return rand.choice(['down','up','right'])
    if (source == 'right'):
        return rand.choice(['down','left','up'])

class Maze:
    def __init__(self, height = DEFAULT_HEIGHT, width = DEFAULT_WIDTH,
            jFactor = JAGGED_FACTOR, sFactor = SPLIT_FACTOR, dFactor = DIE_FACTOR):
        self.grid = []
        self.height = height
        self.width = width
        self.splitFactor = SPLIT_FACTOR
        self.jFactor = jFactor
        self.sFactor = sFactor
        self.dFactor = dFactor

        self.randGrid()

    def randGrid(self):
        for i in range(self.height):
            self.grid.append([False for x in range(self.width)])
        success = False
        while (not success):
            if (logging):
                print "Attempting to create a valid maze..."
            success = self.carveRandGrid()

    def carveRandGrid(self):
        self.carvers = []
        self.carvers.append(GridCarver(self))
        carvedExit = False
        i = 0

        while not carvedExit:
            i += 1
            r = rand.random()
            if (r < self.sFactor):
                p = rand.choice(self.carvers)
                self.carvers.append(GridCarver(self, p.x, p.y))
            for c in self.carvers:
                carvedExit = c.move()
                if (carvedExit):
                    break
            if (i > self.height * self.width):
                return False
        self.carvers = []
        self.grid[0][0] = True
        return True

    def countCarvers(self):
        i = 0
        for c in self.carvers:
            if (not c.dead):
                i += 1
        return i

    def display(self, playerY = -1, playerX = -1):
        for i in range(self.height):
            s = ''
            for j in range(self.width):
                if (i == playerY) and (j == playerX):
                    s += PLAYER
                elif (self.grid[i][j]):
                    s += PASSABLE
                else:
                    s += IMPASSABLE
            print s

    def vision(self, sight, y, x):
        d = []
        for i in range(-sight, sight+1):
            for j in range(-sight, sight+1):
                if (i != 0) or (j != 0):
                    if (y+i < 0) or (x+j < 0) or (y+i > self.height-1) or (x+j > self.width-1):
                        d.append(IMPASS_VALUE)
                    elif (self.grid[y+i][x+j]):
                        d.append(PASS_VALUE)
                    else:
                        d.append(IMPASS_VALUE)
        return d
        

class GridCarver:
    def __init__(self, maze, x = START_X, y = START_Y):
        self.x = x
        self.y = y
        #self.direction = randDirection()
        self.direction = 'right'
        self.maze = maze
        self.dead = False

    def move(self):
        if (self.dead):
            return False

        if (self.direction == 'up'):
            if (self.y > 0):
                self.y -= 1
            else:
                self.direction = 'down'
        elif (self.direction == 'down'):
            if (self.y < self.maze.height - 1):
                self.y += 1
            else:
                self.direction = 'up'
        elif (self.direction == 'left'):
            if (self.x > 0):
                self.x -= 1
            else:
                self.direction = 'right'
        elif (self.direction == 'right'):
            if (self.x < self.maze.width - 1):
                self.x += 1
            else:
                self.direction = 'left'

        """
        if (self.maze.grid[self.y][self.x]):
            r = rand.random()
            if (r < PLUG_FACTOR):
                self.maze.grid[self.y][self.x] = False
                self.direction = randDirection(self.direction)
                return False
        """

        self.maze.grid[self.y][self.x] = True

        if (self.y == self.maze.height - 1):
            return True

        r = rand.random()
        if (r < self.maze.dFactor):
            if (self.maze.countCarvers() > 1):
                self.dead = True
                return False

        r = rand.random()
        if (r < self.maze.jFactor):
            self.direction = randDirection()

        return False