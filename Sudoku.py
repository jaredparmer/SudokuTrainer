#!/usr/bin/env python3

import random
import math
import time
import numpy as np


""" todos:
    - create Sudoku class                                 DONE 01/10
        - solve_fast() and helper fns need puzzle as arg  DONE 01/10
    - enhance solve fn to count solutions                 DONE 15/10
    - write scoring function                              DONE 02/11
    - set-oriented solve optimization                     DONE 05/11
    - debug solve_all() (branching too much)
    - pickle puzzles
    - white generate() to generate puzzles                IN PROGRESS 06/11
        - write remove() helper fn                        DONE 06/11
    - enhance generate() for target and max difficulty
    - generalize turtle fns for puzzles not 9x9
    - generalize initialize() and make() for size
    - implement GUI
        - fill cells
        - call for solvability
        - call for final check
        - get hint/freebie
        - candidate marks
            - corner notation
            - center notation
        - highligher
        - highlight selected number (every 8, e.g.)
    - write fns for IDing strategies
        - X wing
        - XY wing
        - Schrodinger cell
        - swordfish pattern
        - empty rectangle
        - jellyfish pattern
"""


class Sudoku:
    """ represents a Sudoku puzzle """

    # TODO: error catch sizes that aren't perfect squares or not int
    # TODO: generalize to Sudokus of any (perfect square) size
    def __init__(self, size=9, label=time.time(), puzzle=[]):
        # instance attributes:
        self.puzzle = []
        self.size = size
        self.box_size = int(math.sqrt(size))
        self.label = str(label)
        self.candidates = ''
        for i in range(self.size):
            self.candidates += str(i + 1)
               
        """ A puzzle is a list of elements that are either strings of candidate
        values for a particular cell, or the integer solution for that cell.
        The row and column for each cell is implicit in the data structure as
        follows:
            row1col1, row1col2, ..., row1col9,
            row2col1, row2col2, ..., row2col9,
            .
            .
            .
            row9col1, row9col2, ..., row9col9
        When the string of candidate values is empty, there is no valid value
        for that cell and the puzzle is thus unsolvable.
        """

        """ a list of complete, valid solutions to the given puzzle; an
        unsolvable given puzzle has an empty list of solutions; a uniquely
        solvable given puzzle has a single-element list of solutions, etc.
        Only a given puzzle with a unique solution is valid. """
        self.solutions = []

        """ difficulty of unique solution given by:
             difficulty = B * 100 + E
        where B is the sum (Bi - 1) ** 2 for every branching factor, and E is
        the number of empty cells in the given puzzle. This score is computed
        in score() if and only if a single solution has been found. """
        self.difficulty = np.NaN
        self.branch_factors = []

        if puzzle == []:
            # user has not provided puzzle values; make a puzzle from scratch
            self.make()
        else:
            """ TODO: ensure user did not provide invalid values (e.g., two 9s
            in the same row """

            """ step one: set self.puzzle to a blank puzzle """
            for i in range(self.size ** 2):
                self.puzzle.append(self.candidates)

            """ step two: insert any given values with insert(), which also
            removes that value from the candidate list of neighbors """
            for i in range(len(puzzle)):
                if isinstance(puzzle[i], int) and puzzle[i] != 0:
                    # caller provided value for cell
                    self.insert(str(puzzle[i]), i)

            """ step three: store solution and score puzzle """
            self.solve(report=False)
        

    def __str__(self):
        return self.print()


    def fewest_candidates(self, puzzle=None):
        """ helper function for solve_all(). returns the index of cell in
        puzzle with fewest remaining candidate values.
        """
        if puzzle is None:
            puzzle = self.puzzle
            
        fewest = -1
        for i in range(self.size**2):
            if isinstance(puzzle[i], int):
                # cell is solved; skip it
                continue
            if len(puzzle[i]) <= 1:
                """ cell has only one candidate, or is unsolvable; this cell
                should be processed immediately by caller function.
                """
                return i
            if fewest == -1:
                # first candidate has been found;
                fewest = i
            elif len(puzzle[i]) < len(puzzle[fewest]):
                # cell has fewest candidates of cells checked so far
                fewest = i
        return fewest


    def fewest_positions(self, puzzle=None):
        """ helper function for solve_all(). returns the candidate value with
        the fewest possible positions in a given set (row, column, or box) and
        the indices of that set. """
        if puzzle is None:
            puzzle = self.puzzle

        fpp_candidate = ''
        fpp_positions = list(range(self.size**2))
        
        # find value with fewest candidate positions by column
        d = {}
        for col in range(0, self.size):
            for i in range(0, self.size**2, self.size):
                j = i + col
                if isinstance(puzzle[j], int):
                    continue
    
                for candidate in puzzle[j]:
                    if candidate in d:
                        d[candidate].append(j)
                    else:
                        d[candidate] = [j]

            for candidate in d:
                if len(d[candidate]) < len(fpp_positions):
                    fpp_candidate = candidate
                    fpp_positions = d[candidate]
                
            d = {}
            
        # now by row
        d = {}
        for row in range(0, self.size**2, self.size):
            for i in range(0, self.size):
                j = i + row
                if isinstance(puzzle[j], int):
                    continue
                
                for candidate in puzzle[j]:
                    if candidate in d:
                        d[candidate].append(j)
                    else:
                        d[candidate] = [j]

            for candidate in d:
                if len(d[candidate]) < len(fpp_positions):
                    fpp_candidate = candidate
                    fpp_positions = d[candidate]
   
            d = {}
            
        # now by box
        d = {}
        i = 0
        while i < self.size**2:
            # traverse across boxes, where i is the index of the top-left cell
            for j in range(0, self.size * self.box_size, self.size):
                for k in range (0, self.box_size):
                    # traverse within each box
                    index = i + j + k
                    if isinstance(puzzle[index], int):
                        continue
                    
                    for candidate in puzzle[index]:
                        if candidate in d:
                            d[candidate].append(index)
                        else:
                            d[candidate] = [index]
                            
            # entire box checked; process and clear dictionary
            for candidate in d:
                if len(d[candidate]) < len(fpp_positions):
                    fpp_candidate = candidate
                    fpp_positions = d[candidate]

            d = {}

            # increment counter for next box
            i += self.box_size
            if i % self.size == 0:
                """ we have finished the boxes in this row of the puzzle (e.g.,
                boxes 1, 2, and 3 in a 9x9 Sudoku); so increment i further to
                set it to the top-left cell of the next box (e.g., box 4) """
                i += self.size * (self.box_size - 1)
        
        return fpp_candidate, fpp_positions


    def insert(self, value, index, puzzle=None):
        """ inserts given value into given cell of Sudoku puzzle, and removes
        that value from the candidates list of all neighboring cells. Helper
        function for __init__(), make(), generate(), and solve_all(). """
        if puzzle is None:
            puzzle = self.puzzle
            
        row = index // self.size
        col = index % self.size            
        box_r = row - (row % self.box_size)
        box_c = col - (col % self.box_size)

        # step one: remove value from candidates elsewhere in box
        # cell in top-left corner of relevant box
        top_left = box_r * int(math.sqrt(len(puzzle))) + box_c
        # now traverse all cells in box
        for i in range(0, self.size * self.box_size, self.size):
            for j in range(top_left + i, top_left + i + self.box_size):
                if isinstance(puzzle[j], int):
                    continue
                if value in puzzle[j]:
                    puzzle[j] = puzzle[j].replace(value, '')

        # step two: remove from candidates elsewhere in column
        for i in range(0, self.size**2, self.size):
            j = i + col
            if isinstance(puzzle[j], int):
                continue
            if value in puzzle[j]:
                puzzle[j] = puzzle[j].replace(value, '')

        # step three: remove from candidates elsewhere in row
        row_index = row * self.size
        for i in range(0, self.size):
            j = row_index + i
            if isinstance(puzzle[j], int):
                continue
            if value in puzzle[j]:
                puzzle[j] = puzzle[j].replace(value, '')

        # step four: insert value
        puzzle[index] = int(value)


    def is_complete(self, puzzle=None):
        """ checks whether any cells have not been solved. Cells with
        candidates remaining (i.e., a non-empty string) or cells with no valid
        solution (i.e., an empty string) cause it to return False. Otherwise,
        the puzzle is complete and the function returns True.
        """
        if puzzle is None:
            puzzle = self.puzzle
            
        for i in range(self.size**2):
            if not isinstance(puzzle[i], int):
                return False
        return True


    def make(self):
        """ fills the first three boxes and first column of a blank grid, then
        uses generate() to generate a final puzzle """

        # step zero: initialize puzzle with all candidates
        for i in range(self.size**2):
            self.puzzle.append(self.candidates)

        # step one: fill box 1
        # traverse by row and col the cells within the first box
        top_left_index = 0
        row_index_delta = self.size
        row_beyond_box_index = self.size * self.box_size
        for i in range(top_left_index, row_beyond_box_index, row_index_delta):
            # create random sequence of candidates for row
            values = random.sample(list(self.puzzle[i]), len(self.puzzle[i]))        
            for j in range(i, i + self.box_size):
                # pull random value and assign to cell
                candidate = values.pop()
                self.insert(candidate, j)

        # step two: fill box 2
        # traverse by row and col the cells within the second box
        top_left_index += self.box_size
        row_beyond_box_index += self.box_size
        for i in range(top_left_index, row_beyond_box_index, row_index_delta):
            # create random sequence of candidates for row
            values = random.sample(list(self.puzzle[i]), len(self.puzzle[i]))
            for j in range(i, i + self.box_size):
                row = j // self.size
                if row < self.box_size - 1:
                    """ we're not on last row, so only pick a value for the
                    cell that won't make last row unsolvable. """
                    brc = self.size * (self.box_size - 1) + self.box_size
                    
                    for v in values:
                        """ temporarily remove v from candidates for cell in
                        bottom-right corner of the current/second box """
                        brc_wo_v = self.puzzle[brc].replace(v, '')
                        if len(brc_wo_v) >= self.box_size:
                            # bottom row of box will still be solvable
                            candidate = v
                            values.remove(v)
                            break
                else:
                    # in last row of box; simply pick value and fill
                    candidate = values.pop()

                self.insert(candidate, j)

        # step three: fill box 3
        # traverse by row and col the cells within third box
        top_left_index += self.box_size
        row_beyond_box_index += self.box_size
        for i in range(top_left_index, row_beyond_box_index, row_index_delta):
            # create random sequence of candidates for row
            values = random.sample(list(self.puzzle[i]), len(self.puzzle[i]))
            for j in range(i, i + self.box_size):
                candidate = values.pop()
                self.insert(candidate, j)

        # step four: fill column 1
        # traverse first col of entire puzzle, starting below first box
        top_left_index = self.size * self.box_size
        row_beyond_puzzle_index = self.size**2
        for i in range(top_left_index, row_beyond_puzzle_index,
                       row_index_delta):
            values = random.sample(list(self.puzzle[i]), len(self.puzzle[i]))
            candidate = values.pop()
            self.insert(candidate, i)

        # step five: generate puzzle
        self.generate()


    def print(self, puzzle=None):
        if puzzle is None:
            puzzle = self.puzzle
            
        res = self.label + ':\n'
        for i in range(self.size**2):
            row = i // self.size
            col = i % self.size
            if row % self.box_size == 0 and col == 0:
                # starting a new row; print horizontal bar
                res += '-------------------------\n'
            if col % self.box_size == 0:
                # entered a new box; print vertical bar
                res += '| '

            if isinstance(puzzle[i], int):
                # cell has determinate value
                res += str(puzzle[i]) + ' '
            elif len(puzzle[i]) >= 1:
                # cell has multiple candidates
                res += '0 '
            else:
                # cell has no candidates, puzzle is unsolvable
                res += '! '

            if col == self.size - 1:
                # hit right edge of puzzle; move to next line
                res += '|\n'
        res += '-------------------------'
        return res


    def remove(self, index, puzzle=None):
        """ removes value from given cell (index) of Sudoku puzzle, and stores
        all candidate values in that cell that are not already used in this
        cell's row, column, or box. Helper function for generate(). """
        if puzzle is None:
            puzzle = self.puzzle

        if not isinstance(puzzle[index], int):
            # cell is not solved; nothing to remove
            return

        # step one: load all candidates into cell
        puzzle[index] = self.candidates

        # step two: remove candidates already used elsewhere
        row = index // self.size
        col = index % self.size
        for candidate in puzzle[index]:
            if (self.used_in_row(row, candidate, puzzle) or
                self.used_in_col(col, candidate, puzzle) or
                self.used_in_box(row, col, candidate, puzzle)):
                puzzle[index] = puzzle[index].replace(candidate, '')


    def score(self, puzzle=None):
        if puzzle is None:
            puzzle = self.puzzle
        
        if len(self.solutions) == 1:
            # unique solution found; commence scoring
            # step one: calculate B, branch-difficulty score
            terms = [(self.branch_factors[i] - 1) ** 2
                     for i in range(len(self.branch_factors))]
            B = sum(terms)

            # step two: fetch number of empty cells in given puzzle
            empty_cells = 0
            for i in range(len(puzzle)):
                if not isinstance(puzzle[i], int):
                    empty_cells += 1
                    
    ##        print("branch_factors:", self.branch_factors)
    ##        print("terms:", terms)
    ##        print("B =", B)
    ##        print("# of empty cells =", empty_cells)

            # step three: calculate and store puzzle difficulty score
            self.difficulty = B * 100 + empty_cells
        else:
            # no unique solution found
            self.difficulty = np.NaN
            
        return self.difficulty


    def solve(self, puzzle=None, report=True):
        """ calls solve_all() to generate solution(s), scores unique solution
        if found, and (optionally) prints the resultant solution """

        # first, clear values in solutions list
        self.solutions = []
        self.branch_factors = []

        self.solve_all(puzzle)
        self.score(puzzle)

        if report:
            if len(self.solutions) == 0:
                print("No solution could be found.")
            elif len(self.solutions) == 1:
                print("Unique solution: ")
                print(self.print(self.solutions[0]))
                print("Difficulty score:", self.difficulty)
            else:
                print("Multiple possible solutions found.")


    # TODO: check to ensure given puzzle is valid; e.g., solve_all() currently
    # ignores the fact that the puzzle has two 1s in the top row
    def solve_all(self, puzzle=None):
        """ solver function that utilizes backtracking, randomization, and
        optimization. Returns solved puzzle, or None if given puzzle is
        unsolvable. Stores found solutions in self.solutions list.

        The optimization is that this solver does not traverse all cells in
        order (from 0 to 80 in a 9x9 puzzle, for example). Instead, it picks
        the cell with the fewest remaining candidates, or the set and value
        with the fewest possible positions, whichever is smaller.
        """
        if puzzle is None:
            puzzle = self.puzzle[:]
            
        while not self.is_complete(puzzle):
            i = self.fewest_candidates(puzzle)
            # fewest_candidates() skips solved cells                
 
            if len(puzzle[i]) == 1:
                # all candidates but one have been eliminated; officially
                # solve cell with insert()
                self.insert(puzzle[i], i, puzzle)
                continue
            if len(puzzle[i]) == 0:
                # cell has no possible solutions; puzzle unsolvable
                return None
            if len(puzzle[i]) > 1:
                # cell has more than one candidate

                search_set = []
                """ find value with fewest possible remaining positions in
                some set (row, column, or box) """
                fpp_value, fpp_positions = (
                    self.fewest_positions(puzzle))
                
                if len(fpp_positions) < len(puzzle[i]):
                    # value-set is more promising than current cell
                    for position in fpp_positions:
                        # build search_set to try value in each position in set
                        search_set.append((fpp_value, position))
                else:
                    # current cell is more promising than value-set
                    candidates = random.sample(puzzle[i], len(puzzle[i]))
                    for candidate in candidates:
                        # build search-set to try each candidate in cell
                        search_set.append((candidate, i))

                branches = 0

                for candidate, position in search_set:
                    puzzle_copy = puzzle[:]

                    self.insert(candidate, position, puzzle_copy)

                    # recurse on copy and mark branching
                    branches += 1
                    puzzle_copy = self.solve_all(puzzle_copy)

                    # check that we haven't found more than one solution
                    if (len(self.solutions) >= 2
                        and puzzle_copy is not None):
                        # we have, so start kick
                        return puzzle_copy
                        
                # search tree is exhausted from this node
                self.branch_factors.append(branches)
                return None
            
        # puzzle is complete; store it in solutions and score
        if puzzle not in self.solutions:
            self.solutions.append(puzzle)
            
        return puzzle


    def used_in_box(self, row, col, candidate, puzzle=None):
        if puzzle is None:
            puzzle = self.puzzle
            
        # row and col values for cell in top-left corner of relevant box
        box_r = row - (row % self.box_size)
        box_c = col - (col % self.box_size)
        # cell in top-left corner of relevant box
        top_left = box_r * self.size + box_c
        # now traverse all cells in box
        for i in range(0, self.size * self.box_size, self.size):
            for j in range(top_left + i, top_left + i + self.box_size):
                if puzzle[j] == int(candidate):
                    return True
        return False


    def used_in_col(self, col, candidate, puzzle=None):
        if puzzle is None:
            puzzle = self.puzzle
            
        for i in range(0, self.size**2, self.size):
            j = i + col
            if puzzle[j] == int(candidate):
                return True
        return False


    def used_in_row(self, row, candidate, puzzle=None):
        if puzzle is None:
            puzzle = self.puzzle
            
        row_index = row * self.size
        for i in range(0, self.size):
            j = row_index + i
            if puzzle[j] == int(candidate):
                return True
        return False


def _comparisons():
    dlbeer_55 = [5,3,4,0,0,8,0,1,0,
                 0,0,0,0,0,2,0,9,0,
                 0,0,0,0,0,7,6,0,4,
                 0,0,0,5,0,0,1,0,0,
                 1,0,0,0,0,0,0,0,3,
                 0,0,9,0,0,1,0,0,0,
                 3,0,5,4,0,0,0,0,0,
                 0,8,0,2,0,0,0,0,0,
                 0,6,0,7,0,0,3,8,2]

    dlbeer_253 = [0,7,0,3,0,0,0,4,0,
                  3,0,0,0,8,0,2,0,0,
                  2,0,1,4,0,7,0,0,0,
                  5,0,4,0,0,0,0,9,0,
                  0,2,0,0,0,0,0,5,0,
                  0,1,0,0,0,0,7,0,3,
                  0,0,0,9,0,6,3,0,2,
                  0,0,2,0,3,0,0,0,9,
                  0,6,0,0,0,2,0,8,0]

    dlbeer_451 = [0,4,0,0,0,7,0,9,0,
                  0,9,1,0,8,0,0,0,0,
                  7,0,3,9,0,1,0,0,0,
                  0,1,0,0,6,4,2,0,0,
                  0,0,0,5,0,8,0,0,0,
                  0,0,5,7,1,0,0,6,0,
                  0,0,0,1,0,5,8,0,6,
                  0,0,0,0,4,0,9,1,0,
                  0,5,0,8,0,0,0,2,0]

    dlbeer_551 = [3,7,0,0,0,9,0,0,6,
                  8,0,0,1,0,3,0,7,0,
                  0,0,0,0,0,0,0,0,8,
                  0,2,0,0,8,0,0,0,5,
                  1,8,7,0,0,0,6,4,2,
                  5,0,0,0,2,0,0,1,0,
                  7,0,0,0,0,0,0,0,0,
                  0,5,0,6,0,2,0,0,7,
                  2,0,0,3,0,0,0,6,1]

    dlbeer_953 = [0,0,3,0,0,0,0,0,0,
                  8,0,9,4,6,0,7,0,2,
                  2,0,0,0,1,8,6,0,0,
                  0,0,0,0,0,6,0,7,0,
                  0,0,8,0,0,0,4,0,0,
                  0,7,0,8,0,0,0,0,0,
                  0,0,2,9,4,0,0,0,5,
                  4,0,6,0,3,2,8,0,7,
                  0,0,0,0,0,0,2,0,0]

    puzzle = Sudoku(label='dlbeer_551', puzzle=dlbeer_551)
    print(puzzle)
    puzzle.solve(report=False)
    print("Difficulty: ", puzzle.difficulty)

    puzzle = Sudoku(label='dlbeer_253', puzzle=dlbeer_253)
    print(puzzle)
    puzzle.solve(report=False)
    print("Difficulty: ", puzzle.difficulty)

    puzzle = Sudoku(label='dlbeer_451', puzzle=dlbeer_451)
    print(puzzle)
    puzzle.solve(report=False)
    print("Difficulty: ", puzzle.difficulty)

    puzzle = Sudoku(label='dlbeer_953', puzzle=dlbeer_953)
    print(puzzle)
    puzzle.solve(report=False)
    print("Difficulty: ", puzzle.difficulty)


def generate(base_puzzle=Sudoku(), steps=10, walks=1):
    """ 
    """

    # start with the first solution solve() gives as best found so far
    print("puzzle state before solve():")
    print(self)
    self.solve(report=False)
    puzzles_found = [(0, self.solutions[0])]

    print("best puzzle found so far: ", puzzles_found[0][1])
    print("best score so far: ", puzzles_found[0][0])

    # make a copy of the best-so-far puzzle, where we'll start
    puzzle = self.solutions[0][:]

    # generate populations for later sampling; these are lists of indices
    unsolved_cells = []
    solved_cells = []
    for i in range(len(puzzle)):
        if isinstance(puzzle[i], int):
            solved_cells.append(puzzle.index(puzzle[i], i))
        else:
            unsolved_cells.append(puzzle.index(puzzle[i], i))

    print("unsolved cells initial: ")
    print(unsolved_cells)

    print("solved cells initial: ")
    print(solved_cells)

    for i in range(walks):
        # take given number of walks
        for j in range(steps):
            """ take given number of steps per walk. A 'step' is adding or
            removing two clues, where addition or removal is chosen
            randomly but proportional to the options there are. e.g., if
            the puzzle is entirely complete, it will choose to remove with
            certainty; if it is almost complete, it will choose to remove
            with near-certainty, etc. """
            p = 1 - len(unsolved_cells)/len(puzzle)
            
            if np.random.random() < p:
                # this step is a removal of clues
                # pick two cells from solved calls
                positions = (
                    np.random.choice(solved_cells, 2, replace=False))
                for index in positions:
                    self.remove(index, puzzle)
                    unsolved_cells.append(index)
                    solved_cells.remove(index)
            else:
                # this step is an addition of clues
                # pick two cells from unsolved cells
                positions = (
                    np.random.choice(unsolved_cells, 2, replace=False))
                for index in positions:
                    value = np.random.choice(list(puzzle[index]))
                    self.insert(value, index, puzzle)
                    solved_cells.append(index)
                    unsolved_cells.remove(index)

            # add puzzle so far to list, for later comparison
            puzzles_found.append((np.NaN, puzzle[:]))

        print(f"walk {i} complete")
        print("puzzles found without scoring and tossing invalids:")
        print(puzzles_found)
        print("length: ", len(puzzles_found))
            
        # walk i complete
        # check puzzles found so far and toss out invalid ones
        for score, puzz in puzzles_found:
            print("puzzle solved and scored:")
            puzz_copy = puzz[:]
            print("puzzle pre-solve:")
            print(self.print(puzz_copy))
            self.solve(puzz_copy, report=False)
            score_copy = self.difficulty
            print("puzzle post-solve:")
            print(self.print(puzz_copy))
            print("score: ", score_copy)
##                if score_copy is np.NaN:
##                    # puzz has no unique solution; toss it
##                    puzzles_found.remove((score, puzz))
##                else:
##                    # puzz has a unique solution; update its score
##                    puzzles_found.remove((score, puzz))
##                    puzzles_found.append((score_copy, puzz))
                

##            print("puzzles found after tossing invalids:")
##            print(puzzles_found)
##            print("length: ", len(puzzles_found))
        

        """ remove everything from puzzles_found """

##                self.solve(puzzle, report=False)
##                if self.difficulty is not np.NaN:
##                    # puzzle generated after this step is valid; store it
##                    puzzles_found.append((self.difficulty, puzzle))
        


    print("all walks complete")
    print("state of puzzle:")
    print(self.print(puzzle))

                
    # final step: store best puzzle, store its solution and difficulty
##        self.puzzle = best_puzzle
##        self.solve(report=False)


puzzle = Sudoku()
