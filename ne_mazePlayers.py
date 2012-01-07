import ne_genetics
import ne_maze
import random
import time
import pickle

#Network handling and topology
DETERMINISTIC_MOVES = False
VISION = 2
OUTPUTS = 4

#Tournament Control
MAX_STEPS = 100
RUNS_PER_ROUND = 5
ROUNDS_PER_MAZE = 6
DEFAULT_HEIGHT = 25
DEFAULT_WIDTH = 35

#Multi-Tournament Control
NUM_MAZES = 4
JFACTORS = (0.1,0.2,0.3,0.4)
SFACTORS = (0.1,0.07,0.04,0.0)
DFACTORS = (0.4,0.3,0.2)

#Fitness parameters
MOVE_PENALTY = 0
WALL_PENALTY = 5
ROW_REWARD = 10
FINISH_REWARD = 200

#Population/Speciation Control
KEEP_BEST = True
ALLOW_AUTOGAMY = True
DEFAULT_POP_SIZE = 30
COMPATABILITY_THRESHOLD = 2.0
COMPATABILITY_THRESHOLD_MODIFIER = 0.4
TARGET_SPECIES = 5

#Mutation parameters
DYNAMIC_MUTATION_RATES = False
MUTATOR_MULTIPLIER = 0.1
MUTATOR_SPREAD = 0.05

#I/O parameters
LOGGING = False
FPS = 3
SAVE_PREFIX = "ne_mazepop"

ne_genetics.resetState((2*VISION + 1)**2 - 1, OUTPUTS)

rand = random.Random()

class Player:
    def __init__(self, parents = None):
        if (not parents):
            self.net = ne_genetics.Network()
        else:
            self.net = ne_genetics.Network((parents[0].net, parents[1].net))
        self.species = -1
        self.fitness = 0
        self.reset()

    def respond(self, inputs):
        out = self.net.timestep(inputs)
        if (DETERMINISTIC_MOVES):
            highest = 0
            for i in range(1, OUTPUTS):
                if (out[i] > out[highest]):
                    highest = i
            return highest

        s = min(out)
        for i in range(OUTPUTS):
            out[i] -= s
        s = sum(out)
        if (s == 0):
            for i in range(OUTPUTS):
                out[i] = 1.0 / OUTPUTS
        else:
            for i in range(OUTPUTS):
                out[i] /= s

        r = rand.random()
        s = 0
        for i in range(OUTPUTS):
            s += out[i]
            if (r < s):
                return i

    def timestep(self, maze):
        self.fitness -= MOVE_PENALTY
        inputs = maze.vision(VISION, self.y, self.x)
        response = self.respond(inputs)
        #up
        if (response == 0):
            if (inputs[2*(VISION**2) - 1] == 1):
                self.y -= 1
            else:
                self.fitness -= WALL_PENALTY
        #down
        if (response == 1):
            if (inputs[2*VISION*(2+VISION)] == 1):
                self.y += 1
                if (self.y > self.bestY):
                    self.bestY = self.y
                    self.fitness += ROW_REWARD
            else:
                self.fitness -= WALL_PENALTY
        #left
        if (response == 2):
            if (inputs[2*(VISION**2)+2*VISION-1] == 1):
                self.x -= 1
            else:
                self.fitness -= WALL_PENALTY
        #right
        if (response == 3):
            if (inputs[2*VISION*(1+VISION)] == 1):
                self.x += 1
            else:
                self.fitness -= WALL_PENALTY

        if (self.y == maze.height - 1):
            self.fitness += FINISH_REWARD
            return True

        return False


    def showMove(self, maze, n = 1):
        for i in range(n):
            done = self.timestep(maze)
            maze.display(self.y, self.x)
            time.sleep(1.0/FPS)
            print ""
            if (done):
                return True
        return False

    def reset(self, y = ne_maze.START_Y, x = ne_maze.START_X):
        self.y = y
        self.x = x
        self.bestY = 0
        self.net.wipe()

    def navigate(self, maze, startPos = (ne_maze.START_Y,ne_maze.START_X)):
        self.y = startPos[0]
        self.x = startPos[1]
        for i in range(MAX_STEPS):
            if (self.timestep(maze)):
                break

class Population:
    def __init__(self, size = DEFAULT_POP_SIZE):
        self.size = size
        self.players = [Player() for i in range(size)]
        self.numSpecies = 1
        self.extinctSpecies = 0
        self.compatabilityThreshold = (COMPATABILITY_THRESHOLD - (TARGET_SPECIES-1)
                * COMPATABILITY_THRESHOLD_MODIFIER)
        for p in self.players:
            p.species = 0
        self.speciesRepresentatives = []
        self.speciesRepresentatives.append(rand.choice(self.players).net)
        self.lastHigh = 0

    def __getitem__(self, i):
        return self.players[i]

    def tournament(self, t = 1, mazeDimensions = (DEFAULT_HEIGHT, DEFAULT_WIDTH), showReport = True):
        startTime = time.time()
        while (time.time() - startTime < t):
            print "----Running Tournament----"
            m = ne_maze.Maze(mazeDimensions[0], mazeDimensions[1])
            if (showReport):
                print "Maze for this tournament:"
                m.display()
            for j in range(ROUNDS_PER_MAZE):
                self.oneRound(m)
            if (showReport):
                print "Highest Fitness:"
                print self.players[0].fitness

        for p in self.players:
            p.reset()

    def multiTourny(self, t = 1, mazeDimensions = (DEFAULT_HEIGHT, DEFAULT_WIDTH), numMazes = NUM_MAZES, showReport = True):
        startTime = time.time()
        while (time.time() - startTime < t):
            print "----Running multi-tournament----"
            M = []
            for i in range(numMazes):
                M.append(ne_maze.Maze(mazeDimensions[0], mazeDimensions[1], rand.choice(JFACTORS),
                    rand.choice(SFACTORS), rand.choice(DFACTORS)))
                if (showReport):
                    print "Maze " + repr(i) + ":"
                    M[i].display()
            for j in range(ROUNDS_PER_MAZE):
                for m in M:
                    self.oneRound(m, False)
                high = self.breedAll()
                if (showReport):
                    print "High fitness = " + repr(high)

        for p in self.players:
            p.reset()
            

    def oneRound(self, maze, breed = True):
        for p in self.players:
            p.fitness = 0
            for n in range(RUNS_PER_ROUND):
                p.reset()
                p.navigate(maze)
        if (breed):
            self.breedAll()
            

    def breedAll(self):
        fitnesses = [g.fitness for g in self.players]
        if (LOGGING):
            print "Fitnesses: " + repr(fitnesses)

        if (KEEP_BEST):
            bestPlayer = 0
            for i in range(1, self.size):
                if (fitnesses[i] > fitnesses[bestPlayer]):
                    bestPlayer = i
            if (LOGGING):
                print "Keeping player " + repr(bestPlayer)

        minFitness = min(fitnesses)
        for i in range(self.size):
            fitnesses[i] -= minFitness

        fitnesses = self.shareFitnesses(fitnesses)

        s = sum(fitnesses)
        if (s == 0):
            return None

        fitnesses[0] = fitnesses[0]/s
        for i in range(1,self.size):
            fitnesses[i] = fitnesses[i]/s + fitnesses[i-1]

        if (LOGGING):
            print "Modified Fitnesses: " + repr(fitnesses)

        players = []
        if (KEEP_BEST):
            players.append(self.players[bestPlayer])
            for i in range(self.size - 1):
                players.append(self.oneChild(fitnesses))
        else:
            for i in range(self.size):
                players.append(self.oneChild(fitnesses))

        for p in players:
            self.speciate(p)
        self.players = players
        self.checkExtinction()

        if (DYNAMIC_MUTATION_RATES):
            self.changeMutationRates()

        self.lastHigh = self.players[0].fitness

        return self.lastHigh

    def shareFitnesses(self, fit):
        for i in range(self.size):
            fit[i] /= self.countInSpecies(self.players[i].species)
        return fit

    def countInSpecies(self, n):
        count = 0.0
        for i in range(self.size):
            if (self.players[i].species == n):
                count += 1
        return count

    def checkExtinction(self):
        for i in range(self.numSpecies):
            if (self.speciesRepresentatives[i] != None):
                if (self.countInSpecies(i) == 0):
                    self.speciesRepresentatives[i] = None
                    self.extinctSpecies += 1

    def oneChild(self, fit):
        r = rand.random()
        for i in range(self.size):
            if (r < fit[i]):
                if (LOGGING):
                    print "New Child: Parent 1 is player " + repr(i)
                parent1 = self.players[i]
                break

        r = rand.random()
        for j in range(self.size):
            if (r < fit[j]):
                if (LOGGING):
                    print "           Parent 2 is player " + repr(j)
                parent2 = self.players[j]
                break

        while (not ALLOW_AUTOGAMY) and (parent1 == parent2):
            r = rand.random()
            for j in range(self.size):
                if (r < fit[j]):
                    parent2 = self.players[j]
                    break

        return Player((parent1, parent2))

    def speciate(self, player):
        for i in range(self.numSpecies):
            if ((self.speciesRepresentatives[i] != None) and
                    (player.net.distance(self.speciesRepresentatives[i]) < self.compatabilityThreshold)):
                player.species = i
                break
        if (player.species == -1):
            player.species = self.numSpecies
            self.numSpecies += 1
            self.speciesRepresentatives.append(player.net)
            self.compatabilityThreshold = (COMPATABILITY_THRESHOLD -
                    (TARGET_SPECIES - self.numSpecies + self.extinctSpecies) * COMPATABILITY_THRESHOLD_MODIFIER)

    def changeMutationRates(self):
        high = self.players[0].fitness
        if (self.lastHigh == 0):
            change = (self.lastHigh - high + 0.0)
        else:
            change = (self.lastHigh - high + 0.0) / self.lastHigh
        m = mutatorFunction(change)
        ne_genetics.TOGGLE_ENABLED_CHANCE *= m
        ne_genetics.ADD_CONNECTION_CHANCE *= m
        ne_genetics.ADD_NODE_CHANCE *= m
        ne_genetics.CHANGE_WEIGHT_CHANCE *= m


def mutatorFunction(x):
        m = MUTATOR_MULTIPLIER
        s = MUTATOR_SPREAD
        if (x < 0):
            x *= -1
        return 4 * ((1+m) - 1/(1+m)) * 3**(-x/s) / (1+3**(-x/s))**2 + 1 / (1+m)

def saveState(pop, i):
    f = open(SAVE_PREFIX + repr(i), 'w')
    stuff = (pop, ne_genetics.geneMappings)
    pickle.dump(stuff, f)

def loadState(i):
    f = open(SAVE_PREFIX + repr(i))
    stuff = pickle.load(f)
    ne_genetics.geneMappings = stuff[1]
    return stuff[0]

def resetParameters():
    ne_genetics.resetState((2*VISION + 1)**2 - 1, OUTPUTS)