import random
from abc import ABC, abstractmethod
from cube_model import RubiksCube


class BaseSolver(ABC):
   

    def __init__(self, cube: RubiksCube):
        self._cube = cube

    @abstractmethod
    def solve(self) -> list[str]:
        ...

    @staticmethod
    def inverse_move(move: str) -> str:
        if move.endswith("'"):
            return move[:-1]
        return move + "'"

    @staticmethod
    def inverse_sequence(moves: list[str]) -> list[str]:
        return [BaseSolver.inverse_move(m) for m in reversed(moves)]


class ReverseSolver(BaseSolver):

    def solve(self) -> list[str]:
        #compute the solution by inverting the move history
        return self.inverse_sequence(self._cube.history)


#scram
class Scrambler:
    
    MOVES = ["R", "L", "U", "D", "F", "B",
             "R'", "L'", "U'", "D'", "F'", "B'"]

    def __init__(self, length: int = 20):
        self._length = length

    def generate(self) -> list[str]:
        scramble = []
        last_face = ""
        for _ in range(self._length):
            while True:
                move = random.choice(self.MOVES)
                face = move[0]
                if face != last_face:
                    break
            scramble.append(move)
            last_face = face
        return scramble

    def scramble_cube(self, cube: RubiksCube) -> list[str]:
        moves = self.generate()
        cube.do_moves(moves, record=True)
        return moves

