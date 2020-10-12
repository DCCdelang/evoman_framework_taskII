# framework
import sys
sys.path.insert(0, 'evoman')
from environment import Environment
from demo_controller import player_controller
from player import Player
from sensors import *

# imports other libs
import time
import numpy as np
from math import fabs,sqrt
import glob, os
import neat
import visualize
import pickle

os.environ["PATH"] += os.pathsep + 'D:/Program Files (x86)/Graphviz2.38/bin/'


experiment_name = 'multi_demo_neat_easy'
if not os.path.exists(experiment_name):
    os.makedirs(experiment_name)

# initializes simulation in multi evolution mode, for multiple static enemies.

EASY = [1,2,5,8]
HARD = [3,4,6,7]
ALL = [1,2,3,4,5,6,7,8]

env = Environment(experiment_name=experiment_name,
                  enemies=ALL,
                  multiplemode="yes",
                  playermode="ai",
                  # player_controller=player_controller(0),
                  enemymode="static",
                  level=2,
                  speed="fastest")

# default environment fitness is assumed for experiment

env.state_to_log() # checks environment state

####   Optimization for controller solution (best genotype-weights for phenotype-network): Ganetic Algorihm    ###

ini = time.time()  # sets time marker

# genetic algorithm params

run_mode = 'test' # train or test


np.random.seed(420)

GEN = 30
MAXFIT = -10
TOTALGAMES = 0

# Main evaluation function
def eval_genome(genomes,config):
    global TOTALGAMES
    global MAXFIT
    nets = []
    ge = []

    # Loop for all genomes in one generation
    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        ge.append(genome)
        env.player_controller = net
        f,p,e,t,fl,pl,el,tl = env.play()
        genome.fitness = f

        # Update max fitness and write to bestgenome file
        if f > MAXFIT:
            MAXFIT = f
            file_aux  = open(experiment_name+'/bestgenome.txt','w')
            file_aux.write("Enemies: "+ str(env.enemies)+"\nFitness: "+ str(fl)+"\nPlayerlife: "+ str(pl)+"\nEnemylife: "+ str(el)+"\nTime: "+ str(tl)+ "\n\n")
            file_aux.close()
        TOTALGAMES += 1


# Setting up NEAT
def run(config_file):
    global TOTALGAMES
    # Coupling with config file
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # setting up population
    pop = neat.Population(config)

    # Setting up statistics
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)

    # giving fitness function and amount of generations
    winner = pop.run(eval_genome,GEN)
    pickle.dump(winner, open('winner.pkl', 'wb'))

    print('\nBest man:\n{!s}'.format(winner))

    fim = time.time() # prints total execution time for experiment
    print( '\nExecution time: '+str(round((fim-ini)/60,2))+' minutes \n')
    file_aux  = open(experiment_name+'/stats.txt','w')
    file_aux.write('Total execution time: '+str(round((fim-ini)/60,2))+' minutes')
    file_aux.write('\n\nAmount of generations: '+str(GEN))
    file_aux.close()

    # Draw topology and fitness per generation
    visualize.draw_net(config, winner, True)
    visualize.plot_stats(stats, ylog=False, view=True)

    # Save text file with winning genome topology
    top1 = str(stats.best_genome())
    file_aux  = open(experiment_name+'/bestgenome.txt','a')
    file_aux.write(top1)
    file_aux.close()

    # Save stats file with per generation info
    TOTALGAMES *= len(env.enemies)
    file_aux  = open(experiment_name+'/stats.txt','a')
    file_aux.write("\n\nEnemies: " + str(env.enemies))
    file_aux.write("\n\nTotal amount of games: " + str(TOTALGAMES))

    fit_max = stats.get_fitness_stat(max)
    fit_mean = stats.get_fitness_mean()
    fit_std = stats.get_fitness_stdev()
    fit_med = stats.get_fitness_median()

    for value in range(len(fit_mean)):
        file_aux.write("\n\nGen Max   Mean   Std   Med")
        file_aux.write("\n"+str(value)+":  "+str(round(fit_max[value],3))+ " "+str(round(fit_mean[value],3))+" "+str(round(fit_std[value],3))+" "+str(round(fit_med[value],3))+" ")
    file_aux.close()

    # Save all species to text file
    file_aux  = open(experiment_name+'/species.txt','w')
    spec_fit = stats.get_species_fitness()
    print(str(spec_fit))
    file_aux.write(str(spec_fit)+"\n")
    for gen in range(len(spec_fit)):
        file_aux.write("\n\nGen "+ str(gen) + "\nID fitness\n")
        for value in range(len(spec_fit[gen])):
            file_aux.write(str(value)+ ":  " + str(spec_fit[gen][value]))
    file_aux.close()

# Function to replay best topology from pickle file
def replay_genome(config_path, genome_path):
    # Load requried NEAT config
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)

    # Unpickle saved winner
    with open(genome_path, "rb") as f:
        genome = pickle.load(f)

    net = neat.nn.FeedForwardNetwork.create(genome, config)
    env.player_controller = net
    f,p,e,t,fl,pl,el,tl = env.play()
    genome.fitness = f
    return f,p,e,t,fl,pl,el,tl

# Calls replay function to test winning situation
if run_mode =='test':
    file_aux  = open('gain_results/EASYgain.txt','w')
    file_aux.write("Sol Run Kill Gain Pe Ee Fit Gainl Pl El Fl\n\n")
    for sol in range(10):
        for run in range(5):
            path = "neat_sol/EASY/sol_"+str(sol)+"/winner.pkl"
            print(path)
            f,p,e,t,fl,pl,el,tl = replay_genome("neat_test/config-feedforward.txt", path)
            gain = p-e
            gains = []
            for i in range(len(pl)):
                gains.append(pl[i]-el[i])
            killed = el.count(0)
            file_aux.write(str(sol)+"-"+str(run+1)+"= "+str(killed)+", "+str(gain)+", "+str(p)+", "+str(e)+", "+str(f)+", "+str(gains)+", "+str(pl)+", "+str(el)+", "+str(fl)+"\n")
    file_aux.close()
    sys.exit(0)

# Locating config file
if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_file = os.path.join(local_dir, "config-feedforward.txt")
    run(config_file)