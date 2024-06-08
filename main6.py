import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "shapely"])
import pygame
from math import cos, sin, radians, sqrt, tan
from shapely.geometry import Point, Polygon

import pygame.gfxdraw
import models.chessboard as m_chessboard
import models.rook as m_rook
import models.knight as m_knight
import models.bishop as m_bishop
import models.king as m_king
import models.queen as m_queen
import models.pawn as m_pawn

# proietta = lambda p: [p[0], p[1]]
proietta = lambda p: [(p[0]*(size:=500))/((znear:=0.1)+p[2]), (p[1]*size)/(znear+p[2])]
ruota = lambda p, a: [
    (a0 := cos(radians(a[1]))) * (a1 := ((b := cos(radians(a[2]))) * p[0] + (-(c := sin(radians(a[2])))) * p[1])) + (d := sin(radians(a[1]))) * p[2],
    (e := cos(radians(a[0]))) * (b1 := (c * p[0] + b * p[1])) + (-(f := sin(radians(a[0])))) * (c1 := ((-d) * a1 + a0 * p[2])),
    f * b1 + e * c1
]
d3d = lambda p1, p2: float(sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2))
ps = lambda p1, p2: p1[0]*p2[0] + p1[1]*p2[1] + p1[2]*p2[2]

class Mouse:
    def __init__(self):
        self.pos = lambda : pygame.mouse.get_pos()
        self.lastClick = None
        self.newClick = pygame.mouse.get_pressed()[0]
        self.isClicked()
    def isClicked(self):
        self.lastClick = self.newClick
        self.newClick = pygame.mouse.get_pressed()[0]
        return self.newClick

class Piece:
    def __init__(self, screen, model, details):
        self.details = details
        self.name = self.details[2]
        self.screen = screen
        self.model = model
        self.faces = []
        for i in range(len(self.model.f)):
            p, n, c = zip(*self.model.f[i])
            p = [[(pm:=self.model.v[p[j]-1])[0]*(size := self.details[1])+self.details[0][0], pm[1]*size+self.details[0][1], pm[2]*size+self.details[0][2]] for j in range(len(p))]
            n = [self.model.n[test-1] for test in n]
            c = [self.model.c[test-1] for test in c] if self.details[3] == None else [self.details[3]]
            self.faces.append(p+[(c[0][0], c[0][1], c[0][2])]+[n[0]]+[[sum(coord) / len(p) for coord in zip(*p)]])
        self.m = [model.v[-1][_]*self.details[1] + self.details[0][_] for _ in range(3)]
        for i in range(len(self.faces)):
            self.faces[i] = self.faces[i][:-3] + [self.m] + self.faces[i][-3:]
        if self.details[5] != None:
            for i in range(len(self.faces)):
                p = []
                for j in range(len(r := self.faces[i][:-4])):
                    FpC = [self.faces[i][:-4][j][_] - self.faces[i][-4][_] for _ in range(3)]
                    FpR = ruota(FpC, self.details[5])
                    p.append([FpR[_] + self.faces[i][-4][_] for _ in range(3)])
                self.faces[i] = p + [self.faces[i][-4]] + [self.faces[i][-3]] + [ruota(self.faces[i][-2], self.details[5])] + [self.faces[i][-1]]
        self.anglen = self.angleo = [-57, 0, 0]
        self.RevolveAround = None
        self.update = False
        self.lastOrderFaces = self.faces

        
        self.mouseWasClicked = False
        self.mouseIsClicked = False
        self.selected = False
        self.firstMousePos = None
        self.delta = [0, 0]
        self.newMoves = None
        self.distance = [0, 0, 0]


    def rAround(self, p): self.RevolveAround = p
    def select(self): self.selected = True
    def deselect(self): self.selected = False
    def moves(self, pos): self.newMoves = pos
    def draw(self):
        self.mouseIsClicked = pygame.mouse.get_pressed()[0]
        if self.newMoves != None:
            if self.details[6] != self.newMoves:
                self.distance = [self.distance[0] + (self.details[6][0] - self.newMoves[0])*30, 0, self.distance[2] + (self.newMoves[1] - self.details[6][1])*30]
        
        if self.anglen != self.angleo:
            facce_ordinate = sorted(self.faces, key=lambda faccia : faccia[-1][2], reverse=True)
            self.lastOrderFaces = facce_ordinate
        else:
            facce_ordinate = self.lastOrderFaces
        
        
        
        for i in range(len(facce_ordinate)):
            p = []
            for j in range(len(facce_ordinate[i][:-4])):
                
                FpR = ruota([
                    (facce_ordinate[i][j][0]) - ((centerPoint:=self.RevolveAround if self.RevolveAround != None else facce_ordinate[i][-4]))[0] + self.distance[0],
                    (facce_ordinate[i][j][1]) - centerPoint[1] + self.distance[1],
                    (facce_ordinate[i][j][2]) - centerPoint[2] + self.distance[2],
                ], self.anglen)
                p.append([FpR[_] + centerPoint[_] for _ in range(3)])
                facce_ordinate[i][-4] = [self.m[_] - centerPoint[_] for _ in range(3)]
                facce_ordinate[i][-4] = ruota(facce_ordinate[i][-4], self.anglen)
                facce_ordinate[i][-4] = [facce_ordinate[i][-4][_] + centerPoint[_] for _ in range(3)]
            f = p + [facce_ordinate[i][-4], facce_ordinate[i][-3], ruota(facce_ordinate[i][-2], self.anglen), [sum(coord)/(len(facce_ordinate[i])-3) for coord in zip(*p)]]
            
            if ps(f[-2], (0, 0, 1)) < 0 and f[-1][2] > 0:
                r = range(len(f[1:-4]))
                if self.selected:
                    c = (255, 0, 0, 255)
                    if self.firstMousePos == None:
                        self.firstMousePos = pygame.mouse.get_pos()
                    else:
                        self.delta = [(nmp := pygame.mouse.get_pos())[0] - self.firstMousePos[0], nmp[1] - self.firstMousePos[1]]
                    
                    

                else:
                    if self.firstMousePos != None:
                        self.firstMousePos = None
                    if self.delta != [0, 0]:
                        self.delta = [0, 0]
                    c = (f[-3][0], f[-3][1], f[-3][2], 255)
                pol = [[(x1 := (s := self.screen.get_size())[0]/2)-(p:=proietta(f[0]))[0]+self.delta[0], (y := s[1]/2)-p[1]+self.delta[1]]] + [[x1-(p:=proietta(f[j+1]))[0]+self.delta[0], y-p[1]+self.delta[1]] for j in r]
                pygame.gfxdraw.filled_polygon(self.screen, pol, c)
                pygame.gfxdraw.aapolygon(self.screen, pol, self.details[4])
        
        self.revolveAround = None
        self.angleo = self.anglen
        self.mouseWasClicked = pygame.mouse.get_pressed()[0]
        
        if self.newMoves != None:
            self.details[6] = self.newMoves
            self.newMoves = None

class Rook(Piece):
    def __init__(self, screen, details): super().__init__(screen, m_rook, details)
    def availableMoves(self, pos, grind, select, n=0):
        if pos[0] > 1:
            pl = list(range(1, pos[0]))
        else:
            pl = []
        if pos[0] < 8:
            pr = list(range(pos[0]+1, 9))
        else:
            pr = []
        px = pl+pr
        if pos[1] > 1:
            pd = list(range(1, pos[1]))
        else:
            pd = []
        if pos[1] < 8:
            pu = list(range(pos[1]+1, 9))
        else:
            pu = []
        py = pd+pu
        p = [[p, pos[1]] for p in px]+[[pos[0], p] for p in py]
        indexMovesToDelete = []
        lengths = [len(pl), len(pr), len(pd), len(pu)]
        left, right, up, down = 0, 0, 0, 0
        for j in range(lengths[0]-1, -1, -1):
            if left == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    left = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths[0], lengths[0]+lengths[1]):
            if right == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    right = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths[0]+lengths[1]+lengths[2]-1, lengths[0]+lengths[1]-1, -1):
            if down == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    down = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths[0]+lengths[1]+lengths[2], lengths[0]+lengths[1]+lengths[2]+lengths[3]):
            if up == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    up = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(len(indexMovesToDelete)):
            p.remove(indexMovesToDelete[j])
        return p
class Bishop(Piece):
    def __init__(self, screen, details): super().__init__(screen, m_bishop, details)
    def availableMoves(self, pos, grind, select, n = 0):
        pa = []
        x, y = pos[0], pos[1]
        while True:
            if x > 1 and y < 8:
                pa.append([(x:=x-1), (y:=y+1)])
            else:
                break
        pb = []
        x, y = pos[0], pos[1]
        while True:
            if x < 8 and y < 8:
                pb.append([(x:=x+1), (y:=y+1)])
            else:
                break
        pc = []
        x, y = pos[0], pos[1]
        while True:
            if x < 8 and y > 1:
                pc.append([(x:=x+1), (y:=y-1)])
            else:
                break
        pd = []
        x, y = pos[0], pos[1]
        while True:
            if x > 1 and y > 1:
                pd.append([(x:=x-1), (y:=y-1)])
            else:
                break
        indexMovesToDelete = []
        lengths = [len(pa), len(pb), len(pc), len(pd)]
        p = pa+pb+pc+pd
        upLeft, upRight, downRight, downLeft = 0, 0, 0, 0
        for j in range(0, lengths[0]):
            if upLeft == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    upLeft = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths[0], lengths[0]+lengths[1]):
            if upRight == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    upRight = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths[0]+lengths[1], lengths[0]+lengths[1]+lengths[2]):
            if downRight == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    downRight = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths[0]+lengths[1]+lengths[2], lengths[0]+lengths[1]+lengths[2]+lengths[3]):
            if downLeft == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    downLeft = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(len(indexMovesToDelete)):
            p.remove(indexMovesToDelete[j])
        return p
class Knight(Piece):
    def __init__(self, screen, details): super().__init__(screen, m_knight, details)
    def availableMoves(self, pos, grind, select, n = 0):
        p = []
        if pos[0] <= 7 and pos[1] <= 6: p.append([pos[0]+1, pos[1]+2])
        if pos[0] <= 6 and pos[1] <= 7: p.append([pos[0]+2, pos[1]+1])
        if pos[0] <= 6 and pos[1] >= 2: p.append([pos[0]+2, pos[1]-1])
        if pos[0] <= 7 and pos[1] >= 3: p.append([pos[0]+1, pos[1]-2])
        if pos[0] >= 2 and pos[1] >= 3: p.append([pos[0]-1, pos[1]-2])
        if pos[0] >= 3 and pos[1] >= 2: p.append([pos[0]-2, pos[1]-1])
        if pos[0] >= 3 and pos[1] <= 7: p.append([pos[0]-2, pos[1]+1])
        if pos[0] >= 2 and pos[1] <= 6: p.append([pos[0]-1, pos[1]+2])
        indexMovesToDelete = []
        for j in range(len(p)):
            if type((move:=grind[p[j][1]-1][p[j][0]-1])) != int:
                if j not in indexMovesToDelete:
                    indexMovesToDelete.append(p[j])

        for j in range(len(indexMovesToDelete)):
            p.remove(indexMovesToDelete[j])
        return p
class King(Piece):
    def __init__(self, screen, details): super().__init__(screen, m_king, details)
    def availableMoves(self, pos, grind, select, n = 0):
        p = []
        if pos[1] < 8: p.append([pos[0], pos[1] + 1])
        if pos[0] < 8 and pos[1] < 8: p.append([pos[0] + 1, pos[1] + 1])
        if pos[0] < 8: p.append([pos[0] + 1, pos[1]])
        if pos[0] < 8 and pos[1] > 1: p.append([pos[0] + 1, pos[1] - 1])
        if pos[1] > 1: p.append([pos[0], pos[1] - 1])
        if pos[0] > 1 and pos[1] > 1: p.append([pos[0] - 1, pos[1] - 1])
        if pos[0] > 1: p.append([pos[0] - 1, pos[1]])
        if pos[0] > 1 and pos[1] < 8: p.append([pos[0] - 1, pos[1] + 1])
        indexMovesToDelete = []
        for j in range(len(p)):
            if type((move:=grind[p[j][1]-1][p[j][0]-1])) != int:
                if p[j] not in indexMovesToDelete:
                    indexMovesToDelete.append(p[j])
        for j in range(len(indexMovesToDelete)):
            p.remove(indexMovesToDelete[j])
        return p
class Queen(Piece):
    def __init__(self, screen, details): super().__init__(screen, m_queen, details)
    def availableMoves(self, pos, grind, select, n = 0):
        if pos[0] > 1:
            pleft = list(range(1, pos[0]))
        else:
            pleft = []
        if pos[0] < 8:
            pright = list(range(pos[0]+1, 9))
        else:
            pright = []
        px = pleft+pright
        if pos[1] > 1:
            pdown = list(range(1, pos[1]))
        else:
            pdown = []
        if pos[1] < 8:
            pup = list(range(pos[1]+1, 9))
        else:
            pup = []
        py = pdown+pup
        pa = []
        x, y = pos[0], pos[1]
        while True:
            if x > 1 and y < 8:
                pa.append([(x:=x-1), (y:=y+1)])
            else:
                break
        pb = []
        x, y = pos[0], pos[1]
        while True:
            if x < 8 and y < 8:
                pb.append([(x:=x+1), (y:=y+1)])
            else:
                break
        pc = []
        x, y = pos[0], pos[1]
        while True:
            if x < 8 and y > 1:
                pc.append([(x:=x+1), (y:=y-1)])
            else:
                break
        pd = []
        x, y = pos[0], pos[1]
        while True:
            if x > 1 and y > 1:
                pd.append([(x:=x-1), (y:=y-1)])
            else:
                break
        p = [[p, pos[1]] for p in px]+[[pos[0], p] for p in py]+pa+pb+pc+pd
        indexMovesToDelete = []
        lengths1 = (x:=[len(pleft), len(pright), len(pdown), len(pup)])
        lengths2 = [len(pa), len(pb), len(pc), len(pd)]
        left, right, down, up, upLeft, upRight, downRight, downLeft = 0, 0, 0, 0, 0, 0, 0, 0
        for j in range(lengths1[0]-1, -1, -1):
            if left == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    left = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths1[0], lengths1[0]+lengths1[1]):
            if right == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    right = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths1[0]+lengths1[1]+lengths1[2]-1, lengths1[0]+lengths1[1]-1, -1):
            if down == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    down = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths1[0]+lengths1[1]+lengths1[2], lengths1[0]+lengths1[1]+lengths1[2]+lengths1[3]):
            if up == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    up = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths1[0]+lengths1[1]+lengths1[2]+lengths1[3], lengths1[0]+lengths1[1]+lengths1[2]+lengths1[3]+lengths2[0]):
            if upLeft == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    upLeft = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths1[0]+lengths1[1]+lengths1[2]+lengths1[3]+lengths2[0], lengths1[0]+lengths1[1]+lengths1[2]+lengths1[3]+lengths2[0]+lengths2[1]):
            if upRight == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    upRight = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths1[0]+lengths1[1]+lengths1[2]+lengths1[3]+lengths2[0]+lengths2[1], lengths1[0]+lengths1[1]+lengths1[2]+lengths1[3]+lengths2[0]+lengths2[1]+lengths2[2]):
            if downRight == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    downRight = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(lengths1[0]+lengths1[1]+lengths1[2]+lengths1[3]+lengths2[0]+lengths2[1]+lengths2[2], lengths1[0]+lengths1[1]+lengths1[2]+lengths1[3]+lengths2[0]+lengths2[1]+lengths2[2]+lengths2[3]):
            if downLeft == 0:
                if type(grind[p[j][1]-1][p[j][0]-1]) != int:
                    downLeft = 1
            else:
                indexMovesToDelete.append(p[j])
        for j in range(len(indexMovesToDelete)):
            p.remove(indexMovesToDelete[j])
        return p
class Pawn(Piece):
    def __init__(self, screen, details):
        super().__init__(screen, m_pawn, details)
        self.movesDone = 0
    def availableMoves(self, pos, grind, select, n = 0):
        p = []
        a, b, c, d = False, False, False, False
        if self.details[7] == 0:
            if pos[0] > 1 and pos[1] < 8:
                p.append([pos[0] - 1, pos[1] + 1])
                a = True
            if pos[1] < 8:
                p.append([pos[0], pos[1] + 1])
                b = True
            if pos[1] < 7:
                p.append([pos[0], pos[1] + 2])
                c = True
            if pos[0] < 8 and pos[1] < 8:
                p.append([pos[0] + 1, pos[1] + 1])
                d = True
        else:
            if pos[0] > 1 and pos[1] > 1:
                p.append([pos[0] - 1, pos[1] - 1])
                a = True
            if pos[1] > 1:
                p.append([pos[0], pos[1] - 1])
                b = True
            if pos[1] > 2:
                p.append([pos[0], pos[1] - 2])
                c = True
            if pos[0] < 8 and pos[1] > 1:
                p.append([pos[0] + 1, pos[1] - 1])
                d = True
        indexMovesToDelete = []
        if n == 1:
            n = []
        cont = 0
        if a:
            if type(grind[p[cont][1]-1][p[cont][0]-1]) == int or grind[p[cont][1]-1][p[cont][0]-1][0].details[7] == select.details[7]:
                indexMovesToDelete.append(p[cont])
                if n != 0:
                    n.append(p[cont])
            cont += 1
        if b:
            if type(grind[p[cont+1][1]-1][p[cont+1][0]-1]) != int or type(grind[p[cont][1]-1][p[cont][0]-1]) != int or type(grind[p[cont+1][1]-1][p[cont+1][0]-1]) != int and type(grind[p[cont][1]-1][p[cont][0]-1]) != int:
                indexMovesToDelete.append(p[cont+1])
            cont += 1
        if c:
            if type(grind[p[cont-1][1]-1][p[cont-1][0]-1]) != int:
                indexMovesToDelete.append(p[cont-1])
            cont += 1
        if d:
            if type(grind[p[cont][1]-1][p[cont][0]-1]) == int or grind[p[cont][1]-1][p[cont][0]-1][0].details[7] == select.details[7]:
                indexMovesToDelete.append(p[cont])
                if n != 0:
                    n.append(p[cont])
        for j in range(len(indexMovesToDelete)):
            p.remove(indexMovesToDelete[j])
        if n == 0:
            return p
        else:
            return n

class Chessboard:
    def __init__(self, screen, details):
        self.opponents = ["bianco", "nero"]
        self.switch = False
        self.turn = 0
        self.details = details
        self.name = self.details[2]
        self.screen = screen
        self.coda = 5

        self.faces = []
        for i in range(len(m_chessboard.f)):
            p, n, c = zip(*m_chessboard.f[i])
            p = [[(pm:=m_chessboard.v[p[j]-1])[0]*(size := +self.details[1])+self.details[0][0], pm[1]*size+self.details[0][1], pm[2]*size+self.details[0][2]] for j in range(len(p))]
            n = [m_chessboard.n[test-1] for test in n]
            c = [m_chessboard.c[test-1] for test in c] if self.details[3] == None else [self.details[3]]
            self.faces.append(p+[(c[0][0], c[0][1], c[0][2])]+[n[0]]+[[sum(coord) / len(p) for coord in zip(*p)]])
        self.m = [m_chessboard.v[-1][_]*self.details[1] + self.details[0][_] for _ in range(3)]
        for i in range(len(self.faces)):
            self.faces[i] = self.faces[i][:-3] + [i, self.m] + self.faces[i][-3:]
        
        if self.details[5] != None:
            for i in range(len(self.faces)):
                p = []
                for j in range(len(r := self.faces[i][:-self.coda])):
                    FpC = [self.faces[i][:-self.coda][j][_] - self.faces[i][-4][_] for _ in range(3)]
                    FpR = ruota(FpC, self.details[5])
                    p.append([FpR[_] + self.faces[i][-4][_] for _ in range(3)])
                self.faces[i] = p + [self.faces[i][-5], self.faces[i][-4]] + [self.faces[i][-3]] + [ruota(self.faces[i][-2], self.details[5])] + [self.faces[i][-1]]
        self.anglen = self.angleo = [-57, 0, 0]
        self.RevolveAround = None
        self.update = False
        self.lastOrderFaces = self.faces
        self.select = None
        self.mouseWasClicked = False
        self.mouseIsClicked = False
        self.mousePos = None
        self.pieces = [
            Pawn(self.screen, [[+1*(15+30*3), 15, 600 + 30 - 270], 15,   "pawn", (200, 200, 200), (59, 127, 100), None, [1, 2], 0]),
            Pawn(self.screen, [[+1*(15+30*2), 15, 600 + 30 - 270], 15,   "pawn", (200, 200, 200), (59, 127, 100), None, [2, 2], 0]),
            Pawn(self.screen, [[+1*(15+30*1), 15, 600 + 30 - 270], 15,   "pawn", (200, 200, 200), (59, 127, 100), None, [3, 2], 0]),
            Pawn(self.screen, [[+1*(15+30*0), 15, 600 + 30 - 270], 15,   "pawn", (200, 200, 200), (59, 127, 100), None, [4, 2], 0]),
            Pawn(self.screen, [[-1*(15+30*0), 15, 600 + 30 - 270], 15,   "pawn", (200, 200, 200), (59, 127, 100), None, [5, 2], 0]),
            Pawn(self.screen, [[-1*(15+30*1), 15, 600 + 30 - 270], 15,   "pawn", (200, 200, 200), (59, 127, 100), None, [6, 2], 0]),
            Pawn(self.screen, [[-1*(15+30*2), 15, 600 + 30 - 270], 15,   "pawn", (200, 200, 200), (59, 127, 100), None, [7, 2], 0]),
            Pawn(self.screen, [[-1*(15+30*3), 15, 600 + 30 - 270], 15,   "pawn", (200, 200, 200), (59, 127, 100), None, [8, 2], 0]),
            Rook(self.screen, [[-1*(15+30*3), 15, 600 + 0  - 270], 15,   "rook", (200, 200, 200), (59, 127, 100), None, [8, 1], 0]),
            Rook(self.screen, [[+1*(15+30*3), 15, 600 + 0  - 270], 15,   "rook", (200, 200, 200), (59, 127, 100), None, [1, 1], 0]),
            Knight(self.screen, [[-1*(15+30*2), 15, 600 + 0  - 270], 15, "knight", (200, 200, 200), (59, 127, 100), None, [7, 1], 0]),
            Knight(self.screen, [[+1*(15+30*2), 15, 600 + 0  - 270], 15, "knight", (200, 200, 200), (59, 127, 100), None, [2, 1], 0]),
            Bishop(self.screen, [[-1*(15+30*1), 15, 600 + 0  - 270], 15, "bishop", (200, 200, 200), (59, 127, 100), None, [6, 1], 0]),
            Bishop(self.screen, [[+1*(15+30*1), 15, 600 + 0  - 270], 15, "bishop", (200, 200, 200), (59, 127, 100), None, [3, 1], 0]),
            King(self.screen, [[-1*(15+30*0), 15, 600 + 0  - 270], 15,   "king", (200, 200, 200), (59, 127, 100), None, [5, 1], 0]),
            Queen(self.screen, [[+1*(15+30*0), 15, 600 + 0  - 270], 15,  "queen", (200, 200, 200), (59, 127, 100), None, [4, 1], 0]),
            Pawn(self.screen, [[+1*(15+30*3), 15, 600 + 0  - 90], 15,   "pawn", (0, 0, 0), (100, 200, 200), (0, 180, 0), [1, 7], 1]),
            Pawn(self.screen, [[+1*(15+30*2), 15, 600 + 0  - 90], 15,   "pawn", (0, 0, 0), (100, 200, 200), (0, 180, 0), [2, 7], 1]),
            Pawn(self.screen, [[+1*(15+30*1), 15, 600 + 0  - 90], 15,   "pawn", (0, 0, 0), (100, 200, 200), (0, 180, 0), [3, 7], 1]),
            Pawn(self.screen, [[+1*(15+30*0), 15, 600 + 0  - 90], 15,   "pawn", (0, 0, 0), (100, 200, 200), (0, 180, 0), [4, 7], 1]),
            Pawn(self.screen, [[-1*(15+30*0), 15, 600 + 0  - 90], 15,   "pawn", (0, 0, 0), (100, 200, 200), (0, 180, 0), [5, 7], 1]),
            Pawn(self.screen, [[-1*(15+30*1), 15, 600 + 0  - 90], 15,   "pawn", (0, 0, 0), (100, 200, 200), (0, 180, 0), [6, 7], 1]),
            Pawn(self.screen, [[-1*(15+30*2), 15, 600 + 0  - 90], 15,   "pawn", (0, 0, 0), (100, 200, 200), (0, 180, 0), [7, 7], 1]),
            Pawn(self.screen, [[-1*(15+30*3), 15, 600 + 0  - 90], 15,   "pawn", (0, 0, 0), (100, 200, 200), (0, 180, 0), [8, 7], 1]),
            Rook(self.screen, [[-1*(15+30*3), 15, 600 + 30 - 90], 15,   "rook", (0, 0, 0), (100, 200, 200), (0, 180, 0), [8, 8], 1]),
            Rook(self.screen, [[+1*(15+30*3), 15, 600 + 30 - 90], 15,   "rook", (0, 0, 0), (100, 200, 200), (0, 180, 0), [1, 8], 1]),
            Knight(self.screen, [[-1*(15+30*2), 15, 600 + 30 - 90], 15, "knight", (0, 0, 0), (100, 200, 200), (0, 180, 0), [7, 8], 1]),
            Knight(self.screen, [[+1*(15+30*2), 15, 600 + 30 - 90], 15, "knight", (0, 0, 0), (100, 200, 200), (0, 180, 0), [2, 8], 1]),
            Bishop(self.screen, [[-1*(15+30*1), 15, 600 + 30 - 90], 15, "bishop", (0, 0, 0), (100, 200, 200), (0, 180, 0), [6, 8], 1]),
            Bishop(self.screen, [[+1*(15+30*1), 15, 600 + 30 - 90], 15, "bishop", (0, 0, 0), (100, 200, 200), (0, 180, 0), [3, 8], 1]),
            King(self.screen, [[-1*(15+30*0), 15, 600 + 30 - 90], 15,   "king", (0, 0, 0), (100, 200, 200), (0, 180, 0), [5, 8], 1]),
            Queen(self.screen, [[+1*(15+30*0), 15, 600 + 30 - 90], 15,  "queen", (0, 0, 0), (100, 200, 200), (0, 180, 0), [4, 8], 1])
        ]
        self.kingFreeMoves = None
        self.kingBudyMoves = None
        self.kingMoveConfirm = None
        self.check = False
        self.checkmate = False
    def rAround(self, p): self.RevolveAround = p
    def draw(self):
        mousePos = None
        currentAvailableMoves = None
        canMove = False
        grind = [[0 for i in range(8)] for j in range(8)]
        self.mouseIsClicked = pygame.mouse.get_pressed()[0]
        if self.anglen != self.angleo:
            facce_ordinate = sorted(self.faces, key=lambda faccia : faccia[-1][2], reverse=True)
            self.lastOrderFaces = facce_ordinate
        else: facce_ordinate = self.lastOrderFaces
        for i in range(len(facce_ordinate)):
            p = []
            for j in range(len(facce_ordinate[i][:-self.coda])):
                FpR = ruota([facce_ordinate[i][j][_] - ((centerPoint:=self.RevolveAround if self.RevolveAround != None else facce_ordinate[i][-4]) if _ == 0 else centerPoint)[_] for _ in range(3)], self.anglen)
                p.append([FpR[_] + centerPoint[_] for _ in range(3)])

                facce_ordinate[i][-4] = [self.m[_] - centerPoint[_] for _ in range(3)]
                facce_ordinate[i][-4] = ruota(facce_ordinate[i][-4], self.anglen)
                facce_ordinate[i][-4] = [facce_ordinate[i][-4][_] + centerPoint[_] for _ in range(3)]
            f = p + [facce_ordinate[i][-5], facce_ordinate[i][-4], facce_ordinate[i][-3], ruota(facce_ordinate[i][-2], self.anglen), [sum(coord)/(len(facce_ordinate[i])-self.coda) for coord in zip(*p)]]
            if ps(f[-2], (0, 0, 1)) < 0 and f[-1][2] > 0:
                r = range(len(f[1:-self.coda]))
                pol = [[(x1 := (s := self.screen.get_size())[0]/2)-(p:=proietta(f[0]))[0], (y := s[1]/2)-p[1]]] + [[x1-(p:=proietta(f[j+1]))[0], y-p[1]] for j in r]
                pygame.gfxdraw.filled_polygon(self.screen, pol, (f[-3][0], f[-3][1], f[-3][2], 255))
                pygame.gfxdraw.aapolygon(self.screen, pol, self.details[4])

                for obj in self.pieces:
                    grind[obj.details[6][1]-1][obj.details[6][0]-1] = [obj, 0]

                
                if Polygon(pol).contains(Point((pos := pygame.mouse.get_pos())[0], pos[1])) and f[-5] < 64:
                    if self.mouseIsClicked:
                        if not self.mouseWasClicked:
                            for obj in self.pieces:
                                if obj.details[6] == [f[-5]%8+1, f[-5]//8+1]:
                                    if obj.details[7] == self.turn:
                                        if self.select != None:
                                            self.select.deselect()
                                        obj.select()
                                        self.select = obj
                                        break
                    else:
                        if self.mouseWasClicked:
                            if self.select != None:
                                availableMoves = self.select.availableMoves(self.select.details[6], grind, self.select)
                                canMove = True
                                mousePos = [f[-5]%8+1, f[-5]//8+1]
                                currentAvailableMoves = availableMoves


        # aggiorna griglia
        opponentMoves = []
        selfMoves = []
        grind[self.pieces[14+16*self.turn].details[6][1]-1][self.pieces[14+16*self.turn].details[6][0]-1] = grind[self.pieces[14+16*self.turn].details[6][1]-1][self.pieces[14+16*self.turn].details[6][0]-1][1]
        for piece in self.pieces:
            if piece.details[7] != self.turn:
                for m in piece.availableMoves(piece.details[6], grind, piece, 1):
                    if type(grind[m[1]-1][m[0]-1]) == int: grind[m[1]-1][m[0]-1] += 1
                    else: grind[m[1]-1][m[0]-1][1] += 1
                    opponentMoves.append(m)
            else:
                for m in piece.availableMoves(piece.details[6], grind, piece):
                    selfMoves.append(m)
        grind[self.pieces[14+16*self.turn].details[6][1]-1][self.pieces[14+16*self.turn].details[6][0]-1] = [self.pieces[14+16*self.turn], grind[self.pieces[14+16*self.turn].details[6][1]-1][self.pieces[14+16*self.turn].details[6][0]-1]]
        kingFreeMoves = []
        kingBudyMoves = []
        for mossapossibile in self.pieces[14+16*self.turn].availableMoves(self.pieces[14+16*self.turn].details[6], grind, self.pieces[14+16*self.turn], 1):
            if not mossapossibile in opponentMoves: kingFreeMoves.append(mossapossibile)
            else: kingBudyMoves.append(mossapossibile)
        kingsRescueMoves = []
        for mossapossibile in kingBudyMoves:
            if mossapossibile in selfMoves: kingsRescueMoves.append(mossapossibile)
        if grind[self.pieces[14+16*self.turn].details[6][1]-1][self.pieces[14+16*self.turn].details[6][0]-1][1] > 0:
            if not self.check:
                self.check = True
            if len(kingFreeMoves) == 0:
                self.checkmate = True
            if self.checkmate:
                print(f"vince il {self.opponents[-1*self.turn+1]}")
        else:
            if self.check:
                self.check = False
        
        if canMove:
            if mousePos in currentAvailableMoves:
                
                if self.select.name == "pawn":
                    if self.select.details[7] == 0:
                        if self.select.movesDone == 0: self.select.movesDone = 1
                        elif mousePos == [self.select.details[6][0], self.select.details[6][1]+2]: canMove = False
                    else:
                        if self.select.movesDone == 0: self.select.movesDone = 1
                        elif mousePos == [self.select.details[6][0], self.select.details[6][1]-2]: canMove = False
                if canMove:
                    if type(grind[mousePos[1]-1][mousePos[0]-1]) != int:
                        if grind[mousePos[1]-1][mousePos[0]-1][0].name != "king":
                            for j in range(len(self.pieces)):
                                if self.pieces[j].details[7] != self.select.details[7]:
                                    if self.pieces[j].details[6] == grind[mousePos[1]-1][mousePos[0]-1][0].details[6]:
                                        del self.pieces[j]
                                        break
                    if type(grind[mousePos[1]-1][mousePos[0]-1]) == int:
                        self.select.moves(mousePos)
                        self.switch = True
            self.select.deselect()
            self.select = None
        self.revolveAround = None
        self.angleo = self.anglen
        self.mouseWasClicked = pygame.mouse.get_pressed()[0]

        if not self.mouseIsClicked:
            if self.mouseWasClicked:
                if self.select != None:
                    self.select.deselect()
                self.select = None

class App:
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.board = Chessboard(self.screen, [[0, 0, 0], 15, "chessboard", None, (255, 0, 0), None, None, None])
        self.rSpeed = 15
        self.run()
    
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
            if self.board.switch == True:
                self.board.turn = -self.board.turn + 1
                self.board.switch = False
            orderOBJ = sorted(
                [p for p in self.board.pieces],
                key=lambda obj : obj.lastOrderFaces[0][-4][2],
                reverse=True
            )
            self.screen.fill((255, 255, 255))
            for obj in [self.board] + orderOBJ:
                obj.rAround(self.board.m)
                obj.draw()
                if obj.anglen[1]<180 and self.board.turn:
                    obj.anglen[1] += self.rSpeed
                elif obj.anglen[1]>0 and not self.board.turn:
                    obj.anglen[1] -= self.rSpeed
            pygame.display.update()
            pygame.time.Clock().tick(120)
App()

