import sys
import pygame
from pygame.locals import *
from utils import *

class Sprite (object):
    def __init__ (self, image_path=None, size=None, pos=(0, 0)):
        if image_path:
            self.image = pygame.image.load(image_path).convert_alpha()
            if size:
                # need resizing
                self.image = pygame.transform.scale(self.image, size)
        else:
            err("Image is required for Sprite")
        # self.rect stores the current position of the sprite
        self.rect = self.image.get_rect().move(pos[0], pos[1])
        # which world this sprite belongs to
        self.world = None

    def __str__(self):
        return self.__class__.__name__

    def size (self):
        return (self.rect.width, self.rect.height)

    def collide (self, other):
        """Check whether this sprite collide with the other sprite, if so,
        return the colliding sprite, or None if no collision happened.
        `other' could be one single sprite or a list of sprites """
        if type(other) == type(self):
            sprites = [other]
        else:
            sprites = other
        for sprite in sprites:
            if rect_collide(self.rect, sprite.rect):
                return sprite
        return None

    def decorate (self, screen):
        """This function is used to decorate the specific sprite. For each
        sprite, it should (in many cases) contain not only the rendered
        image, but some decorations (e.g., boxs around it) to mark the
        sprite. By default, there is no decoration. Please redefine this
        function when needed. (should refers to self.rect when requiring
        current sprite position) """
        pass

    def update (self, msec):
        """Update sprite condition since msec passed. By default, nothing
        is done."""
        pass

    def over_left (self):
        return self.rect.left < 0

    def over_right (self):
        size = self.world.get_size()
        return self.rect.right > size[0]

    def over_top (self):
        return self.rect.top < 0

    def over_bottom (self):
        size = self.world.get_size()
        return self.rect.bottom > size[1]

    def render (self, screen):
        screen.blit(self.image, self.rect)
        self.decorate(screen)

class World (object):
    """The gaming world. There could have entities in the world. For now,
    there could have only one gaming world."""
    def __init__ (self, bg_color=(0,0,0), size=(800, 600)):
        # first, init pygame
        pygame.init()

        # init self
        self.bg_color = bg_color
        # stores all the entities in the gaming world
        self.sprites = []
        self.screen = pygame.display.set_mode(size)

    def __str__ (self):
        return "World (Sprites: %s)" % ", ".join(self.sprites)

    def get_size (self):
        return self.screen.get_size()

    def add_sprite (self, sprite):
        debug("Adding sprite: %s" % sprite)
        self.sprites.append(sprite)
        sprite.world = self

    def add_sprites (self, sprites):
        for sprite in sprites:
            self.add_sprite(sprite)

    def remove_sprite (self, sprite):
        if sprite in self.sprites:
            self.sprites.remove(sprite)
            sprite.world = None

    def update (self, msec):
        """Update the world since `msec' micro-seconds have passed. Notify
        all the sprites about this."""
        for sprite in self.sprites:
            sprite.update(msec)

    def render (self):
        # we will draw bg before all entities
        self.screen.fill(self.bg_color)
        for sprite in self.sprites:
            sprite.render(self.screen)
        pygame.display.update()

class Game (object):
    """The whole game admin, managing the world and also interactive with
    the user. """
    def __init__ (self, name="TestGame", framerate=30, world=None):
        self.name = name
        self.framerate = framerate
        self.clock = pygame.time.Clock()
        pygame.display.set_caption(name)
        if not world:
            world = World()
        self.world = world

    def handle_key (self, type, key):
        debug("Key %s pressed" % pygame.key.name(key))

    def run (self):
        """Start the game!"""
        while 1:
            for event in pygame.event.get():
                if event.type == QUIT:
                    sys.exit()
                elif event.type == KEYDOWN:
                    self.handle_key(KEYDOWN, event.key)

            self.world.render()
            msec = self.clock.tick(self.framerate)
            self.world.update(msec)
