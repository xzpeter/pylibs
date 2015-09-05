import time
import math
import random

# Define some colors
black    = (   0,   0,   0)
white    = ( 255, 255, 255)
green    = (   0, 255,   0)
blue     = (   0,   0, 255)
red      = ( 255,   0,   0)
yellow   = ( 255, 255,   0)

def debug (msg):
    print "%s: %s" % (time.strftime("%D %H:%m:%S"), msg)

def warn (msg):
    debug("WARN: " + msg)
    
def err (msg):
    debug("ERROR: " + msg)
    raise Exception(msg)

def point_in_rect (point, rect):
    x = point[0]
    y = point[1]
    if x >= rect.left and x <= rect.right and \
       y >= rect.top and y <= rect.bottom:
        return True
    return False

def rect_collide (rect1, rect2):
    points = [rect1.topleft, rect1.topright,
              rect1.bottomleft, rect1.bottomright]
    for point in points:
        if point_in_rect(point, rect2):
            return True
    return False

def vector_norm (vector):
    x = vector[0]
    y = vector[1]
    len = math.sqrt(x**2 + y**2)
    return [x/len, y/len]

def vector_mul (vector, n):
    return [vector[0]*n, vector[1]*n]

def random_vector (norm):
    x = random.random() * 2 - 1
    y = random.random() * 2 - 1
    return vector_mul(vector_norm([x,y]), norm)
