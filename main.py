import math
import pygame
import random
from Objects.Moon import *
from Utils.Midi_Utils import *
from Utils.Generators import *

pygame.init()

# Config
width = 1920
height = 1080

# Init params
spacing = 24
cols = int(width / spacing) + 1
rows = int((curveCalculation(width/2)) / spacing) + 1

timer = 0

stars = star_generator(600)
objects = []

# Initialization
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()

pygame.mixer.music.load("Sounds/Ecossaise_Both.mp3")
pygame.mixer.music.play()

music_length = 60000

# Generate objects
earth = generate_earth(rows, cols, spacing, music_length)
moon = Moon(rows, cols, spacing, earth.center_x, earth.center_y * 2, orbit_radius=2150, moon_radius=200, collide_earth_ms=music_length)

notesList = readMidi('Sounds/Ecossaise_Beethoven.mid')
pianoNotes = seperateInstrument(notesList, 0)
trumpetNotes = seperateInstrument(notesList, 1)

minPitch, maxPitch = get_min_max_pitch(notesList)
stars = star_generator(len(pianoNotes) + len(trumpetNotes))

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
        
    # Drawing background
    elapsed_time_s = round((pygame.time.get_ticks() - start_time) / 1000,2)
    new_piano_notes = [note for note in pianoNotes
                if last_time < note.start <= elapsed_time_s]

    new_trumpet_notes = [note for note in trumpetNotes
            if last_time < note.start <= elapsed_time_s]
        
    for note in new_trumpet_notes:
        star = get_random_stars(stars)
        star.set_exploding()
        star.move_angle = random.uniform(0, 2 * math.pi)

    for note in new_piano_notes:
        star = get_random_stars(stars)
        star.set_moving()
        star.move_angle = random.uniform(0, 2 * math.pi)
            
    """
    for each star update graphics and rotate them
    """
    for star in stars:
        star.update(screen)
        star.draw(screen)
        star.rotation += star.rotation_speed

        if star.state is None or star.is_off_screen(SCREEN_WIDTH, SCREEN_HEIGHT):
            stars.remove(star)
            
    earth.update(elapsed_time_s*1000)
    earth.draw(screen)
        
    moon.update(elapsed_time_s*1000)
    moon.draw(screen)
        
    # Find the start for each instrument
    new_trumpet_notes = [note for note in trumpetNotes
                        if last_time < note.start <= elapsed_time_s]
    new_piano_notes = [note for note in pianoNotes
                        if last_time < note.start <= elapsed_time_s]
    
    # Generate Satellite or Alien when a note begins
    if new_trumpet_notes not in (None, []):
        y = int(trumpetNotes[0].pitch - minPitch) * int(height / (maxPitch - minPitch))
        x = width - 50
        instru = generate_Alien(x,y, noteLifetime(trumpetNotes[0]), velocityRange(trumpetNotes, trumpetNotes[0]))
        objects.append(instru)
        del trumpetNotes[0]

    if new_piano_notes not in (None, []):
        y = int(new_piano_notes[0].pitch - minPitch) * int(height / (maxPitch - minPitch))
        x = 50
        instru = generate_Satellite(x, y, noteLifetime(pianoNotes[0]), velocityRange(pianoNotes, pianoNotes[0]))
        print(pianoNotes[0].velocity)
        objects.append(instru)
        del pianoNotes[0]
    
    # Draw all satellites and aliens
    for obj in objects[:]:
        obj.update()
        if obj.life_time <= 0:
            objects.remove(obj)
        else:
            obj.draw(screen)    
        
    last_time = elapsed_time_s

    pygame.display.flip()
    clock.tick(60)  # limits FPS to 60
    # print(clock.get_fps())

pygame.quit()