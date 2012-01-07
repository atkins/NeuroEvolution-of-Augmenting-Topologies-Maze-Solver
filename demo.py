import ne_mazePlayers
import ne_genetics
import ne_maze
import random
import time
import pickle

#Default Values
WIDTH = 20
HEIGHT = 20
STEPS = 200

population = ne_mazePlayers.loadState(12)
population[0].reset()

print "Welcome to the demonstration of Maze Solver 1.0"

WIDTH = int(raw_input('Please enter the width of the maze: '))
HEIGHT = int(raw_input('Please enter the height of the maze: '))
STEPS = int(raw_input('Please enter the number of turns to take: '))


m = ne_maze.Maze(WIDTH, HEIGHT)
finished = population[0].showMove(m,STEPS)

if finished:
        print "The maze was sucessfully solved."
else:
        print "The maze was not solved."
