import sys
import pygame
from random import randint
from engine import *
from utils import *

DWARF_SIZE = (100, 100)
DWARF_PER_TEAM = 6

class Dwarf (Sprite):
    STA_IDLE = 0
    STA_RUN = 1
    STA_FIGHT = 2

    RUN_INTERVAL = 3000          # ms
    RUN_LENGTH = 1000            # ms
    RUN_STEP = 5                 # pixels
    def __init__ (self, pos, team):
        Sprite.__init__(self, "dwarf.png", DWARF_SIZE, pos)
        self.team = team
        self.tick = randint(1, Dwarf.RUN_INTERVAL * 0.9)
        self.status = Dwarf.STA_IDLE
        # acceleration
        self.acc = [0, 0]
        self.health = 100

    def decorate (self, screen):
        mid = list(self.rect.midbottom)
        mid[1] -= 10
        points = (mid, (mid[0]-5, mid[1]+5), (mid[0]+5, mid[1]+5))
        pygame.draw.polygon(screen, self.team, points)

    def get_random_acc (self):
        return random_vector(Dwarf.RUN_STEP)

    def lose_health (self):
        self.health -= randint(1, 30)

    def go_back(self):
        self.acc = vector_mul(self.acc, -1)

    def fight (self, other):
        """Two dwarf fight! It's bloody!"""
        for dwarf in [self, other]:
            dwarf.lose_health()
            dwarf.go_back()

    def update (self, msec):
        # do tick. When reach 
        self.tick += msec

        if self.status == Dwarf.STA_IDLE:
            if self.tick >= Dwarf.RUN_INTERVAL:
                # start running
                self.tick = 0
                self.acc = self.get_random_acc()
                self.status = Dwarf.STA_RUN
            else:
                # do nothing
                pass
        elif self.status == Dwarf.STA_RUN:
            if self.tick >= Dwarf.RUN_LENGTH:
                # stop run
                self.tick = 0
                self.acc = [0, 0]
                self.status = Dwarf.STA_IDLE
            else:
                self.rect = self.rect.move(*self.acc)
                if self.over_left() or self.over_right():
                    self.acc[0] = -self.acc[0]
                if self.over_top() or self.over_bottom():
                    self.acc[1] = -self.acc[1]

class DwarfWorld (World):
    def __init__ (self):
        World.__init__(self)
        self.group = {}
        self.group[red] = []
        self.group[green] = []

    def member_add (self, team, dwarf):
        self.add_sprite(dwarf)
        self.group[team].append(dwarf)

    def update (self, msec):
        World.update(self, msec)
        # if there are collision between teams, then fight
        for dwarf in self.group[red]:
            opponent = dwarf.collide(self.group[green])
            if opponent:
                dwarf.fight(opponent)
                debug("Fight happened, red health %s, green %s" %\
                      (dwarf.health, opponent.health))
        # clean up the dead corpse
        for sprite in self.sprites:
            if sprite.health <= 0:
                debug("Sprite dead, removing corpse")
                self.group[sprite.team].remove(sprite)
                self.remove_sprite(sprite)

class DwarfFight (Game):
    def __init__ (self):
        world = DwarfWorld()
        Game.__init__(self, name="Dwarf Fight", framerate=30, world=world)

        window_size = self.world.get_size()
        avail_rect = (window_size[0] - DWARF_SIZE[0],
                      window_size[1] - DWARF_SIZE[1])
        dwarfs = []
        for team in [green, red]:
            count = 0
            while 1:
                dwarf = Dwarf((randint(0, avail_rect[0]),
                               randint(0, avail_rect[1])),
                              team)
                if dwarf.collide(dwarfs):
                    continue
                world.member_add(team, dwarf)
                dwarfs.append(dwarf)
                count += 1
                if count == DWARF_PER_TEAM:
                    break

game = DwarfFight()
game.run()
