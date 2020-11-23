import numpy as np
import matplotlib.pyplot as plt
#deap related imports
from deap import base
from deap import creator
from deap import tools
from deap import algorithms
import operator
from enum import Enum
from collections import namedtuple
import random
import time
import math

def Manhattan(source, target):
    """mahnattan distance between two coordinates tuples"""
    return abs(source[0]-target[0]) + abs(source[1]-target[1])

def display_labyrinth(grid, start_cell, end_cell, solution=None):
    """Display the labyrinth matrix and possibly the solution with matplotlib.
    Free cell will be in light gray.
    Wall cells will be in dark gray.
    Start and end cells will be in dark blue.
    Path cells (start, end excluded) will be in light blue.
    :param grid np.array: labyrinth matrix
    :param start_cell: tuple of i, j indices for the start cell
    :param end_cell: tuple of i, j indices for the end cell
    :param solution: list of successive tuple i, j indices who forms the path
    """
    grid = np.array(grid, copy=True)
    FREE_CELL = 19
    WALL_CELL = 16
    START = 0
    END = 0
    PATH = 2
    grid[grid == 0] = FREE_CELL
    grid[grid == 1] = WALL_CELL
    grid[start_cell] = START
    grid[end_cell] = END
    if solution:
        solution = solution[1:-1]
        for cell in solution:
            grid[cell] = PATH
    else:
        print("No solution has been found")
    plt.matshow(grid, cmap="tab20c")
    plt.show()
    

def solve_labyrinth(grid, start_cell, end_cell, max_time_s):
    """Attempt to solve the labyrinth by returning the best path found
    :param grid np.array: numpy 2d array
    :start_cell tuple: tuple of i, j indices for the start cell
    :end_cell tuple: tuple of i, j indices for the end cell
    :max_time_s float: maximum time for running the algorithm
    :return list: list of successive tuple i, j indices who forms the path
    """

    """ ----- CHROMOSOME INITIALISATION ----- """
    """ --- SIZE --- """
    #terrain shape
    h = grid.shape[0]
    w = grid.shape[1]
    # number of steps of the chromosome, M * N/2
    CHROMOSOME_LENGTH = math.ceil(h * w / 2)
    # if there is only 10% walls, we can aim better - the best opimized path (M+N as the max manhattan) [maybe too optimistic ?]
    #CHROMOSOME_LENGTH = math.ceil(h + w)

    """ --- ENCODING --- """
    #tuple that code the operations as (apply, str) representation to avoid creating classes for each direction
    Code = namedtuple("Code", ["apply", "str"])

    #operations as (apply, str) tuple. apply on the tuple representing the current case, yield the next case
    DIRECTIONS = {
        0: Code(lambda caseTuple : (caseTuple[0]-1, caseTuple[1]), "left"),
        1: Code(lambda caseTuple : (caseTuple[0]+1, caseTuple[1]), "right"),
        2: Code(lambda caseTuple : (caseTuple[0], caseTuple[1]-1), "top"),
        3: Code(lambda caseTuple : (caseTuple[0], caseTuple[1]+1), "bottom")
    }
    ENCODING_MIN, ENCODING_MAX = 0, len(DIRECTIONS)-1

    def chromosome_as_cells(individual):
        """ Return the chromosome as a list of successive cells - stop if "end" is found"""
        path = [start_cell]
        for code in _decode(individual):
            path.append(code.apply(path[-1])) #append each move to the last case of the list (=current case)
            if path[-1] == end_cell :
                return path
        return path

    def _parse_code(code):
        """ Convert bit string to a Code namedtuple """
        return DIRECTIONS[code]
        
    def _decode(individual):
        """ Parse each code of the full chromosome (aka individual) """
        return [_parse_code(gene) for gene in individual]

    def display_chromosome(individual):
        """ Convert chromosome to a readable format (Path of cells : (0,0)->(1,1)->...) """
        return " -> ".join(str(cell) for cell in chromosome_as_cells(individual))

    def valid(case):
        """ return wether a case is valid (in board, not a wall) """
        x,y = case[0], case[1]
        return x in range(w) and y in range(h) and grid[x][y] == 0


    """ --- FITNESSES --- """

    def eval_and_correct(individual, target):
        """ compute the path of the chromosome, do on-the-fly corrections """
        #init
        currentCase = start_cell
        path =  [start_cell]
        idealistic = Manhattan(start_cell, end_cell)
        minManhattan = idealistic
        
        #iterate over every gene of the chromosome, keep index for eventual correction
        for i in range(len(individual)):
            gene = individual[i]

            nextCase = _parse_code(gene).apply(currentCase)
            while not valid(nextCase):
                #correct code of chromosome randomly
                individual[i] = random.randint(ENCODING_MIN, ENCODING_MAX)
                nextCase = _parse_code(individual[i]).apply(currentCase)

            currentCase = nextCase
            currentManhattan = Manhattan(currentCase, target)
            if(currentManhattan == 0):
                #we found the end - stop here !
                return 0

            path.append(currentCase)
            if(currentManhattan < minManhattan):
                minManhattan = currentManhattan
                distinctCells = len(set(path))

        #return the minimal mahnattan value (the "closer" case of the end with the least amount of steps") as fitness value
        #with its associated penalties (ex : Did we come back on an already seen case ?)
        return minManhattan + abs(idealistic - distinctCells)

    toolbox = base.Toolbox()
    def fitness(individual, target):
        """ Fitness of the chromosome with on-the-fly correction of failing genes """
        return (eval_and_correct(individual, target),)

    toolbox.register("fitness", fitness)
    #fitness tries to reach 0 (0 = Reached goal)
    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMin)


    """ --- MUTATIONS AND SELECTION --- """
    toolbox.register("mate", tools.cxOnePoint)
    toolbox.register("mutate", tools.mutUniformInt, low=ENCODING_MIN, up=ENCODING_MAX, indpb=0.1)
    toolbox.register("select", tools.selTournament)

    """ --- POPULATION INITIALISATION --- """
    toolbox.register("init_gene", random.randint, ENCODING_MIN, ENCODING_MAX)
    toolbox.register("init_individual", tools.initRepeat, creator.Individual, toolbox.init_gene, CHROMOSOME_LENGTH)
    toolbox.register("init_population", tools.initRepeat, list, toolbox.init_individual)

    def evaluate_population(population, target):
        for ind in population:
            ind.fitness.values = toolbox.fitness(ind, target)
    toolbox.register("evaluate", evaluate_population)

    def find_winners(population):
        winners = [i for i in population if i.fitness.values[0] == 0]
        return winners

    TARGET = end_cell
    MUTPB = 0.3
    CXPB = 0.7
    tournSize = 100
    solution = None

    #init pop
    pop = toolbox.init_population(n=200)
    #give base fitness
    toolbox.evaluate(pop, TARGET)
    #init time
    start = time.time()
    timePassed = 0
    iterations = 0

    #while loop
    while timePassed < max_time_s and len(find_winners(pop)) <= 0:
        print(f"\r iteration {iterations}", end="")
        # --- SEL ---
        offspring = toolbox.select(pop, len(pop), tournSize)
        offspring = list(map(toolbox.clone, offspring))

        # --- MATE&MUTATE ---
        #mate
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
        #mutate
        for mutant in offspring:
            if random.random() < MUTPB:
                toolbox.mutate(mutant)

        #remplace pop
        pop = offspring
        #pop eval
        toolbox.evaluate(pop, TARGET)
        # Search for the solution
        fitnesses = [ind.fitness.values[0] for ind in pop]
        min_fit = min(fitnesses)
        best = pop[fitnesses.index(min_fit)]
        if not solution or best.fitness.values[0] < solution.fitness.values[0]:
            solution = best

        #calculate time & iterations
        timePassed = time.time() - start
        iterations += 1

    winner = solution if solution is not None else find_winners(pop)
    if winner :
        print(f"\nfound in {iterations} iterations and {timePassed}s")
        print(f"Path found : {chromosome_as_cells(winner)}")
        return chromosome_as_cells(winner)
    return None