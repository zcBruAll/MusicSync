import pygame
import random
from Midi_Utils import *
from Generators import *
pygame.init()


#       Functions
def curveCalculation(x):
    return 1080 - ((x/3200)*(1920-x) + 100)
    # 1080 - the result so that it creates the curve at the bottom of the screen and not at the top


#       Config
width = 1500
height = 700

spacing = 24
scale = 20.0
cols = int(width/spacing)+1
rows = int((curveCalculation(960))/spacing)+1
running = True


triangleList = []
objects =[]

timer = 0
videoTimer = -(15*float(1/60))
soonestNote = 0


#       Classes
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
        if (random.random() < 0.1):
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



#       Initialization
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
pygame.mixer.music.load("Sounds/PinkPanther.midi")
pygame.mixer.music.play()

#Creating all the triangles before the loop makes for a way better performance
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


notesList = readMidi('Sounds/PinkPanther.midi')
pianoNotes = seperateInstrument(notesList, 0)
trumpetNotes = seperateInstrument(notesList, 1)

#Calculating the max pitch and min pitch
maxPitch = 0
minPitch = notesList[0][0].pitch
for k in notesList:
    for i in k:
        if(i.pitch > maxPitch):
            maxPitch = i.pitch
        elif (i.pitch < minPitch):
            minPitch = i.pitch


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            

    screen.fill((10,10,25))
    timer += 1
    videoTimer += float(1/60)

    for x in range(width):
        pygame.draw.line(screen,(0,0,0),(x,curveCalculation(x)),(x+1,curveCalculation(x+1)-10),1)

    for i in triangleList:
        for j in range(len(i)):
            pygame.draw.polygon(screen, i[j][0].color,(i[j][0].p1,i[j][0].p2,i[j][0].p3))
            pygame.draw.polygon(screen, i[j][1].color,(i[j][1].p1,i[j][1].p2,i[j][1].p3))
            if (timer > 60):
                i[j][1].changeColor(i[j][0])
                i[j][0].changeColor(i[j-1][1])


    if (float(notesList[0][0].start) < float(notesList[1][0].start)):
        soonestNote = 0
    else:
        soonestNote = 1

    #draw satellites and aliens
    for obj in objects[:]:
        obj.update()
        if obj.life_time <= 0:
            objects.remove(obj)
        else:
            obj.draw(screen)

    if (timer > 60):
        for x in triangleList:
            x[0][0].defineColor()
            x[0][1].defineColor()
        timer = 0

    if (videoTimer >= (float(notesList[soonestNote][0].start))):
        y = int((notesList[soonestNote][0].pitch-minPitch)*(int(width/(maxPitch-minPitch))))
        y = notesList[soonestNote][0].pitch
        if(y > height):
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