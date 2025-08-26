import pygame

class Satellite():
    def __init__(self, x, y, num_pannel = 2):
        self.x = x
        self.y = y
        self.life_time = 200
        self.color = (255, 0, 0)
        
        #body dimensions
        self.size = 50
        self.length = 50
        self.width = 20
        self.pannel_length = 50
        self.pannel_width = 80
        
        #changing parameters
        self.num_pannel = num_pannel
        self.body_color = (0,0,0)
        self.pannel_color = (0,0,0)

        self.body = [
            #main body
            [
                [x - self.size, y - self.size],
                [x, y],
                [x + self.size, y - self.size]
            ],
            [
                [x + self.size, y - self.size],
                [x, y],
                [x + self.size, y + self.size]
            ],
            [
                [x + self.size, y + self.size],
                [x, y],
                [x - self.size, y + self.size]
            ],
            [
                [x - self.size, y - self.size],
                [x, y],
                [x - self.size, y + self.size]
            ],
            #right wing
            [
                [x + self.size, y - self.width/2],
                [x + self.size + self.length, y - self.width/2],
                [x + self.size, y + self.width/2]
            ],
            [
                [x + self.size + self.length, y + self.width/2],
                [x + self.size + self.length, y - self.width/2],
                [x + self.size, y + self.width/2]
            ],
            #left wing
            [
                [x - self.size, y - self.width/2],
                [x - self.size - self.length, y - self.width/2],
                [x - self.size, y + self.width/2]
            ],
            [
                [x - self.size - self.length, y + self.width/2],
                [x - self.size - self.length, y - self.width/2],
                [x - self.size, y + self.width/2]
            ]
        ]
        
        self.pannels = []
        Satellite.add_pannel(self, num_pannel)
        """ self.pannels = [
            #right pannel
            [
                [x + self.size + self.length, y - self.pannel_width/2],                            #A
                [x + self.size + self.length + self.pannel_length, y - self.pannel_width/2],       #B
                [x + self.size + self.length, y + self.pannel_width/2]                             #D
            ],
            [
                [x + self.size + self.length + self.pannel_length, y - self.pannel_width/2],       #B
                [x + self.size + self.length + self.pannel_length, y + self.pannel_width/2],       #C
                [x + self.size + self.length, y + self.pannel_width/2]                             #D
            ],
            #left pannel
            [
                [x - self.size - self.length, y - self.pannel_width/2],
                [x - self.size - self.length - self.pannel_length, y - self.pannel_width/2],
                [x - self.size - self.length, y + self.pannel_width/2]
            ],
            [
                [x - self.size - self.length - self.pannel_length, y - self.pannel_width/2],
                [x - self.size - self.length - self.pannel_length, y + self.pannel_width/2],
                [x - self.size - self.length, y + self.pannel_width/2]
            ]
        ] """
        
    def update(self):
        self.life_time -= 1
        

    def add_pannel(self, num):
        for i in range(1, num + 1):
            #right pannels
            tri1 = [
                    [self.x + self.size + self.length + self.pannel_length*(i-1), self.y - self.pannel_width/2],                            
                    [self.x + self.size + self.length + self.pannel_length*i, self.y - self.pannel_width/2],       
                    [self.x + self.size + self.length + self.pannel_length*(i-1), self.y + self.pannel_width/2]                             
            ]
            tri2 = [
                    [self.x + self.size + self.length + self.pannel_length*i, self.y - self.pannel_width/2],       
                    [self.x + self.size + self.length + self.pannel_length*i, self.y + self.pannel_width/2],       
                    [self.x + self.size + self.length + self.pannel_length*(i-1), self.y + self.pannel_width/2]                             
            ]
            #left pannels
            tri3 = [
                    [self.x - self.size - self.length - self.pannel_length*(i-1), self.y - self.pannel_width/2],
                    [self.x - self.size - self.length - self.pannel_length*i, self.y - self.pannel_width/2],
                    [self.x - self.size - self.length - self.pannel_length*(i-1), self.y + self.pannel_width/2]
            ]
            tri4 = [
                    [self.x - self.size - self.length - self.pannel_length*i, self.y - self.pannel_width/2],
                    [self.x - self.size - self.length - self.pannel_length*i, self.y + self.pannel_width/2],
                    [self.x - self.size - self.length - self.pannel_length*(i-1), self.y + self.pannel_width/2]
            ]
            
            self.pannels.append(tri1)
            self.pannels.append(tri2)
            self.pannels.append(tri3)
            self.pannels.append(tri4)

        # return self.pannels
        
    def draw(self, surface):
        for tri in self.body:
            for coords in tri:
                coords[0] += 1
            pygame.draw.polygon(surface, self.color, tri)
            
        for tri in self.pannels:
            for coords in tri:
                coords[0] += 1
            pygame.draw.polygon(surface, (0, 0, 255), tri)
        
            
        
            
    """ 
    if the coords are truple [(x,y)] instead of a list [[x,y]]
    
    def draw(self, surface):
    for tri in self.all_triangles:
        new_tri = [(x + self.dx, y) for (x, y) in tri]
        pygame.draw.polygon(surface, self.color, new_tri)
    """
            