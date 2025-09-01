import math
import pygame
import random
from Objects.Moon import *
from Utils.Midi_Utils import *
from Utils.Generators import *

pygame.init()

stars = []
objects = []
notesList = []
pianoNotes = []
trumpetNotes = []
minPitch, maxPitch = None,None
stars = 0
music_length = 0
# Generate objects
earth = None
moon = None

def init_simu():
    global stars, objects, notesList, pianoNotes, trumpetNotes, minPitch, maxPitch, music_length, earth, moon
    objects = []
    notesList = readMidi(midi_path)
    pianoNotes = seperateInstrument(notesList, 0)
    trumpetNotes = seperateInstrument(notesList, 1)
    minPitch, maxPitch = get_min_max_pitch(notesList)
    stars = star_generator(len(pianoNotes) + len(trumpetNotes))
    music_length = pretty_midi.PrettyMIDI(midi_path).get_end_time() * 1000
    # Generate objects
    earth = generate_earth(rows, cols, spacing, music_length)
    moon = Moon(rows, cols, spacing, earth.center_x, earth.center_y * 2, orbit_radius=2150, moon_radius=200, collide_earth_ms=music_length)
    pygame.mixer.music.load(mp3_path)
    pygame.mixer.music.play()


midi_path = 'Sounds/SSB.mid'
mp3_path = 'Sounds/SSB.mp3'

# Config
width = 1920
height = 1080

# Init params
spacing = 24
cols = int(width / spacing) + 1
rows = int((curveCalculation(width/2)) / spacing) + 1

# Initialization
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
init_simu()

# Checks each x and y position for the triangles, assigns them a noise value, and then a color based on it
start_time = pygame.time.get_ticks()
last_time = 0.0
big_bang_triangles = []
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((10, 10, 25))
    elapsed_time_s = round((pygame.time.get_ticks() - start_time) / 1000,2)
        
    if music_length - (elapsed_time_s*1000) > 0:
        # Drawing background
        new_piano_notes = [note for note in pianoNotes
                    if last_time < note.start <= elapsed_time_s]

        new_trumpet_notes = [note for note in trumpetNotes
                if last_time < note.start <= elapsed_time_s]
            
        if stars != []:
            for note in new_trumpet_notes:
                star = get_random_stars(stars)
                star.set_exploding()
                star.move_angle = random.uniform(0, 2 * math.pi)

        if stars != []:
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
                
        if earth is not None:
            earth.update(elapsed_time_s*1000)
            earth.draw(screen)

        if moon is not None:
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

    if music_length - (elapsed_time_s*1000) <= 2000:
        if big_bang_triangles == []:
            cx, cy = earth.center_x, earth.center_y-300   # explosion center

            for _ in range(5000):  # number of fragments
                # Start all points close to the center
                p1 = (cx + random.randint(-10, 10), cy + random.randint(-10, 10))
                p2 = (cx + random.randint(-10, 10), cy + random.randint(-10, 10))
                p3 = (cx + random.randint(-10, 10), cy + random.randint(-10, 10))

                # Velocity vector: random direction, outward from center
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(15, 40)
                vel = (math.cos(angle) * speed, math.sin(angle) * speed)

                big_bang_triangles.append({"points": [p1, p2, p3], "vel": vel})
        
        new_triangles = []
        for tri in big_bang_triangles:
            dx, dy = tri["vel"]
            tri["points"] = [(x + dx, y + dy) for (x, y) in tri["points"]]

            color = (
                random.randint(180, 255),
                random.randint(80, 200),
                random.randint(50, 150)
            )

            pygame.draw.polygon(screen, color, tri["points"])
            new_triangles.append(tri)

        big_bang_triangles = new_triangles

    if music_length - (elapsed_time_s*1000) <= -1000:
        init_simu()
        elapsed_time_s = 0
        big_bang_triangles = []
        start_time = pygame.time.get_ticks()

    last_time = elapsed_time_s

    pygame.display.flip()
    clock.tick(60)  # limits FPS to 60
    # print(clock.get_fps())

pygame.quit()