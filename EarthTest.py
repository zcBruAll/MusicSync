import pygame
import random
import pretty_midi
from instruments import *

# pygame setup
pygame.init()

width = 1920
height = 1080

screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
running = True


#Function to calculate the curve
def curveCalculation(x):
    return 1080 - ((x/3200)*(1920-x) + 100)
    # 1080 - the result so that it creates the curve at the bottom of the screen and not at the top


#Config of the triangles
spacing = 24
scale = 20.0
cols = int(width/spacing)+1
rows = int((curveCalculation(960))/spacing)+1



class Sattelite:
    def __init__(self, startOfNote, endOfNote, noteVelocity):
        self.p1 = [0,random.randint(0,1080)]
        self.p2 = [0,random.randint(0,1080)]
        self.p3 = [150,random.randint(0,1080)]
        self.drawingCoordinates = (self.p1,self.p2,self.p3)
        self.lifeOfNote = float(endOfNote - startOfNote)
        self.tTL = int(self.lifeOfNote * 200)
        self.speed = int(noteVelocity/30)
        self.color = (255,255,255)

    def move(self):
        self.p1[0] += self.speed
        self.p2[0] += self.speed
        self.p3[0] += self.speed



class EarthTriangle:
    def __init__(self,p1 : tuple, p2 : tuple, p3 : tuple):
        self.p1 = list(p1)
        self.p2 = list(p2)
        self.p3 = list(p3)
        self.rgb1 = 0
        self.rgb2 = 0
        self.rgb3 = 0
        self.defineColor()

        self.color = (self.rgb1, self.rgb2, self.rgb3)

    #This function is used to redefine a new random color
    #It's used at the start and every time the earth "rotates" so that we don't just have lines of color
    def defineColor(self):
        if (random.random() < 0.03):
            self.rgb1 = 0
            self.rgb2 = random.randint(0,100)
            self.rgb3 = random.randint(250,255)
        else:
            self.rgb1 = 0
            self.rgb2 = random.randint(150,255)
            self.rgb3 = 0

    #This function "moves" the color to the right
    def changeColor(self,upEarthTriangle):
        self.rgb1 = upEarthTriangle.rgb1
        self.rgb2 = upEarthTriangle.rgb2
        self.rgb3 = upEarthTriangle.rgb3
        self.color = (self.rgb1, self.rgb2, self.rgb3)

    

    
        

#Creating all the triangles before the loop makes for a wayy better performance
triangleList = []
for y in range(rows):
    tempList = []
    for x in range(cols):

        # Vertices positions
        x0 = x*spacing
        x1 = (x+1)*spacing
        x2 = x*spacing
        x3 = (x+1)*spacing
        y0 = 1080 - (y*spacing)
        y1 = 1080 - (y*spacing)
        y2 = 1080 - (y+1)*spacing
        y3 = 1080 - (y+1)*spacing

        #Here we make it so that if any vertex g5oes "above" the curve it will relocate to the curve instead
        if (y0 < curveCalculation(x0)):
            y0 = curveCalculation(x0)
        if (y1 < curveCalculation(x1)):
            y1 = curveCalculation(x1)
        if (y2 < curveCalculation(x2)):
            y2 = curveCalculation(x2)
        if (y3 < curveCalculation(x3)):
            y3 = curveCalculation(x3)  
                
        tempList.append((EarthTriangle((x0,y0),(x1,y1),(x2,y2)),EarthTriangle((x1,y1),(x3,y3),(x2,y2))))
    triangleList.append(tempList)
    #Here we create a list of lists with inside each tuple of EarthTriangles that form a rectangle
    #It's made like this to easily access the colors of nearby triangles

satteliteList = []

timer = 0
videoTimer = 0
soonestNote = 0

# Load MIDI file into PrettyMIDI object
midi_data = pretty_midi.PrettyMIDI('Sounds/PinkPanther.midi')
# Print an empirical estimate of its global tempo
instrumentList = midi_data.instruments
notesList = []

notes=[] #satellites list

for x in instrumentList:
    print(x.program)
    notesList.append(x.notes)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            y = random.randint(0, height)
            
            if event.key == pygame.K_1:
                x = 0
                instru = Piano(x,y)

            elif event.key == pygame.K_q:
                x = width - 20
                instru = Trumpet(x,y)

            notes.append(instru)
            
            # if event.key == pygame.K_1:
            #     instru.change_color(1)
            # elif event.key == pygame.K_q:
            #     instru.change_color(2)    

    screen.fill((10,10,25))
    timer += 15
    videoTimer += 10

    for x in range(width):
        pygame.draw.line(screen,(0,0,0),(x,curveCalculation(x)),(x+1,curveCalculation(x+1)-10),1)

    for i in triangleList:
        for j in range(len(i)):
            pygame.draw.polygon(screen, i[j][0].color,(i[j][0].p1,i[j][0].p2,i[j][0].p3))
            pygame.draw.polygon(screen, i[j][1].color,(i[j][1].p1,i[j][1].p2,i[j][1].p3))
            if (timer > 60):
                i[j][1].changeColor(i[j][0])
                i[j][0].changeColor(i[j-1][1])

    for k in satteliteList:
        pygame.draw.polygon(screen,k.color,k.drawingCoordinates)
        k.move()

    if (int((notesList[0][0].start)*100) < int((notesList[1][0].start)*100)):
        soonestNote = 0
    else:
        soonestNote = 1

    #apparition of the sattelite (remove when the lifetime is 0)
    for n in notes[:]:
        n.update()
        if n.life_time <= 0:
            notes.remove(n)
        else:
            n.draw(screen)



    if (timer > 60):
        for x in triangleList:
            x[0][0].defineColor()
            x[0][1].defineColor()
        timer = 0


    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()