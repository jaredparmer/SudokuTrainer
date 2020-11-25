#!/usr/bin/env python3

from Sudoku import Sudoku
from Timer import Timer, TimerError
import Timer, random, math, time, numpy as np

""" TODOs:
    - pickle puzzles
    - write generate() to generate puzzles                DONE 23/11
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

        # step five: generate puzzle
        result = self.generate(result)

        return result


    def generate(self, given_puzzle, steps=20, walks=200, report=False):
        """ 
        """
        total_timer = Timer.Timer(name="generate()")
        copy_timer = Timer.Timer(name="copying lists")
        obj_timer = Timer.Timer(name="creating Sudokus")
        total_timer.start()

        # start with the first solution solve() gives as best found so far
        if report:
            print("initial puzzle for generate():")
            print(given_puzzle)
            
        given_puzzle.solve(report=False)
        copy_timer.start()
        temp = given_puzzle.solutions[0][:]
        copy_timer.stop()
        obj_timer.start()
        puzzle = Sudoku(puzzle=temp)
        obj_timer.stop()
        puzzles_found = [(0, puzzle)]

        for i in range(walks):
            # take given number of walks
            # generate populations for sampling at each step
            unsolved_cells = []
            solved_cells = []
            for k in range(self.length(puzzle)):
                if isinstance(puzzle[k], int):
                    solved_cells.append(k)
                else:
                    unsolved_cells.append(k)

            additions = 0
            removals = 0
            tosses = 0
            
            for j in range(steps):
                """ take given number of steps per walk. A 'step' is adding or
                removing two clues, where addition or removal is chosen
                randomly but proportional to the options there are. e.g., if
                the puzzle is entirely complete, it will choose to remove with
                certainty; if it is almost complete, it will choose to remove
                with near-certainty, etc. """
                p = 1 - len(unsolved_cells)/self.length(puzzle)

                """ copy previous Sudoku for alterations at this step; keep a
                pointer to previous Sudoku and cell lists in case we alter to
                an invalid puzzle at this step """
                prev_puzzle = puzzle
                copy_timer.start()
                prev_unsolved_cells = unsolved_cells[:]
                prev_solved_cells = solved_cells[:]
                temp = puzzle[:]
                copy_timer.stop()
                obj_timer.start()
                puzzle = Sudoku(puzzle=temp)
                obj_timer.stop()
                
                if np.random.random() < p:
                    # this step is a removal of clues
                    # pick two cells from solved calls
                    removals += 1
                    positions = (
                        np.random.choice(solved_cells, 2, replace=False))
                    for index in positions:
                        puzzle.remove(index)
                        unsolved_cells.append(index)
                        solved_cells.remove(index)
                else:
                    # this step is an addition of clues
                    # pick two cells from unsolved cells
                    additions += 1
                    positions = (
                        np.random.choice(unsolved_cells, 2, replace=False))
                    for index in positions:
                        if len(list(puzzle[index])) == 0:
                            # position has no candidates left; skip adding
                            break
                        value = np.random.choice(list(puzzle[index]))
                        puzzle.insert(value, index)
                        solved_cells.append(index)
                        unsolved_cells.remove(index)

                puzzle.solve(report=False)
                if puzzle.difficulty is not np.NaN:
                    # new puzzle is valid; store it
                    puzzles_found.append((puzzle.difficulty, puzzle))
                else:
                    # new puzzle is not valid; retreat to previous setup
                    tosses += 1
                    puzzle = prev_puzzle
                    unsolved_cells = prev_unsolved_cells
                    solved_cells = prev_solved_cells

            if report:
                print(f"walk {i} complete: {additions} additions, "
                      f"{removals} removals, {tosses} tosses")

                print("difficulties:\t", end=' ')
                for score, candidate in puzzles_found:
                    print(score, end=' ')
                print()

            puzzles_found.sort(reverse=True)
            puzzle = puzzles_found[0][1]
            puzzles_found = [puzzles_found[0]]

            if report:
                print(puzzles_found)

        total_timer.stop()
        print(total_timer)
        print(copy_timer)
        print(obj_timer)

        return puzzles_found[0][1]
    

    def is_valid(self, puzzle):
        """ returns True if given Sudoku object has a single solution, False
        otherwise. Runs solve() first to ensure Sudoku has a verdict.

        precondition: given puzzle is Sudoku object.
        postcondition: given Sudoku has all solutions stored and, if valid,
        a difficulty score as well (NaN otherwise). """

        try:
            puzzle.solve(report=False)
            return len(puzzle.solutions) == 1
        except AttributeError:
            print("AttributeError: is_valid() requires "
                  "a Sudoku object argument")


    def length(self, sudoku):
        """ returns number of cells in given Sudoku puzzle """
        return len(sudoku.puzzle)


gen = SudokuGenerator()
puzzle = gen.create()
print(puzzle)
print("difficulty score: ", puzzle.difficulty)
