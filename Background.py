import math
import random
import pygame
import pretty_midi
from Objects.Star import Star

def star_generator(number):
    stars = []
    for _ in range(number):
        num_triangle = random.randint(3, 8)
        size = random.randint(4, 8)
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        color = random.choice([(255, 255, 255), (255, 215, 0), (173, 216, 230)])
        stars.append(Star(x, y, num_triangle, size, color))
    return stars

def get_random_stars(stars):
    return random.choice(stars)

midi = pretty_midi.PrettyMIDI('./Sounds/Ecossaise_Beethoven.mid')
all_piano_notes = [note for inst in midi.instruments for note in inst.notes if inst.program == 0]
all_piano_notes.sort(key=lambda note: note.start)

pygame.init()
pygame.mixer.init()
pygame.mixer.music.load("./Sounds/Ecossaise_Piano.mp3")
pygame.mixer.music.play()

SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
running = True
stars = star_generator(300)

start_time = pygame.time.get_ticks()
last_time = 0.0

while running:
    elapsed_time_s = round((pygame.time.get_ticks() - start_time) / 1000,2)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    screen.fill((10,10,25))
    # RENDER YOUR GAME HERE
    
    #get nearest note from elapsed_time with 0.005 difference
    new_notes = [note for note in all_piano_notes 
                 if last_time < note.start <= elapsed_time_s]

    if new_notes not in (None, []):
        star = get_random_stars(stars)
        star.isMoving = True
        star.move_angle = random.uniform(0, 2 * math.pi)

    last_time = elapsed_time_s

    for star in stars:
        star.update()
        star.draw(screen)
        star.rotation += 0.01
        
    pygame.display.flip()

    clock.tick(60)



pygame.quit()