import sys
import math
import cv2 as cv
import numpy as np

def mainLaserCrossDetection(laserImage, X_coordinateMouse, Y_coordinateMouse):
       
    filename = laserImage

    # Loads an image
    src = cv.imread(cv.samples.findFile(filename))
    
    # Definiere die Größe des ROIs
    roi_size = 600
    
    # Berechne die obere linke Ecke des ROIs
    x = X_coordinateMouse - roi_size // 2
    y = Y_coordinateMouse - roi_size // 2
    
    # Überprüfe, ob das ROI oberhalb des Bildes liegt
    if y < 0:
        y = 0
    # Überprüfe, ob das ROI links vom Bild liegt
    if x < 0:
        x = 0
    
    # Berechne die untere rechte Ecke des ROIs
    x_end = x + roi_size
    y_end = y + roi_size
    
    # Überprüfe, ob das ROI unterhalb des Bildes liegt
    if y_end > src.shape[0]:
        y_end = src.shape[0]
        y = y_end - roi_size
    # Überprüfe, ob das ROI rechts vom Bild liegt
    if x_end > src.shape[1]:
        x_end = src.shape[1]
        x = x_end - roi_size
    
    # Schneide das ROI aus dem ursprünglichen Bild aus
    imageCropped = src[y:y_end, x:x_end]
    
    # Vergrößere das Bild auf die gewünschte Größe von 600x600 Pixeln
    # imageResized = cv.resize(imageCropped, (roi_size, roi_size))
    
    src = imageCropped   
    
    hsv = cv.cvtColor(src, cv.COLOR_BGR2HSV)
    value = hsv[:,:,2]
    
    img_filtered = cv.GaussianBlur(value, (0, 0), 1.2)
    
    
    dst = cv.Canny(img_filtered, 60, 100, None, 3)
    
    # Copy edges to the images that will display the results in BGR
    cdst = cv.cvtColor(dst, cv.COLOR_GRAY2BGR)
    
    lines = cv.HoughLines(dst, 1, np.pi / 1, 80, 50, 0, 0)
    s = []
    
    if lines is not None:
        for i in range(0, len(lines)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
            pt2 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))

            cv.line(cdst, pt1, pt2, (0,0,255), 1, cv.LINE_AA)
            cv.line(src, pt1, pt2, (0,0,255), 1, cv.LINE_AA)
            s.append(pt1[0])
    
    # Initialisierung des maximalen Rotwertes und der zugehörigen y-Koordinate
    max_red_value_1 = 0
    max_y_1 = 0
    max_red_value_2 = 0
    max_y_2 = 0

    # Schleife für die Durchiteration der y-Koordinate
    for i in range(value.shape[0]):
        # Rotwert des aktuellen Pixels
        intensity = value[i, pt1[0]+50]
        # Überprüfung, ob der Rotwert größer als der aktuelle maximale Rotwert ist
        if intensity > max_red_value_1:
            # Aktualisierung des maximalen Rotwertes und der zugehörigen y-Koordinate
            max_red_value_1 = intensity
            max_y_1 = i
        if i == 800:
            break;
    
    # Ausgabe des maximalen Rotwertes und der zugehörigen y-Koordinate
    print('Maximaler Rotwert:', max_red_value_1)
    print('Y-Koordinate:', max_y_1)
       
    for i in range(value.shape[0]):
        # Rotwert des aktuellen Pixels
        intensity = value[i, pt1[0]-50]
        # Überprüfung, ob der Rotwert größer als der aktuelle maximale Rotwert ist
        if intensity > max_red_value_2:
            # Aktualisierung des maximalen Rotwertes und der zugehörigen y-Koordinate
            max_red_value_2 = intensity
            max_y_2 = i
        if i == 800:
            break;
            
    print('Maximaler Rotwert:', max_red_value_2)
    print('Y-Koordinate:', max_y_2)
        
    pt1_hor = (pt1[0] + 50, max_y_1)
    pt2_hor= (pt1[0] - 50, max_y_2)
    
    def extend_line(p1, p2, distance=10000):
        diff = np.arctan2(p1[1] - p2[1], p1[0] - p2[0])
        p3_x = int(p1[0] + distance*np.cos(diff))
        p3_y = int(p1[1] + distance*np.sin(diff))
        p4_x = int(p1[0] - distance*np.cos(diff))
        p4_y = int(p1[1] - distance*np.sin(diff))
        return ((p3_x, p3_y), (p4_x, p4_y))
    
    p3, p4 = extend_line(pt1_hor, pt2_hor)
    a = cv.line(src, p3, p4, (0,255,0), 1, cv.LINE_AA)
        
    pt1_middle = (int((s[0] + s[1])/2), 0)
    pt2_middle = (int((s[0] + s[1])/2), 1000)
    b = cv.line(src, pt1_middle, pt2_middle, (0,255,0), 1, cv.LINE_AA)
    

    def calculate_intersection(line1, line2):
        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2
    
        # Berechnung der Determinante
        det = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
        if det != 0:
            # Berechnung der x- und y-Koordinaten des Schnittpunkts
            x = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / det
            y = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / det
            return x, y
        else:
            # Linien sind parallel, es gibt keinen Schnittpunkt
            return None
    
    def add_values_to_coordinates(coordinates, x, y):
        x_old, y_old = coordinates
        x_new = x_old + x
        y_new = y_old + y
        return x_new, y_new
    
    p5, p6 = p3
    p7, p8 = p4
    line1 = (int((s[0] + s[1])/2), 0, int((s[0] + s[1])/2), 1000)
    line2 = (p5, p6, p7, p8)
    
    x_intersection, y_intersection = calculate_intersection(line1, line2)
    center_coordinates = (int(x_intersection), int(y_intersection))
    x, y = add_values_to_coordinates(center_coordinates, x, y)
    print(x, y)
    
    cv.circle(src, center_coordinates, 5, (255,0,0), 5)
    
    cv.imshow("Source", src)
    cv.imshow("Gauss", img_filtered)
    cv.imshow("Detected Lines (in red) - Standard Hough Line Transform", cdst)
    
    # cv.waitKey()
    return x, y
    
# if __name__ == "__main__":
#     main(sys.argv[1:])