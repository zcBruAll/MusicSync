import pygame
import random
import Objects.Shapes


class Satellite():
    def __init__(self, x, y, lifetime, velocity, bodyType, body_width, body_height, body_color, pannel_width, pannel_height, num_wings, pannel_color):
        self.x = x
        self.y = y
        self.life_time = lifetime * 200
        
        self.body_color = body_color
        self.pannel_color = pannel_color
        
        # body dimensions
        self.size = body_width

        # little wings dimensions (unchanged)
        self.length = random.randint(20, 50)
        self.width = 20

        # creacting all lists of points
        self.body = Satellite.draw_body(self, x, y, bodyType, body_width, body_height)

        self.pannels = []
        Satellite.add_pannel(self, velocity, pannel_width, pannel_height, num_wings)

    def update(self):
        self.life_time -= 1

    def draw_body(self, x, y, isRectangle, width, height):
        all_points = []
        if (isRectangle == True):
            all_points = [
                [
                    [x - width, y - height],
                    [x, y],
                    [x + width, y - height]
                ],
                [
                    [x + width, y - height],
                    [x, y],
                    [x + width, y + height]
                ],
                [
                    [x + width, y + height],
                    [x, y],
                    [x - width, y + height]
                ],
                [
                    [x - width, y - height],
                    [x, y],
                    [x - width, y + height]
                ],
                # right wing
                [
                    [x + width, y - self.width/2],
                    [x + width + self.length, y - self.width/2],
                    [x + width, y + self.width/2]
                ],
                [
                    [x + width + self.length, y + self.width/2],
                    [x + width + self.length, y - self.width/2],
                    [x + width, y + self.width/2]
                ],
                # left wing
                [
                    [x - width, y - self.width/2],
                    [x - width - self.length, y - self.width/2],
                    [x - width, y + self.width/2]
                ],
                [
                    [x - width - self.length, y + self.width/2],
                    [x - width - self.length, y - self.width/2],
                    [x - width, y + self.width/2]
                ]
            ]
        else:
            all_points = Objects.Shapes.drawElipse(x, y, width, height, 10)
            tri1 = [
                [x + width - 10, y - self.width/2],
                [x + width + self.length, y - self.width/2],
                [x + width - 10, y + self.width/2]
            ]
            tri2 = [
                [x + width + self.length, y + self.width/2],
                [x + width + self.length, y - self.width/2],
                [x + width - 10, y + self.width/2]
            ]
            tri3 = [
                [x - width + 10, y - self.width/2],
                [x - width - self.length, y - self.width/2],
                [x - width + 10, y + self.width/2]
            ]
            tri4 = [
                [x - width - self.length, y + self.width/2],
                [x - width - self.length, y - self.width/2],
                [x - width + 10, y + self.width/2]
            ]
            all_points.append(tri1)
            all_points.append(tri2)
            all_points.append(tri3)
            all_points.append(tri4)

        return all_points

    def add_pannel(self, num, pannel_width, pannel_height, num_wings):
        if num_wings == 2:
            for i in range(1, num +1):
                # right pannels
                tri1 = [
                    [self.x + self.size + self.length + pannel_width * (i-1), self.y - pannel_height],
                    [self.x + self.size + self.length + pannel_width*i, self.y],
                    [self.x + self.size + self.length + pannel_width * (i-1), self.y]
                ]
                tri2 = [
                    [self.x + self.size + self.length + pannel_width*i, self.y - pannel_height],
                    [self.x + self.size + self.length + pannel_width*i, self.y],
                    [self.x + self.size + self.length + pannel_width *(i-1), self.y - pannel_height]
                ]
                tri3 = [
                    [self.x + self.size + self.length + pannel_width * (i-1), self.y + pannel_height],
                    [self.x + self.size + self.length + pannel_width*i, self.y],
                    [self.x + self.size + self.length + pannel_width * (i-1), self.y]
                ]
                tri4 = [
                    [self.x + self.size + self.length + pannel_width*i, self.y + pannel_height],
                    [self.x + self.size + self.length + pannel_width*i, self.y],
                    [self.x + self.size + self.length + pannel_width *(i-1), self.y + pannel_height]
                ]
                # left pannels
                tri5 = [
                    [self.x - self.size - self.length - pannel_width * (i-1), self.y - pannel_height],
                    [self.x - self.size - self.length - pannel_width*i, self.y],
                    [self.x - self.size - self.length - pannel_width * (i-1), self.y]
                ]
                tri6 = [
                    [self.x - self.size - self.length - pannel_width*i, self.y - pannel_height],
                    [self.x - self.size - self.length - pannel_width*i, self.y],
                    [self.x - self.size - self.length - pannel_width *(i-1), self.y - pannel_height]
                ]
                tri7 = [
                    [self.x - self.size - self.length - pannel_width * (i-1), self.y + pannel_height],
                    [self.x - self.size - self.length - pannel_width*i, self.y],
                    [self.x - self.size - self.length - pannel_width * (i-1), self.y]
                ]
                tri8 = [
                    [self.x - self.size - self.length - pannel_width*i, self.y + pannel_height],
                    [self.x - self.size - self.length - pannel_width*i, self.y],
                    [self.x - self.size - self.length - pannel_width *(i-1), self.y + pannel_height]
                ]
                self.pannels.append(tri1)
                self.pannels.append(tri2)
                self.pannels.append(tri3)
                self.pannels.append(tri4)
                self.pannels.append(tri5)
                self.pannels.append(tri6)
                self.pannels.append(tri7)
                self.pannels.append(tri8)
        
        else:
            for i in range(1, num +1):
                # right pannels
                tri1 = [
                    [self.x + self.size + self.length + pannel_width *(i-1), self.y - pannel_height/2],
                    [self.x + self.size + self.length + pannel_width*i, self.y - pannel_height/2],
                    [self.x + self.size + self.length + pannel_width *(i-1), self.y + pannel_height/2]
                ]
                tri2 = [
                    [self.x + self.size + self.length + pannel_width*i, self.y - pannel_height/2],
                    [self.x + self.size + self.length + pannel_width*i, self.y + pannel_height/2],
                    [self.x + self.size + self.length + pannel_width *(i-1), self.y + pannel_height/2]
                ]
                # left pannels
                tri3 = [
                    [self.x - self.size - self.length - pannel_width *(i-1), self.y - pannel_height/2],
                    [self.x - self.size - self.length - pannel_width*i, self.y - pannel_height/2],
                    [self.x - self.size - self.length - pannel_width *(i-1), self.y + pannel_height/2]
                ]
                tri4 = [
                    [self.x - self.size - self.length - pannel_width*i, self.y - pannel_height/2],
                    [self.x - self.size - self.length - pannel_width*i, self.y + pannel_height/2],
                    [self.x - self.size - self.length - pannel_width *(i-1), self.y + pannel_height/2]
                ]

                self.pannels.append(tri1)
                self.pannels.append(tri2)
                self.pannels.append(tri3)
                self.pannels.append(tri4)

    def draw(self, surface):
        for tri in self.body:
            for coords in tri:
                coords[0] += 3
                coords[1] += 1
            pygame.draw.polygon(surface, self.body_color, tri)


        for tri in self.pannels:
            for coords in tri:
                coords[0] += 3
                coords[1] += 1
            pygame.draw.polygon(surface, self.pannel_color, tri)
            pygame.draw.polygon(surface, (255,255,255), tri, 2)


    """ 
    if the coords are truple [(x,y)] instead of a list [[x,y]]
    
    def draw(self, surface):
    for tri in self.all_triangles:
        new_tri = [(x + self.dx, y) for (x, y) in tri]
        pygame.draw.polygon(surface, self.color, new_tri)
    """
