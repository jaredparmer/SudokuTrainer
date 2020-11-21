#!/usr/bin/env python3

from Sudoku import Sudoku
import random, math, time, numpy as np

""" TODOs:
    - pickle puzzles
    - write generate() to generate puzzles                IN PROGRESS 06/11
    - enhance generate() for target and max difficulty
    - error catching in create()
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

class SudokuGenerator:
    """ Manager class for Sudoku objects. Performs operations like creating,
    duplicating, adjusting difficulty, etc. of Sudoku puzzles. """

    """ class attribute: list of human solving techniques that SudokuGenerator
    can use to constrain the Sudokus it generates. """
    strategies = ['X wing', 'XY wing', 'Schrödinger cell', 'swordfish',
                  'jellyfish', 'empty rectangle']

    """ class attribute: range of possible Sudoku difficulties, with names as
    keys and ranges of scores [x, y) as values."""
    difficulties = {'very easy': range(0, 200), 'easy': range(200, 400),
                    'medium': range(400, 600), 'hard': range(600, 800),
                    'very hard': range(800, 1000)}

    def __init__(self, label=''):
        self.label = str(label)

    def __str__(self):
        return 'SudokuGenerator ' + self.label

    def create(self, size=9, label=time.time(), clues=[]):
        """ return Sudoku of given size, with given clues and label. If no
        clues are given, returns a Sudoku from scratch with randomization. """

        if clues != []:
            # clues given; generate Sudoku with those
            return Sudoku(size, label, clues)

        """ otherwise, generate Sudoku from scratch. Initialize Sudoku object
        with no clues in it, and all cells populated with candidates """
        result = Sudoku(size, label)

        # step one: fill box 1
        # traverse by row and col the cells within the first box
        top_left_index = 0
        row_index_delta = result.size
        row_beyond_box_index = result.size * result.box_size
        for i in range(top_left_index, row_beyond_box_index, row_index_delta):
            # create random sequence of candidates for row
            values = random.sample(
                list(result.puzzle[i]), len(result.puzzle[i]))
            for j in range(i, i + result.box_size):
                # pull random value and assign to cell
                candidate = values.pop()
                result.insert(candidate, j)

        # step two: fill box 2
        # traverse by row and col the cells within the second box
        top_left_index += result.box_size
        row_beyond_box_index += result.box_size
        for i in range(top_left_index, row_beyond_box_index, row_index_delta):
            # create random sequence of candidates for row
            values = random.sample(
                list(result.puzzle[i]), len(result.puzzle[i]))
            for j in range(i, i + result.box_size):
                row = j // result.size
                if row < result.box_size - 1:
                    """ we're not on last row, so only pick a value for the
                    cell that won't make last row unsolvable. """
                    brc = result.size * (result.box_size - 1) + result.box_size
                    
                    for v in values:
                        """ temporarily remove v from candidates for cell in
                        bottom-right corner of the current/second box """
                        brc_wo_v = result.puzzle[brc].replace(v, '')
                        if len(brc_wo_v) >= result.box_size:
                            # bottom row of box will still be solvable
                            candidate = v
                            values.remove(v)
                            break
                else:
                    # in last row of box; simply pick value and fill
                    candidate = values.pop()

                result.insert(candidate, j)

        # step three: fill box 3
        # traverse by row and col the cells within third box
        top_left_index += result.box_size
        row_beyond_box_index += result.box_size
        for i in range(top_left_index, row_beyond_box_index, row_index_delta):
            # create random sequence of candidates for row
            values = random.sample(
                list(result.puzzle[i]), len(result.puzzle[i]))
            for j in range(i, i + result.box_size):
                candidate = values.pop()
                result.insert(candidate, j)

        # step four: fill column 1
        # traverse first col of entire puzzle, starting below first box
        top_left_index = result.size * result.box_size
        row_beyond_puzzle_index = result.size**2
        for i in range(top_left_index, row_beyond_puzzle_index,
                       row_index_delta):
            values = random.sample(
                list(result.puzzle[i]), len(result.puzzle[i]))
            candidate = values.pop()
            result.insert(candidate, i)

##        # step five: generate puzzle
##        self.generate()

        return result
##
##
##def generate(base_puzzle=Sudoku(), steps=10, walks=1):
##    """ 
##    """
##
##    # start with the first solution solve() gives as best found so far
##    print("puzzle state before solve():")
##    print(self)
##    self.solve(report=False)
##    puzzles_found = [(0, self.solutions[0])]
##
##    print("best puzzle found so far: ", puzzles_found[0][1])
##    print("best score so far: ", puzzles_found[0][0])
##
##    # make a copy of the best-so-far puzzle, where we'll start
##    puzzle = self.solutions[0][:]
##
##    # generate populations for later sampling; these are lists of indices
##    unsolved_cells = []
##    solved_cells = []
##    for i in range(len(puzzle)):
##        if isinstance(puzzle[i], int):
##            solved_cells.append(puzzle.index(puzzle[i], i))
##        else:
##            unsolved_cells.append(puzzle.index(puzzle[i], i))
##
##    print("unsolved cells initial: ")
##    print(unsolved_cells)
##
##    print("solved cells initial: ")
##    print(solved_cells)
##
##    for i in range(walks):
##        # take given number of walks
##        for j in range(steps):
##            """ take given number of steps per walk. A 'step' is adding or
##            removing two clues, where addition or removal is chosen
##            randomly but proportional to the options there are. e.g., if
##            the puzzle is entirely complete, it will choose to remove with
##            certainty; if it is almost complete, it will choose to remove
##            with near-certainty, etc. """
##            p = 1 - len(unsolved_cells)/len(puzzle)
##            
##            if np.random.random() < p:
##                # this step is a removal of clues
##                # pick two cells from solved calls
##                positions = (
##                    np.random.choice(solved_cells, 2, replace=False))
##                for index in positions:
##                    self.remove(index, puzzle)
##                    unsolved_cells.append(index)
##                    solved_cells.remove(index)
##            else:
##                # this step is an addition of clues
##                # pick two cells from unsolved cells
##                positions = (
##                    np.random.choice(unsolved_cells, 2, replace=False))
##                for index in positions:
##                    value = np.random.choice(list(puzzle[index]))
##                    self.insert(value, index, puzzle)
##                    solved_cells.append(index)
##                    unsolved_cells.remove(index)
##
##            # add puzzle so far to list, for later comparison
##            puzzles_found.append((np.NaN, puzzle[:]))
##
##        print(f"walk {i} complete")
##        print("puzzles found without scoring and tossing invalids:")
##        print(puzzles_found)
##        print("length: ", len(puzzles_found))
##            
##        # walk i complete
##        # check puzzles found so far and toss out invalid ones
##        for score, puzz in puzzles_found:
##            print("puzzle solved and scored:")
##            puzz_copy = puzz[:]
##            print("puzzle pre-solve:")
##            print(self.print(puzz_copy))
##            self.solve(puzz_copy, report=False)
##            score_copy = self.difficulty
##            print("puzzle post-solve:")
##            print(self.print(puzz_copy))
##            print("score: ", score_copy)
####                if score_copy is np.NaN:
####                    # puzz has no unique solution; toss it
####                    puzzles_found.remove((score, puzz))
####                else:
####                    # puzz has a unique solution; update its score
####                    puzzles_found.remove((score, puzz))
####                    puzzles_found.append((score_copy, puzz))
##                
##
####            print("puzzles found after tossing invalids:")
####            print(puzzles_found)
####            print("length: ", len(puzzles_found))
##        
##
##        """ remove everything from puzzles_found """
##
####                self.solve(puzzle, report=False)
####                if self.difficulty is not np.NaN:
####                    # puzzle generated after this step is valid; store it
####                    puzzles_found.append((self.difficulty, puzzle))
##        
##
##
##    print("all walks complete")
##    print("state of puzzle:")
##    print(self.print(puzzle))
##
##                
##    # final step: store best puzzle, store its solution and difficulty
####        self.puzzle = best_puzzle
####        self.solve(report=False)
##
##
##puzzle = Sudoku()


def main():
    gen = SudokuGenerator()
    puzzle = gen.create()
    print(puzzle)

if __name__ == '__main__':
    main()
