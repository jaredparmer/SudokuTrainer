#!/usr/bin/env python3

import random
import math
import time
import numpy as np


""" todos:
    - debug solve_all() (branching too much)
    - generalize to Sudokus of any perfect square size
    - error catch in __init__: sizes that aren't perfect squares or int
    - error catch in __init__: invalid given values

"""

class Sudoku:
    """ represents a Sudoku puzzle """

    def __init__(self, size=9, label=time.time(), puzzle=[]):
        # instance attributes:
        self.puzzle = []
        self.size = size
        self.box_size = int(math.sqrt(size))
        self.label = str(label)
        self.candidates = ''
               
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

        # initialize self.candidates based on puzzle size
        for i in range(self.size):
            self.candidates += str(i + 1)

        # initialize self.puzzle to a blank puzzle
        for i in range(self.size ** 2):
                self.puzzle.append(self.candidates)
        
        if puzzle != []:
            """ user has provided puzzle values; insert with insert(), which
            also removes that value from the candidate list of neighbors """
            for i in range(len(puzzle)):
                if isinstance(puzzle[i], int) and puzzle[i] != 0:
                    # caller provided value for cell
                    self.insert(str(puzzle[i]), i)

        """ store solution and score puzzle; solve() will provide values for
        self.solutions and self.difficulty """
        self.solve(report=False)


    def __getitem__(self, key):
        return self.puzzle[key]


    def __lt__(self, other):
        """ dummy defn for sorting by SudokuGenerator(), which prioritizes
        difficulty scores but is otherwise indifferent """
        return self
        

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
        function for __init__() and solve_all(). """
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
        cell's row, column, or box. """
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
