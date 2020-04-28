#!/usr/bin/env python2

from gurobipy import Model, GRB
from itertools import product
import numpy as np
import time


class auto_assigner:
    # tolerance for integrality check
    _EPS = 1e-3

    # initialize the parameters
    # demand - requested number of reviewers per paper
    # ability - the maximum number of papers reviewer can review
    # function - transformation function of similarities
    # iter_limit - maximum number of iterations of Steps 2 to 7
    # time_limit - time limit in seconds. The algorithm performs iterations of Steps 2 to 7 until the time limit is exceeded
    def __init__(self, simmatrix, demand=3, ability=3, function=lambda x: x, iter_limit=np.inf, time_limit=np.inf):
        self.simmatrix = simmatrix
        self.numrev = simmatrix.shape[0]
        self.numpapers = simmatrix.shape[1]
        self.ability = ability
        self.demand = demand
        self.function = function
        if iter_limit < 1:
            raise ValueError('Maximum number of iterations must be at least 1')
        self.iter_limit = iter_limit
        self.time_limit = time_limit

    # initialize the flow network in the subroutine
    def _initialize_model(self):

        problem = Model()
        problem.setParam('OutputFlag', False)

        # edges from source to reviewers, capacity controls maximum reviewer load
        self._source_vars = problem.addVars(self.numrev, vtype=GRB.CONTINUOUS, lb=0.0,
                                            ub=self.ability, name='reviewers')

        # edges from papers to sink, capacity controls a number of reviewers per paper
        self._sink_vars = problem.addVars(self.numpapers, vtype=GRB.CONTINUOUS, lb=0.0,
                                          ub=self.demand, name='papers')

        # edges between reviewers and papers. Initially capacities are set to 0 (no edge is added in the network)
        self._mix_vars = problem.addVars(self.numrev, self.numpapers, vtype=GRB.CONTINUOUS,
                                         lb=0.0, ub=0.0, name='assignment')
        problem.update()

        # flow balance equations for reviewers' nodes
        self._balance_reviewers = problem.addConstrs((self._source_vars[i] == self._mix_vars.sum(i, '*')
                                                      for i in range(self.numrev)))

        # flow balance equations for papers' nodes
        self._balance_papers = problem.addConstrs((self._sink_vars[i] == self._mix_vars.sum('*', i)
                                                   for i in range(self.numpapers)))
        problem.update()

        self._problem = problem

    # compute the order in which subroutine adds edges to the network
    def _ranking_of_pairs(self, simmatrix):
        pairs = [[reviewer, paper] for (reviewer, paper) in product(range(self.numrev), range(self.numpapers))]
        sorted_pairs = sorted(pairs, key=lambda x: simmatrix[x[0], x[1]], reverse=True)
        return sorted_pairs

    # subroutine
    # simmatrix - similarity matrix, updated for previously assigned papers
    # kappa - requested number of reviewers per paper
    # abilities - current constraints on reviewers' loads
    # not_assigned - a set of papers to be assigned
    # lower_bound - internal variable to start the binary search from
    def _subroutine(self, simmatrix, kappa, abilities, not_assigned, lower_bound, *args):

        # set up the max flow objective
        self._problem.setObjective(sum([self._source_vars[i] for i in range(self.numrev)]), GRB.MAXIMIZE)

        # if paper is not fixed in the final output yet, assign it with kappa reviewers
        for paper in not_assigned:
            self._sink_vars[paper].ub = kappa
            self._sink_vars[paper].lb = 0

        # adjust reviewers' loads (in the network) for paper that are already fixed in the final assignment
        for reviewer in range(self.numrev):
            self._source_vars[reviewer].ub = abilities[reviewer]

        sorted_pairs = self._ranking_of_pairs(simmatrix)

        # upper_bound - internal variable to start the binary search from
        if args != ():
            upper_bound = args[0]
        else:
            upper_bound = len(sorted_pairs)

        current_solution = 0

        # if upper_bound == lower_bound, do one iteration to add corresponding edges to the flow network
        one_iteration_done = False

        # binary search to find the minimum number of edges
        # with largest similarity that should be added to the network
        # to achieve the requested max flow

        while lower_bound < upper_bound or not one_iteration_done:
            one_iteration_done = True
            prev_solution = current_solution
            current_solution = lower_bound + (upper_bound - lower_bound) // 2

            # the next condition is to control the case when upper_bound - lower_bound = 1
            # then it must be the case that max flow is less then required
            if current_solution == prev_solution:
                if maxflow < len(not_assigned) * kappa and current_solution == lower_bound:
                    current_solution += 1
                    lower_bound += 1
                else:
                    raise ValueError('An error occured1')

            # if binary choice increased the current estimate, add corresponding edges to the network
            if current_solution > prev_solution:
                for cur_pair in sorted_pairs[prev_solution: current_solution]:
                    self._mix_vars[cur_pair[0], cur_pair[1]].ub = 1
            # otherwise remove the corresponding edges
            else:
                for cur_pair in sorted_pairs[current_solution: prev_solution]:
                    self._mix_vars[cur_pair[0], cur_pair[1]].ub = 0

            # check maxflow in the current estimate
            self._problem.optimize()
            maxflow = self._problem.objVal

            # if maxflow equals to the required flow, decrease the upper bound on the solution
            if maxflow == len(not_assigned) * kappa:
                upper_bound = current_solution
            # otherwise increase the lower bound
            elif maxflow < len(not_assigned) * kappa:
                lower_bound = current_solution
            else:
                raise ValueError('An error occured2')

        # check if binary search succesfully converged
        if maxflow != len(not_assigned) * kappa or lower_bound != current_solution:
            # shouldn't enter here
            print
            maxflow, len(not_assigned), lower_bound, current_solution
            raise ValueError('An error occured3')

        # prepare for max-cost max-flow -- we enforce each paper to be reviewed by kappa reviewers
        for paper in not_assigned:
            self._sink_vars[paper].lb = kappa

        # max cost max flow objective
        self._problem.setObjective(sum([sum([simmatrix[reviewer, paper] * self._mix_vars[reviewer, paper]
                                             for paper in not_assigned])
                                        for reviewer in range(self.numrev)]), GRB.MAXIMIZE)
        self._problem.optimize()

        # return assignment
        assignment = {}
        for paper in not_assigned:
            assignment[paper] = []
        for reviewer in range(self.numrev):
            for paper in not_assigned:
                if self._mix_vars[reviewer, paper].X == 1:
                    assignment[paper] += [reviewer]
                if np.abs(self._mix_vars[reviewer, paper].X - int(self._mix_vars[reviewer, paper].X)) > self._EPS:
                    raise ValueError('Error with rounding -- please check that demand and ability are integal')
                self._mix_vars[reviewer, paper].ub = 0
        self._problem.update()

        return assignment, current_solution

    # Join two assignments
    @staticmethod
    def _join_assignment(assignment1, assignment2):
        assignment = {}
        for paper in assignment1:
            assignment[paper] = assignment1[paper] + assignment2[paper]
        return assignment

    # Compute fairness
    def quality(self, assignment, *args):
        qual = np.inf
        if args != ():
            paper = args[0]
            return np.sum([self.function(self.simmatrix[reviewer, paper]) for reviewer in assignment[paper]])
        else:
            for paper in assignment:
                if qual > sum([self.function(self.simmatrix[reviewer, paper]) for reviewer in assignment[paper]]):
                    qual = np.sum([self.function(self.simmatrix[reviewer, paper]) for reviewer in assignment[paper]])
        return qual

    # Full algorithm
    def _fair_assignment(self):
        
        # Counter for number of performed iterations
        iter_counter = 0
        # Start time
        start_time = time.time()
        
        current_best = None
        current_best_score = 0
        local_simmatrix = self.simmatrix.copy()
        local_abilities = self.ability * np.ones(self.numrev)
        not_assigned = set(range(self.numpapers))
        final_assignment = {}

        # One iteration of Steps 2 to 7 of the algorithm
        while not_assigned != set() and iter_counter < self.iter_limit and (time.time() < start_time + self.time_limit or iter_counter == 0):
            
            iter_counter += 1
            
            lower_bound = 0
            upper_bound = len(not_assigned) * self.numrev

            # Step 2
            for kappa in range(1, self.demand + 1):

                # Step 2(a)
                tmp_abilities = local_abilities.copy()
                tmp_simmatrix = local_simmatrix.copy()

                # Step 2(b)
                assignment1, lower_bound = self._subroutine(tmp_simmatrix, kappa, tmp_abilities, not_assigned,
                                                            lower_bound, upper_bound)

                # Step 2(c)
                for paper in assignment1:
                    for reviewer in assignment1[paper]:
                        tmp_simmatrix[reviewer, paper] = -1
                        tmp_abilities[reviewer] -= 1

                # Step 2(d)
                assignment2 = self._subroutine(tmp_simmatrix, self.demand - kappa, tmp_abilities, not_assigned,
                                               lower_bound, upper_bound)[0]

                # Step 2(e)
                assignment = self._join_assignment(assignment1, assignment2)

                # Keep track of the best candidate assignment (including the one from the prev. iteration)
                if self.quality(assignment) > current_best_score or current_best_score == 0:
                    current_best = assignment
                    current_best_score = self.quality(assignment)

            # Steps 4 to 6
            for paper in not_assigned.copy():
                # For every paper not yet fixed in the final assignment we update the assignment
                final_assignment[paper] = current_best[paper]
                # Find the most worst-off paper
                if self.quality(current_best, paper) == current_best_score:
                    # Delete it from current candidate assignment and from the set of papers which are
                    # not yet fixed in the final output
                    del current_best[paper]
                    not_assigned.discard(paper)
                    # This paper is now fixed in the final assignment

                    # Update abilities of reviewers
                    for reviewer in range(self.numrev):
                        # edges adjunct to the vertex of the most worst-off papers
                        # will not be used in the flow network any more
                        local_simmatrix[reviewer, paper] = -1
                        self._mix_vars[reviewer, paper].ub = 0
                        self._mix_vars[reviewer, paper].lb = 0
                        if reviewer in final_assignment[paper]:
                            local_abilities[reviewer] -= 1
            
            current_best_score = self.quality(current_best)
            self._problem.update()

        self.fa = final_assignment
        self.best_quality = self.quality(final_assignment)

    def fair_assignment(self):
        self._initialize_model()
        self._fair_assignment()

def tpms_assignment(papload, revload, similarity):
    problem = Model()
    problem.setParam('OutputFlag', False)
    numrev = similarity.shape[0]
    numpap = similarity.shape[1]
    source_vars = problem.addVars(numrev, vtype=GRB.CONTINUOUS, lb=0, ub=revload, name='reviewers')
    sink_vars = problem.addVars(numpap, vtype=GRB.CONTINUOUS, lb=0,
                                          ub=papload, name='papers')
    mix_vars = problem.addVars(numrev, numpap, vtype=GRB.CONTINUOUS,
                                         lb=0.0, ub=1.0, name='assignment')
                    
    #Reviewer flow constraints
    balance_reviewers = problem.addConstrs((source_vars[i] == mix_vars.sum(i, '*') for i in range(numrev)))

    # avoid COIs
    #avoid_cois = problem.addConstrs((mix_vars[i][j] == 0 for i in range(numrev) for j in range(numpap) if similarity[i,j] < -0.5))

    #Paper flow constraints
    balance_papers = problem.addConstrs((sink_vars[j] == mix_vars.sum('*', j) for j in range(numpap)))
        
    #Objective
    problem.setObjective(sum([sum([mix_vars[rev, pap] * similarity[rev, pap] 
                                   for pap in range(numpap)])
                              for rev in range(numrev)]),
                         GRB.MAXIMIZE)
    problem.optimize()
    if problem.status != 2:
        raise Exception('An error occured')
    #The rest is a constructun of the assignment dict
    assignment = {rev : [] for rev in range(numrev)}
    for pap in range(numpap):
        for rev in range(numrev):
            if mix_vars[rev, pap].X == 1:
                assignment[rev] += [pap]
        
    return(assignment)
