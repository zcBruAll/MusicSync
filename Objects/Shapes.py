import math

def drawSemiElispe_notCenter(cx, cy, rx, ry, segment):
    points = []
    triangles = []
    
    for i in range(segment + 1):
        angle = 2 * math.pi * i / (segment*2)
        x = cx + rx * math.cos(angle)
        y = cy + ry * math.sin(angle)
        points.append([x,y])
        
    for i in range(segment):    
        triangles.append([ points[i], [x,y], points[i+1]])
    
    return triangles

def drawSemiElipse(cx, cy, rx, ry, segment, orientation = 1):
    angle_step = 180 / segment
    triangles = []
    
    #draw a top semi elipse
    if orientation == 0:
        angle_step = -angle_step

    for i in range(segment):
        angle1 = math.radians(i * (angle_step))
        angle2 = math.radians((i + 1) * (angle_step))
        
        point1 = [cx + rx * math.cos(angle1), cy + ry * math.sin(angle1)]
        point2 = [cx + rx * math.cos(angle2), cy + ry * math.sin(angle2)]
        
        triangles.append([[cx,cy], point1, point2])
         
    return triangles    

def drawSemiCercle_notCenter(cx, cy, r, segment):
    points = []
    triangles = []
    
    for i in range(segment + 1):
        angle = 2 * math.pi * i / (segment*2)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)

        points.append([x,y])
        
    for i in range(segment):    
        triangles.append([ points[i], [x,y], points[i+1]])
    
    return triangles

def drawSemiCercle(cx, cy, radius, segment, orientation = 1):
    angle_step = 180 / segment
    triangles = []
    
    #draw a top semi cercle
    if orientation == 0:
        angle_step = -angle_step
        
    for i in range(segment):
        angle1 = math.radians(i * (angle_step))
        angle2 = math.radians((i + 1) * (angle_step))
        
        point1 = [cx + radius * math.cos(angle1), cy + radius * math.sin(angle1)]
        point2 = [cx + radius * math.cos(angle2), cy + radius * math.sin(angle2)]
        
        triangles.append([[cx,cy], point1, point2])
        
    return triangles