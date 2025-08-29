import math
import time

import pygame
import random
from Midi_Utils import *
from Generators import *
import noise

pygame.init()


#       Functions
def curveCalculation(x):
    return 1080 - ((x / 3200) * (1920 - x) + 100)
    # 1080 - the result so that it creates the curve at the bottom of the screen and not at the top


def colorGreen():
    return ((0, random.randint(150, 255), 0))


def colorBlue():
    return ((0, random.randint(0, 100), random.randint(225, 255)))

def get_random_stars(stars):
    available = [s for s in stars if not s.isMoving]  # filtre
    if available:  # vérifie qu'il en reste
        return random.choice(available)
    return None  # si toutes les étoiles bougent déjà


#       Config
width = 1920
height = 1080

spacing = 24
scale = 20.0
cols = int(width / spacing) + 1
rows = int((curveCalculation(960)) / spacing) + 1
print(cols * rows)
running = True
defaultLeft = True

notesList = []
triangleList = []  # Triangles for the planet
objects = []  # satellites list

timer = 0
videoTimer = -(15 * float(1 / 60))
soonestNote = 0


#       Classes
class EarthTriangle:
    def __init__(self, p1: tuple, p2: tuple, p3: tuple):
        self.p1 = list(p1)
        self.p2 = list(p2)
        self.p3 = list(p3)
        self.rgb1 = 0
        self.rgb2 = 0
        self.rgb3 = 0
        self.color = (self.rgb1, self.rgb2, self.rgb3)

    def chooseColor(self, color):
        self.rgb1 = color[0]
        self.rgb2 = color[1]
        self.rgb3 = color[2]
        self.color = (self.rgb1, self.rgb2, self.rgb3)


#       Initialization
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
pygame.mixer.music.load("Sounds/PinkPanther_Both.mp3")
pygame.mixer.music.play()


# Creating all the triangles before the loop makes for a way better performance
for y in range(rows):
    tempList = []
    for x in range(cols):

        # Vertices positions
        x0 = x * spacing
        x1 = (x + 1) * spacing
        x2 = x * spacing
        x3 = (x + 1) * spacing
        y0 = 1080 - (y * spacing)
        y1 = 1080 - (y * spacing)
        y2 = 1080 - (y + 1) * spacing
        y3 = 1080 - (y + 1) * spacing

        # Here we make it so that if any vertex goes "above" the curve it will relocate to the curve instead
        if (y0 < curveCalculation(x0)):
            y0 = curveCalculation(x0)
        if (y1 < curveCalculation(x1)):
            y1 = curveCalculation(x1)
        if (y2 < curveCalculation(x2)):
            y2 = curveCalculation(x2)
        if (y3 < curveCalculation(x3)):
            y3 = curveCalculation(x3)

        tempList.append((EarthTriangle((x0, y0), (x1, y1), (x2, y2))))
        tempList.append(EarthTriangle((x1, y1), (x3, y3), (x2, y2)))
    triangleList.append(tempList)
    # Here we create a list of lists with inside each tuple of EarthTriangles that form a rectangle
    # It's made like this to easily access the colors of nearby triangles


notesList = readMidi('Sounds/PinkPanther.midi')
pianoNotes = seperateInstrument(notesList, 0)
trumpetNotes = seperateInstrument(notesList, 1)

# Calculating the max pitch and min pitch (used later to determine the Y position of the notes)
maxPitch = 0
minPitch = notesList[0][0].pitch
for k in notesList:
    for i in k:
        if (i.pitch > maxPitch):
            maxPitch = i.pitch
        elif (i.pitch < minPitch):
            minPitch = i.pitch


#       Noise procedural generation
randomOffset = random.randint(1,1000)
def noiseValue(x,y, scale = 0.1, octaves = 4):
    val = noise.pnoise2((x + randomOffset) * scale, (y + randomOffset) * scale, octaves)
    return (val + 1)/2

# Checks each x and y position for the triangles, assigns them a noise value, and then a color based on it
for y in range (len(triangleList) - 1):
    for x in range(len(triangleList[y]) - 1):
        n = noiseValue(x,y, scale = 0.05)
        if (n > 0.5):
            triangleList[y][x].chooseColor(colorGreen())
        else:
            triangleList[y][x].chooseColor(colorBlue())


start_time = pygame.time.get_ticks()
last_time = 0.0
stars = star_generator(300)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((10, 10, 25))
    timer += 1
    videoTimer += float(1 / 60)
    
    #Drawing background
    elapsed_time_s = round((pygame.time.get_ticks() - start_time) / 1000,2)
    new_notes = [note for note in trumpetNotes 
                 if last_time < note.start <= elapsed_time_s]

    if new_notes not in (None, []):
        star = get_random_stars(stars)
        star.isMoving = True
        star.move_angle = random.uniform(0, 2 * math.pi)

    last_time = elapsed_time_s

    """
    for each star update graphics and rotate them
    """
    for star in stars:
        star.update(screen)
        star.draw(screen)
        star.rotation += star.rotation_speed
        
        if star.is_off_screen(SCREEN_WIDTH, SCREEN_HEIGHT):
            stars.remove(star)

    # Drawing all the triangles
    for i in triangleList:
        for j in range(len(i)):
            pygame.draw.polygon(screen, i[j].color, (i[j].p1, i[j].p2, i[j].p3))
            pygame.draw.polygon(screen, i[j].color, (i[j].p1, i[j].p2, i[j].p3))

    if timer > 60:
        randomOffset -= 1
        #   Changes the color just like during initialization, while moving the offset to rotate the planet
        for y in range(len(triangleList)):
            for x in range(len(triangleList[y])):
                n = noiseValue(x, y, scale=0.05)
                if n > 0.5:
                    triangleList[y][x].chooseColor(colorGreen())
                else:
                    triangleList[y][x].chooseColor(colorBlue())
        timer = 0

    # "Calculating" the soonest note to start
    if (((float(notesList[0][0].start))) < ((float(notesList[1][0].start)))):
        soonestNote = 0
    else:
        soonestNote = 1

    # draw satellites and aliens
    for obj in objects[:]:
        obj.update()
        if obj.life_time <= 0:
            objects.remove(obj)
        else:
            obj.draw(screen)

    # Creation of the "satellites and ovnis"
    if (videoTimer >= (float(notesList[soonestNote][0].start))):
        y = int((notesList[soonestNote][0].pitch - minPitch) * (int(1080 / (maxPitch - minPitch))))
        if (y > height):
            y = height
        if (soonestNote == 1 and not trumpetNotes == []):
            x = 50
            instru = generate_Satellite(x,y, noteLifetime(notesList[soonestNote][0]), velocityRange(notesList[soonestNote][0]))
        elif (not pianoNotes == []):
            x = width - 50
            instru = generate_Alien(x,y, noteLifetime(notesList[soonestNote][0]), velocityRange(notesList[soonestNote][0]))
        objects.append(instru)
        del notesList[soonestNote][0]

    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()