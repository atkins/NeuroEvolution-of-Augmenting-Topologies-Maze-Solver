import random

INPUT_NODES = 24
OUTPUT_NODES = 4

TOGGLE_ENABLED_CHANCE = 0.01
ADD_CONNECTION_CHANCE = 0.08
ADD_NODE_CHANCE = 0.005
CHANGE_WEIGHT_CHANCE = 0.08
CHANGE_WEIGHT_MAGNITUDE = 0.3
AVERAGE_CROSSOVER_WEIGHTS = True
INHERIT_DISJOINT_CHANCE = 0.9
ONLY_SINGLE_MUTATIONS = False
LIMIT_WEIGHTS = False

DISJOINT_DWEIGHT = 1.0
WEIGHT_DWEIGHT = 2.0
USE_PERCENT_DISJOINT = False

ACTIVATION_SPREAD = 0.25

rand = random.Random()
innovations = 0
totalNodes = INPUT_NODES + OUTPUT_NODES
geneMappings = {}

class Node:
    def __init__(self, number, active = True):
        self.number = number
        self.newSum = 0
        self.oldSum = 0
	self.active = active

    def output(self):
        return self.oldSum

    def input(self, magnitude):
        self.newSum += magnitude

    def timestep(self):
        if (self.active):
            self.oldSum = self.activationFunction(self.newSum)
        else:
            self.oldSum = self.newSum
        self.newSum = 0

    def wipe(self):
        self.oldSum = 0
        self.newSum = 0

    def activationFunction(self, sum):
        return (2.0 / (1 + 2 ** (-sum/ACTIVATION_SPREAD))) - 1

class Gene:
    def __init__(self, number, parents = None):
        if (parents != None):
            if (AVERAGE_CROSSOVER_WEIGHTS):
                self.weight = (parents[0].weight + parents[1].weight)/2
            else:
                pick = rand.randint(0,1)
                self.weight = parents[pick].weight
            pick = rand.randint(0,1)
            self.enabled = parents[pick].enabled

        else:
            self.weight = rand.uniform(-1,1)
            self.enabled = True

        self.number = number

    def attachGene(self, network):
        n = network.nodeByNum(geneMappings[self.number][0])
        if (n == None):
            n = Node(geneMappings[self.number][0])
            network.nodes.append(n)
        self.startNode = n
        
        n = network.nodeByNum(geneMappings[self.number][1])
        if (n == None):
            n = Node(geneMappings[self.number][1])
            network.nodes.append(n)
        self.endNode = n

    def mapGene(self, startNode, endNode):
        geneMappings[self.number] = (startNode, endNode)

    def timestep(self):
        if (self.enabled):
            impulse = self.startNode.output()
            impulse *= self.weight
            self.endNode.input(impulse)

    def toggle(self):
        self.enabled = not self.enabled
    
    def mutateWeight(self):
        self.weight += rand.uniform(-CHANGE_WEIGHT_MAGNITUDE,
            CHANGE_WEIGHT_MAGNITUDE)
        if (LIMIT_WEIGHTS) & (self.weight > 1):
            self.weight = 1
        elif (LIMIT_WEIGHTS) & (self.weight < -1):
            self.weight = -1

class Network:
    def __init__(self, parents = None):
        self.genes = []
        self.nodes = []

        for i in range(INPUT_NODES + OUTPUT_NODES):
            self.nodes.append(Node(i, False))

        if (parents != None):
            self.crossover(parents)
        else:
            for i in range(INPUT_NODES * OUTPUT_NODES):
                self.addGene(Gene(i))
        self.mutate()
            
    def timestep(self, input = None):
        if (input):
            self.input(input)

        for n in self.nodes:
            n.timestep()
        for g in self.genes:
            g.timestep()

        return self.output()

    def wipe(self):
        for n in self.nodes:
            n.wipe()        

    def input(self, invals):
        for i in range(INPUT_NODES):
            self.nodes[i].input(invals[i])

    def output(self):
        outvals = []
        for i in range(OUTPUT_NODES):
            outvals.append(self.nodes[i+INPUT_NODES].output())
        return outvals

    def nodeByNum(self, number):
        for n in self.nodes:
            if (n.number == number):
                return n
        return None

    def addGene(self, gene):
        self.genes.append(gene)
        gene.attachGene(self)

    def scrambleWeights(self):
        for g in genes:
            g.weight = rand.uniform(-1,1)

    def distance(self, net):
        disjoint = 0.0
        weightError = 0.0
        matchedWeights = 0.0

        for g0 in self.genes:
            g1 = net.geneByNumber(g0.number)
            if (g1 == None):
                disjoint += 1
            else:
                wdiff = g1.weight - g0.weight
                if (wdiff < 0):
                    wdiff *= -1
                weightError += wdiff
                matchedWeights += 1

        for g1 in net.genes:
            g0 = self.geneByNumber(g1.number)
            if (g1 == None):
                disjoint += 1

        if (USE_PERCENT_DISJOINT):
            distance = disjoint / (disjoint + matchedWeights) * DISJOINT_DWEIGHT
        else:
            distance = disjoint * DISJOINT_DWEIGHT

        if (matchedWeights != 0):
            distance += weightError / matchedWeights * WEIGHT_DWEIGHT

        return distance

    def geneByNumber(self, i):
        for g in self.genes:
            if (i == g.number):
                return g
        return None

    def crossover(self, parents):
        for g0 in parents[0].genes:
            g1 = parents[1].geneByNumber(g0.number)

            if (g1 == None):
                if (rand.random() < INHERIT_DISJOINT_CHANCE):
                    gene = Gene(g0.number, (g0, g0))
                    self.addGene(gene)
            else:
                gene = Gene(g0.number, (g0, g1))
                self.addGene(gene)

        for g1 in parents[1].genes:
            g0 = parents[0].geneByNumber(g1.number)

            if (g0 == None):
                if (rand.random() < INHERIT_DISJOINT_CHANCE):
                    gene = Gene(g1.number, (g1, g1))
                    self.addGene(gene)

    def mutate(self):
        if (rand.random() < CHANGE_WEIGHT_CHANCE):
            rand.choice(self.genes).mutateWeight()

            #Weight changes do not count as the single allowed mutation
            #when ONLY_SINGLE_MUTATIONS is True.

        if (rand.random() < ADD_NODE_CHANCE):
            newNode = Node(globals()['totalNodes'])
            globals()['totalNodes'] += 1

            self.nodes.append(newNode)
            split = rand.choice(self.genes)
            split.enabled = False

            geneMappings[globals()['innovations']] = (split.startNode.number, newNode.number)
            g1 = Gene(globals()['innovations'])
            g1.weight = 1
            globals()['innovations'] += 1

            geneMappings[globals()['innovations']] = (newNode.number, split.endNode.number)
            g2 = Gene(globals()['innovations'])
            g2.weight = split.weight
            globals()['innovations'] += 1

            self.addGene(g1)
            self.addGene(g2)
            
            if (ONLY_SINGLE_MUTATIONS):
                return None

        if (rand.random() < ADD_CONNECTION_CHANCE):
            start = rand.randint(0,len(self.nodes))
            end = rand.randint(0,len(self.nodes))

            #If it's already present in the network, ignore it.
            present = False
            for g in self.genes:
                if (g.startNode.number == start):
                    if (g.endNode.number == end):
                        present = True
                        break

            #If it's a new innovation, map it.
            if (not present) & ((start,end) not in geneMappings.values()):
                gene = Gene(globals()['innovations'])
                globals()['innovations'] += 1
                gene.mapGene(start, end)
                self.addGene(gene)
            #If it's an old innovation, find its number and add it to the network.
            elif (not present):
                for k in range(globals()['innovations']):
                    if (geneMappings[k] == (start, end)):
                        gene = Gene(k)
                        self.addGene(gene)
                        break
            if (ONLY_SINGLE_MUTATIONS):
                return None

        if (rand.random() < TOGGLE_ENABLED_CHANCE):
            rand.choice(self.genes).toggle()

    def display(self):
        for g in self.genes:
            print ("Gene " + repr(g.number) + ": \t" + repr(g.startNode.number) + " -> " +
                repr(g.endNode.number) + ", \t" + repr(g.weight) + " \tEnabled: " + repr(g.enabled))


def initializeGeneMappings():
    for i in range(INPUT_NODES):
        for j in range(OUTPUT_NODES):
            geneMappings[globals()['innovations']] = (i, j + INPUT_NODES)
            globals()['innovations'] += 1

initializeGeneMappings()

def resetState(inputNodes = INPUT_NODES, outputNodes = OUTPUT_NODES):
    globals()['INPUT_NODES'] = inputNodes
    globals()['OUTPUT_NODES'] = outputNodes
    globals()['geneMappings'] = {}
    globals()['innovations'] = 0
    initializeGeneMappings()
