import random

def randomColor(color_name):
    if color_name == 'yellow':
        return (255, random.randint(230, 255), random.randint(1,255))
    
    if color_name == 'purple':
        return (random.randint(160, 190), random.randint(150, 175), random.randint(200, 220))
    
    if color_name == 'white':
        return (random.randint(220, 255),  random.randint(220, 255),  random.randint(220, 255))
    
    if color_name == 'blue':
        hex = random.randint(20, 170)
        return (hex, random.randint(hex, hex+20) , random.randint(120, 225))
    
    if color_name == 'multi':
        return (random.randint(92, 183), random.randint(92, 183), random.randint(92, 183))
    
    if color_name == 'earth green':
        return (0, random.randint(150, 200), 0)
    
    if color_name == 'earth blue':
        return (0, random.randint(0, 50), random.randint(200, 225))
    
#       Functions
def curveCalculation(x):
    return 1080 - ((x / 3200) * (1920 - x) + 100)
    # 1080 - the result so that it creates the curve at the bottom of the screen and not at the top
    
def colorGreen():
        return ((0, random.randint(150, 255), 0))

def colorBlue():
    return ((0, random.randint(0, 100), random.randint(225, 255)))

def get_random_stars(stars):
    available = [s for s in stars if s.is_static()]  # filtre
    if available:  # vérifie qu'il en reste
        return random.choice(available)
    return None  # si toutes les étoiles bougent déjà