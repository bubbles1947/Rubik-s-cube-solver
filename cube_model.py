from enum import Enum
from copy import deepcopy

class Color(Enum):
    WHITE  = "W"
    YELLOW = "Y"
    RED    = "R"
    ORANGE = "O"
    BLUE   = "B"
    GREEN  = "G"

    def __repr__(self):
        return self.value

class Face:

    def __init__(self, color: Color):
        self._grid = [[color for _ in range(3)] for _ in range(3)]

    @property
    def grid(self) -> list[list[Color]]:
        return self._grid

    def get(self, row: int, col: int) -> Color:
        return self._grid[row][col]

    def set(self, row: int, col: int, color: Color):
        self._grid[row][col] = color

    def get_row(self, row: int) -> list[Color]:
        return list(self._grid[row])

    def get_col(self, col: int) -> list[Color]:
        return [self._grid[r][col] for r in range(3)]

    def set_row(self, row: int, values: list[Color]):
        for c in range(3):
            self._grid[row][c] = values[c]

    def set_col(self, col: int, values: list[Color]):
        for r in range(3):
            self._grid[r][col] = values[r]

    def rotate_clockwise(self):
        g = self._grid
        self._grid = [
            [g[2][0], g[1][0], g[0][0]],
            [g[2][1], g[1][1], g[0][1]],
            [g[2][2], g[1][2], g[0][2]],
        ]

    def rotate_counter_clockwise(self):
        g = self._grid
        self._grid = [
            [g[0][2], g[1][2], g[2][2]],
            [g[0][1], g[1][1], g[2][1]],
            [g[0][0], g[1][0], g[2][0]],
        ]

    def is_solved(self) -> bool:
        first = self._grid[0][0]
        return all(self._grid[r][c] == first for r in range(3) for c in range(3))

    def __repr__(self):
        rows = []
        for r in range(3):
            rows.append(" ".join(c.value for c in self._grid[r]))
        return "\n".join(rows)


#full/cube
class RubiksCube:
   
    #class-level constant: the 6 canonical move names
    MOVE_NAMES = ["R", "L", "U", "D", "F", "B",
                  "R'", "L'", "U'", "D'", "F'", "B'"]

    def __init__(self):
        #creat a soolved cuve
        self.faces: dict[str, Face] = {
            "U": Face(Color.WHITE),
            "D": Face(Color.YELLOW),
            "F": Face(Color.GREEN),
            "B": Face(Color.BLUE),
            "L": Face(Color.ORANGE),
            "R": Face(Color.RED),
        }
        #move history for the solver to reverse
        self._history: list[str] = []

    #public helpers
    @property
    def history(self) -> list[str]:
        return list(self._history)

    @property
    def move_count(self) -> int:
        return len(self._history)

    def is_solved(self) -> bool:
        return all(face.is_solved() for face in self.faces.values())

    def reset(self):
        self.__init__()

    def clone(self) -> "RubiksCube":
        return deepcopy(self)

    #generic move dispatcher
    def do_move(self, move: str, record: bool = True):
        
        dispatch = {
            "R": self._R,  "R'": self._R_prime,
            "L": self._L,  "L'": self._L_prime,
            "U": self._U,  "U'": self._U_prime,
            "D": self._D,  "D'": self._D_prime,
            "F": self._F,  "F'": self._F_prime,
            "B": self._B,  "B'": self._B_prime,
        }
        if move not in dispatch:
            raise ValueError(f"unknown move: {move}")
        dispatch[move]()
        if record:
            self._history.append(move)

    def do_moves(self, moves: list[str], record: bool = True):
        for m in moves:
            self.do_move(m, record)

    def clear_history(self):
        self._history.clear()

    #the 12 basic moves (6 faces × CW/CCW) 
    #each move: rotate the target face, then cycle the 4 adjecent strips

    def _R(self):
        #right face clockwise
        self.faces["R"].rotate_clockwise()
        f_col = self.faces["F"].get_col(2)
        u_col = self.faces["U"].get_col(2)
        b_col = self.faces["B"].get_col(0)
        d_col = self.faces["D"].get_col(2)

        self.faces["U"].set_col(2, f_col)
        self.faces["B"].set_col(0, list(reversed(u_col)))
        self.faces["D"].set_col(2, list(reversed(b_col)))
        self.faces["F"].set_col(2, d_col)

    def _R_prime(self):
        #right face counter-clockwise
        for _ in range(3):
            self._R()

    def _L(self):
        #left face clockwise
        self.faces["L"].rotate_clockwise()
        f_col = self.faces["F"].get_col(0)
        u_col = self.faces["U"].get_col(0)
        b_col = self.faces["B"].get_col(2)
        d_col = self.faces["D"].get_col(0)

        self.faces["D"].set_col(0, f_col)
        self.faces["F"].set_col(0, u_col)
        self.faces["U"].set_col(0, list(reversed(b_col)))
        self.faces["B"].set_col(2, list(reversed(d_col)))

    def _L_prime(self):
        for _ in range(3):
            self._L()

    def _U(self):
        #up face clockwise
        self.faces["U"].rotate_clockwise()
        f_row = self.faces["F"].get_row(0)
        l_row = self.faces["L"].get_row(0)
        b_row = self.faces["B"].get_row(0)
        r_row = self.faces["R"].get_row(0)

        self.faces["L"].set_row(0, f_row)
        self.faces["B"].set_row(0, l_row)
        self.faces["R"].set_row(0, b_row)
        self.faces["F"].set_row(0, r_row)

    def _U_prime(self):
        for _ in range(3):
            self._U()

    def _D(self):
        #down face clockwise
        self.faces["D"].rotate_clockwise()
        f_row = self.faces["F"].get_row(2)
        l_row = self.faces["L"].get_row(2)
        b_row = self.faces["B"].get_row(2)
        r_row = self.faces["R"].get_row(2)

        self.faces["R"].set_row(2, f_row)
        self.faces["B"].set_row(2, r_row)
        self.faces["L"].set_row(2, b_row)
        self.faces["F"].set_row(2, l_row)

    def _D_prime(self):
        for _ in range(3):
            self._D()

    def _F(self):
        #front face clockwise
        self.faces["F"].rotate_clockwise()
        u_row = self.faces["U"].get_row(2)
        r_col = self.faces["R"].get_col(0)
        d_row = self.faces["D"].get_row(0)
        l_col = self.faces["L"].get_col(2)

        self.faces["R"].set_col(0, u_row)
        self.faces["D"].set_row(0, list(reversed(r_col)))
        self.faces["L"].set_col(2, d_row)
        self.faces["U"].set_row(2, list(reversed(l_col)))

    def _F_prime(self):
        for _ in range(3):
            self._F()

    def _B(self):
        #back face clockwise
        self.faces["B"].rotate_clockwise()
        u_row = self.faces["U"].get_row(0)
        r_col = self.faces["R"].get_col(2)
        d_row = self.faces["D"].get_row(2)
        l_col = self.faces["L"].get_col(0)

        self.faces["L"].set_col(0, list(reversed(u_row)))
        self.faces["U"].set_row(0, r_col)
        self.faces["R"].set_col(2, list(reversed(d_row)))
        self.faces["D"].set_row(2, l_col)

    def _B_prime(self):
        for _ in range(3):
            self._B()

    def __repr__(self):
        lines = []
        for name, face in self.faces.items():
            lines.append(f"--- {name} ---")
            lines.append(repr(face))
        return "\n".join(lines)

