import math
import pygame
from cube_model import RubiksCube, Color
from cube_solver import ReverseSolver, Scrambler


#constants
WINDOW_W, WINDOW_H = 1060, 710
FPS = 60

#vivid cube sticker colours
COLORS = {
    Color.WHITE:  (240, 240, 240),
    Color.YELLOW: (255, 213, 0),
    Color.RED:    (200, 30, 30),
    Color.ORANGE: (255, 130, 0),
    Color.BLUE:   (0, 70, 200),
    Color.GREEN:  (0, 160, 50),
}

BG_COLOR     = (28, 30, 38)
GRID_COLOR   = (18, 18, 24)
TEXT_COLOR    = (225, 225, 230)
ACCENT       = (80, 190, 255)
BTN_COLOR    = (52, 55, 68)
BTN_HOVER    = (72, 75, 92)
BTN_ACTIVE   = (40, 150, 210)
PANEL_BG     = (38, 40, 50)
PANEL_BORDER = (62, 65, 80)
LABEL_DIM    = (130, 130, 145)
SOLVED_GREEN = (50, 210, 100)


def shade_color(color: tuple, factor: float) -> tuple:
    #multiply each RGB channel by *factor*, clamped to 0-255
    return tuple(max(0, min(255, int(c * factor))) for c in color)


#button
class Button:
    #an clickable button with hover / active visual feedback

    def __init__(self, x, y, w, h, label, callback, font,
                 color=BTN_COLOR, hover_color=BTN_HOVER,
                 active_color=BTN_ACTIVE, text_color=TEXT_COLOR,
                 radius=6):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.callback = callback
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.active_color = active_color
        self.text_color = text_color
        self.radius = radius
        self._hovered = False
        self._pressed = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self.rect.collidepoint(event.pos):
                self.callback()
            self._pressed = False

    def draw(self, surface):
        col = (self.active_color if self._pressed
               else self.hover_color if self._hovered
               else self.color)
        pygame.draw.rect(surface, col, self.rect, border_radius=self.radius)
        pygame.draw.rect(surface, PANEL_BORDER, self.rect, 1,
                         border_radius=self.radius)
        txt = self.font.render(self.label, True, self.text_color)
        surface.blit(txt, txt.get_rect(center=self.rect.center))


#cubeRenderer
class CubeRenderer:
    #draws a RubiksCube as a 2-D net and an interactive 3-D projection

    #normal vectors for each cube face (unit, in model space)
    FACE_NORMALS = {
        "F": ( 0,  0,  1),
        "B": ( 0,  0, -1),
        "U": ( 0,  1,  0),
        "D": ( 0, -1,  0),
        "R": ( 1,  0,  0),
        "L": (-1,  0,  0),
    }

    def __init__(self, cube: RubiksCube):
        self._cube = cube

    #2-D unfolded net
    def draw_net(self, surface, ox, oy, cell=20, gap=2,
                 label_font=None):
        """
        the standard cross-shaped net>

                 [U]
            [L]  [F]  [R]  [B]
                 [D]
        """
        face_sz = cell * 3 + gap * 4

        layout = {
            "U": (1, 0),
            "L": (0, 1), "F": (1, 1), "R": (2, 1), "B": (3, 1),
            "D": (1, 2),
        }

        for name, (gc, gr) in layout.items():
            fx = ox + gc * face_sz
            fy = oy + gr * face_sz
            face = self._cube.faces[name]

            #dark backing
            pygame.draw.rect(surface, GRID_COLOR,
                             (fx, fy, face_sz, face_sz), border_radius=3)

            #sticker cells
            for r in range(3):
                for c in range(3):
                    color = COLORS[face.get(r, c)]
                    cx = fx + gap + c * (cell + gap)
                    cy = fy + gap + r * (cell + gap)
                    pygame.draw.rect(surface, color,
                                     (cx, cy, cell, cell), border_radius=3)

            #bold face label (shadow + white text)
            if label_font:
                center = (fx + face_sz // 2, fy + face_sz // 2)
                shadow = label_font.render(name, True, (0, 0, 0))
                main   = label_font.render(name, True, (255, 255, 255))
                surface.blit(shadow,
                             shadow.get_rect(center=(center[0]+1, center[1]+1)))
                surface.blit(main, main.get_rect(center=center))

    #3-D helpers
    def _face_cells(self, face_name):
        #Return 9 quads as (row, col, [(x,y,z) * 4]) in model space
        cells = []
        for r in range(3):
            for c in range(3):
                if face_name == "F":
                    x0, x1 = c - 1.5, c - 0.5
                    y0, y1 = 0.5 - r, 1.5 - r
                    corners = [(x0,y0,1.5),(x1,y0,1.5),
                               (x1,y1,1.5),(x0,y1,1.5)]
                elif face_name == "B":
                    x0, x1 = 0.5 - c, 1.5 - c
                    y0, y1 = 0.5 - r, 1.5 - r
                    corners = [(x0,y0,-1.5),(x1,y0,-1.5),
                               (x1,y1,-1.5),(x0,y1,-1.5)]
                elif face_name == "U":
                    x0, x1 = c - 1.5, c - 0.5
                    z0, z1 = r - 1.5, r - 0.5
                    corners = [(x0,1.5,z0),(x1,1.5,z0),
                               (x1,1.5,z1),(x0,1.5,z1)]
                elif face_name == "D":
                    x0, x1 = c - 1.5, c - 0.5
                    z0, z1 = 0.5 - r, 1.5 - r
                    corners = [(x0,-1.5,z0),(x1,-1.5,z0),
                               (x1,-1.5,z1),(x0,-1.5,z1)]
                elif face_name == "R":
                    z0, z1 = 0.5 - c, 1.5 - c
                    y0, y1 = 0.5 - r, 1.5 - r
                    corners = [(1.5,y0,z0),(1.5,y0,z1),
                               (1.5,y1,z1),(1.5,y1,z0)]
                elif face_name == "L":
                    z0, z1 = c - 1.5, c - 0.5
                    y0, y1 = 0.5 - r, 1.5 - r
                    corners = [(- 1.5,y0,z0),(-1.5,y0,z1),
                               (-1.5,y1,z1),(-1.5,y1,z0)]
                else:
                    continue
                cells.append((r, c, corners))
        return cells

    @staticmethod
    def _inset(pts, px=1.5):
        #shrink a polygon toward its centroid for a sticker-gap effect
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        out = []
        for p in pts:
            dx, dy = p[0] - mx, p[1] - my
            d = math.hypot(dx, dy)
            if d > 0:
                f = max(0.0, (d - px) / d)
                out.append((mx + dx * f, my + dy * f))
            else:
                out.append(p)
        return out

    #3-D rotatable projection
    def draw_3d(self, surface, cx, cy, scale=52,
                yaw=0.55, pitch=-0.4, label_font=None):
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)

        def rotate(x, y, z):
            #yaw (around Y)
            x1 =  x * cos_y + z * sin_y
            z1 = -x * sin_y + z * cos_y
            #pitch (around X)
            y2 =  y * cos_p - z1 * sin_p
            z2 =  y * sin_p + z1 * cos_p
            return x1, y2, z2

        def project(x, y, z):
            rx, ry, rz = rotate(x, y, z)
            return (cx + rx * scale, cy - ry * scale, rz)

        #normalised light direction (from top-right-front)
        lx, ly, lz = 0.3, 0.6, 0.7
        ll = math.sqrt(lx*lx + ly*ly + lz*lz)
        lx, ly, lz = lx/ll, ly/ll, lz/ll

        #collect visible cells
        draw_list = []        #(depth, screen_pts, colour)
        visible_names = []    #for face labels

        for fname, (nx, ny, nz) in self.FACE_NORMALS.items():
            rnx, rny, rnz = rotate(nx, ny, nz)
            if rnz <= 0.01:      #back-facing or edge-on > skip
                continue
            visible_names.append(fname)

            #directional shade
            dot = rnx * lx + rny * ly + rnz * lz
            shade = 0.52 + max(0.0, dot) * 0.48

            face_obj = self._cube.faces[fname]
            for r, c, corners3 in self._face_cells(fname):
                pts2 = []
                dsum = 0.0
                for px, py, pz in corners3:
                    sx, sy, sz = project(px, py, pz)
                    pts2.append((sx, sy))
                    dsum += sz
                base = COLORS[face_obj.get(r, c)]
                draw_list.append((dsum / 4, pts2, shade_color(base, shade)))

        #sort back-to-front (painter's algorithm)
        draw_list.sort(key=lambda t: t[0])

        for _, pts, col in draw_list:
            inner = self._inset(pts, 2.0)
            pygame.draw.polygon(surface, col, inner)
            pygame.draw.aalines(surface, GRID_COLOR, True, inner)

        #face labels in 3-D
        if label_font:
            for fname in visible_names:
                nx, ny, nz = self.FACE_NORMALS[fname]
                sx, sy, _ = project(1.5*nx, 1.5*ny, 1.5*nz)
                lbl = label_font.render(fname, True, (255, 255, 255))
                lbl.set_alpha(55)
                surface.blit(lbl, lbl.get_rect(center=(sx, sy)))


#animationManager
class AnimationManager:
    #queuees moves and applies them with a timed delay

    def __init__(self, delay_ms=120):
        self._delay = delay_ms
        self._queue: list[str] = []
        self._timer = 0
        self._active = False

    @property
    def is_animating(self) -> bool:
        return self._active

    def enqueue(self, moves: list[str]):
        self._queue.extend(moves)
        if not self._active:
            self._active = True
            self._timer = pygame.time.get_ticks()

    def update(self, cube: RubiksCube) -> bool:
        if not self._active or not self._queue:
            return False
        now = pygame.time.get_ticks()
        if now - self._timer >= self._delay:
            cube.do_move(self._queue.pop(0))
            self._timer = now
            if not self._queue:
                self._active = False
            return True
        return False


#cubeapp
class CubeApp:
    #top-level application, composes model, view and controller

    #panel rectangles (explicit, no overlap)
    _P3D   = pygame.Rect(15,  62, 570, 458)   #3-D view
    _PNET  = pygame.Rect(600, 62, 440, 255)   #net view
    _PHIST = pygame.Rect(600, 326, 440, 62)   #history
    _PKEYS = pygame.Rect(600, 396, 440, 124)  #shortcuts

    def __init__(self):
        pygame.init()
        self._screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Rubik's Cube Solver")
        self._clock = pygame.time.Clock()
        self._running = True

        #fonts
        self._f_sm  = pygame.font.SysFont("Segoe UI", 15)
        self._f_md  = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self._f_lg  = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self._f_ttl = pygame.font.SysFont("Segoe UI", 30, bold=True)
        self._f_net_label = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self._f_3d_label  = pygame.font.SysFont("Segoe UI", 16, bold=True)

        #model
        self._cube = RubiksCube()
        self._renderer = CubeRenderer(self._cube)
        self._scrambler = Scrambler(length=20)
        self._animator = AnimationManager(delay_ms=100)

        #3-D view rotation state
        self._yaw   = 0.55
        self._pitch = -0.42
        self._dragging   = False
        self._drag_start = (0, 0)
        self._drag_yaw0  = 0.0
        self._drag_pitch0 = 0.0

        #status
        self._status = "have fun bros!!!"
        self._solve_moves: list[str] = []

        #buttons
        self._buttons: list[Button] = []
        self._create_buttons()

    #buttons
    def _create_buttons(self):
        f = self._f_md
        bw, bh, g = 58, 36, 6
        x0, y1 = 30, 540
        y2 = y1 + bh + g

        for i, m in enumerate(["R","L","U","D","F","B"]):
            self._buttons.append(
                Button(x0 + i*(bw+g), y1, bw, bh, m,
                       lambda mv=m: self._do_move(mv), f))
        for i, m in enumerate(["R'","L'","U'","D'","F'","B'"]):
            self._buttons.append(
                Button(x0 + i*(bw+g), y2, bw, bh, m,
                       lambda mv=m: self._do_move(mv), f))

        ax = x0 + 6*(bw+g) + 24
        aw = 108
        self._buttons += [
            Button(ax,      y1, aw, bh, "Scramble", self._scramble, f,
                   color=(100,60,30), hover_color=(140,85,40)),
            Button(ax,      y2, aw, bh, "Solve",    self._solve,    f,
                   color=(25,95,55), hover_color=(35,135,75)),
            Button(ax+aw+g, y1, aw, bh, "Reset",    self._reset,    f,
                   color=(100,35,35), hover_color=(140,50,50)),
            Button(ax+aw+g, y2, aw, bh, "Undo",     self._undo,     f,
                   color=(55,55,100), hover_color=(75,75,140)),
        ]

    #actions
    def _do_move(self, move):
        if not self._animator.is_animating:
            self._animator.enqueue([move])
            self._status = f"Move: {move}"
            self._solve_moves.clear()

    def _scramble(self):
        if self._animator.is_animating:
            return
        self._cube.reset()
        moves = self._scrambler.scramble_cube(self._cube)
        self._solve_moves.clear()
        self._status = f"scrambled ({len(moves)} moves)"

    def _solve(self):
        if self._animator.is_animating:
            return
        if self._cube.is_solved():
            self._status = "already solved"
            return
        sol = ReverseSolver(self._cube).solve()
        self._solve_moves = list(sol)
        self._animator.enqueue(sol)
        self._status = f"solving ({len(sol)} moves)"

    def _reset(self):
        if self._animator.is_animating:
            return
        self._cube.reset()
        self._solve_moves.clear()
        self._status = "cube reset."

    def _undo(self):
        if self._animator.is_animating:
            return
        h = self._cube.history
        if not h:
            self._status = "nothing to undo."
            return
        last = h[-1]
        self._cube.do_move(ReverseSolver.inverse_move(last), record=False)
        self._cube._history.pop()
        self._status = f"undid {last}"

    #keyboard
    def _on_key(self, key, mods):
        shift = mods & pygame.KMOD_SHIFT
        move_map = {
            pygame.K_r: ("R'","R"), pygame.K_l: ("L'","L"),
            pygame.K_u: ("U'","U"), pygame.K_d: ("D'","D"),
            pygame.K_f: ("F'","F"), pygame.K_b: ("B'","B"),
        }
        if key in move_map:
            self._do_move(move_map[key][0] if shift else move_map[key][1])
        elif key == pygame.K_s:
            self._scramble()
        elif key == pygame.K_SPACE:
            self._solve()
        elif key == pygame.K_ESCAPE:
            self._reset()
        elif key == pygame.K_z:
            self._undo()

            #3-D view rotation
        elif key == pygame.K_LEFT:
            self._yaw -= 0.15
        elif key == pygame.K_RIGHT:
            self._yaw += 0.15
        elif key == pygame.K_UP:
            self._pitch = max(-1.3, self._pitch - 0.15)
        elif key == pygame.K_DOWN:
            self._pitch = min(1.3, self._pitch + 0.15)
        elif key == pygame.K_v:
            self._yaw, self._pitch = 0.55, -0.42

#drawing helpers
    @staticmethod
    def _panel(surface, rect, title="", font=None):
        pygame.draw.rect(surface, PANEL_BG, rect, border_radius=8)
        pygame.draw.rect(surface, PANEL_BORDER, rect, 1, border_radius=8)
        if title and font:
            surface.blit(font.render(title, True, ACCENT),
                         (rect.x + 14, rect.y + 8))

    def _draw_status(self, surface):
        bar = pygame.Rect(0, WINDOW_H - 38, WINDOW_W, 38)
        pygame.draw.rect(surface, (24, 26, 32), bar)
        pygame.draw.line(surface, PANEL_BORDER,
                         (0, bar.y), (WINDOW_W, bar.y))
        surface.blit(self._f_sm.render(self._status, True, TEXT_COLOR),
                     (16, WINDOW_H - 30))
        if self._cube.is_solved():
            r = self._f_md.render("SOLVED", True, SOLVED_GREEN)
        else:
            r = self._f_md.render(f"Moves: {self._cube.move_count}",
                                  True, LABEL_DIM)
        surface.blit(r, (WINDOW_W - r.get_width() - 16, WINDOW_H - 31))

    def _draw_history(self, surface):
        r = self._PHIST
        self._panel(surface, r, "Move History", self._f_md)
        h = self._cube.history
        text = ("... " if len(h) > 18 else "") + " ".join(h[-18:]) \
               if h else "(no moves yet)"
        t = self._f_sm.render(text, True, LABEL_DIM)
        clip = pygame.Rect(r.x+12, r.y+30, r.w-24, 26)
        surface.set_clip(clip)
        surface.blit(t, (r.x+14, r.y+33))
        surface.set_clip(None)

    def _draw_shortcuts(self, surface):
        r = self._PKEYS
        self._panel(surface, r, "Keyboard Shortcuts", self._f_md)
        rows = [
            ("R / L / U / D / F / B",  "Clockwise move"),
            ("Shift + Rotation-key",            "Counter-clockwise"),
            ("S >  Scramble  |  Space  Solve", ""),
            ("Z > Undo  |  Esc  Reset", ""),
            ("Arrows > Drag  Rotate view  |  V > Reset view", ""),
        ]
        for i, (left, right) in enumerate(rows):
            ty = r.y + 35 + i * 17
            surface.blit(self._f_sm.render(left, True, ACCENT),
                         (r.x + 16, ty))
            if right:
                lw = self._f_sm.size(left)[0]
                surface.blit(self._f_sm.render("  " + right, True, LABEL_DIM),
                             (r.x + 16 + lw, ty))

    #main loop
    def run(self):
        while self._running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self._running = False
                elif ev.type == pygame.KEYDOWN:
                    self._on_key(ev.key, ev.mod)

                #3-D drag rotation
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self._P3D.collidepoint(ev.pos):
                        self._dragging = True
                        self._drag_start  = ev.pos
                        self._drag_yaw0   = self._yaw
                        self._drag_pitch0 = self._pitch
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                    self._dragging = False
                if ev.type == pygame.MOUSEMOTION and self._dragging:
                    dx = ev.pos[0] - self._drag_start[0]
                    dy = ev.pos[1] - self._drag_start[1]
                    self._yaw   = self._drag_yaw0   + dx * 0.007
                    self._pitch = self._drag_pitch0  - dy * 0.007
                    self._pitch = max(-1.3, min(1.3, self._pitch))

                #buttons (3-D panel and buttons don't overlap, safe)
                for b in self._buttons:
                    b.handle_event(ev)

            #animation tick
            if self._animator.update(self._cube):
                if self._cube.is_solved() and self._solve_moves:
                    self._status = f"solved ({len(self._solve_moves)} moves)"

            #render
            self._screen.fill(BG_COLOR)


            #title
            self._screen.blit(
                self._f_ttl.render("Rubik's Cube Solver", True, ACCENT),
                (28, 16))

            #3-D panel
            self._panel(self._screen, self._P3D, "3D View", self._f_md)
            self._renderer.draw_3d(
                self._screen,
                cx=self._P3D.centerx,
                cy=self._P3D.centery + 8,
                scale=52,
                yaw=self._yaw,
                pitch=self._pitch,
                label_font=self._f_3d_label)
            #drag hint
            hint = self._f_sm.render("drag to rotate  |  arrows / V",
                                     True, (70, 70, 85))
            self._screen.blit(hint,
                              (self._P3D.x + 14,
                               self._P3D.bottom - 22))

            #net panel
            self._panel(self._screen, self._PNET,
                        "Net View  (all 6 faces)", self._f_md)
            self._renderer.draw_net(
                self._screen,
                ox=self._PNET.x + 16,
                oy=self._PNET.y + 36,
                cell=20, gap=2,
                label_font=self._f_net_label)

            #history + shortcuts
            self._draw_history(self._screen)
            self._draw_shortcuts(self._screen)

            #buttons
            for b in self._buttons:
                b.draw(self._screen)

            #status bar
            self._draw_status(self._screen)

            pygame.display.flip()
            self._clock.tick(FPS)

        pygame.quit()
