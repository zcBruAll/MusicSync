import random

from Objects.Satellite import Satellite
from Objects.Alien import Alien
from Objects.Star import Star
from Objects.Earth import *
from Objects.Moon import *
from Objects.StellarObject import *
from Utils.func_utils import *

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

def generate_Satellite(x, y, lifetime, additions):
    
    body_width = random.randint(30, 50)
    body_height = random.randint(30, 50)
    
    if random.randint(1,2) == 1:
        isRectangle = True
    else:
        isRectangle = False
        
    body_color = randomColor('white')
    
    if random.randint(1,2) == 1:
        num_wings = 1
    else:
        num_wings = 2
        
    pannel_width = random.randint(20, 30)
    pannel_height = random.randint(50, 80)
    pannel_color = randomColor('multi')
    
    return Satellite(x, y, lifetime, additions, isRectangle, body_width, body_height, body_color, pannel_width, pannel_height, num_wings, pannel_color)

def generate_Alien(x, y, lifetime, additions):
    
    body_height = random.randint(40, 60)
    body_width = random.randint(body_height, 70)
    body_color = randomColor('blue')
    
    elipse_width = random.randint(body_width + 20, 100)
    elipse_height = random.randint(30, body_height)
    elipse_color = randomColor('multi')
    
    light_color = randomColor('yellow')
    
    return Alien(x, y, lifetime, additions, body_width, body_height, body_color, elipse_width, elipse_height, elipse_color, light_color)

def star_generator(number):
    """
    Generate a number of Star with random properties.
    1. Randomly determine the number of triangles (3 to 8).
    2. Randomly determine the size of the star (4 to 8 px).
    3. Randomly determine the position of the star inside the game window
    4. Randomly determine the color of the star (white, gold, or light blue).
    """
    stars = []
    for _ in range(number):
        num_triangle = random.randint(3, 8)
        size = random.randint(3, 6)
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        color = random.choice([(255, 255, 255), (255, 215, 0), (173, 216, 230)])
        stars.append(Star(x, y, num_triangle, size, color))
    return stars

def generate_earth(rows, cols, spacing, music_length=60000, width=1920, height=1080):
    triangleList = []
    center_x = width // 2
    center_y = height  # Terre posée en bas de l’écran

    for y in range(rows):
        tempList = []
        for x in range(cols):

            # Vertices positions
            x0 = x * spacing
            x1 = (x + 1) * spacing
            x2 = x * spacing
            x3 = (x + 1) * spacing
            y0 = height - (y * spacing)
            y1 = height - (y * spacing)
            y2 = height - (y + 1) * spacing
            y3 = height - (y + 1) * spacing

            # Calcul de la courbe terrestre
            y0_temp = curveCalculation(x0)
            y1_temp = curveCalculation(x1)
            y2_temp = curveCalculation(x2)
            y3_temp = curveCalculation(x3)

            if y0 < y0_temp:
                y0 = y0_temp
            if y1 < y1_temp:
                y1 = y1_temp
            if y2 < y2_temp:
                y2 = y2_temp
            if y3 < y3_temp:
                y3 = y3_temp

            tempList.append(StellarObjectTriangle((x0, y0), (x1, y1), (x2, y2)))
            tempList.append(StellarObjectTriangle((x1, y1), (x3, y3), (x2, y2)))
        triangleList.append(tempList)

    return Earth(triangleList, center_x, center_y, music_length)