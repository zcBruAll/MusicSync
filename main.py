import math
import pygame
import random
from Utils.Midi_Utils import *
from Utils.Generators import *

pygame.init()

# Config
width = 1920
height = 1080

# Init params
spacing = 24
cols = int(width / spacing) + 1
rows = int((curveCalculation(960)) / spacing) + 1
print(cols * rows)

# Generate objects
earth = generate_earth(rows, cols, spacing)
stars = star_generator(600)

notesList = []
objects = []  # satellites list

timer = 0
videoTimer = -(15 * float(1 / 60))
soonestNote = 0

# Initialization
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()

pygame.mixer.music.load("Sounds/PinkPanther_Both.mp3")
# pygame.mixer.music.play()

notesList = readMidi('Sounds/PinkPanther.midi')
pianoNotes = seperateInstrument(notesList, 0)
trumpetNotes = seperateInstrument(notesList, 1)
minPitch, maxPitch = get_min_max_pitch(notesList)

# Checks each x and y position for the triangles, assigns them a noise value, and then a color based on it
start_time = pygame.time.get_ticks()
last_time = 0.0
running = True
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
        star.set_exploding()
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

    if timer % 3 == 0:
        earth.update()
        
    earth.draw(screen)

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