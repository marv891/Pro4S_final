import sys
import math
import cv2 as cv
import numpy as np
from collections import defaultdict
import os

def main(X_coordinateMouse, Y_coordinateMouse, measuringArrayImage, laserImage, X_Laser, Y_Laser, nameImage):  
   
    # Loads an image
    new = cv.imread(cv.samples.findFile(measuringArrayImage))
    laserImage = cv.imread(laserImage)
    
    # Definiere die Größe des ROIs
    roi_size = 450
    
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
    if y_end > new.shape[0]:
        y_end = new.shape[0]
        y = y_end - roi_size
    # Überprüfe, ob das ROI rechts vom Bild liegt
    if x_end > new.shape[1]:
        x_end = new.shape[1]
        x = x_end - roi_size
    
    # Schneide das ROI aus dem ursprünglichen Bild aus
    imageCropped = new[y:y_end, x:x_end]
    
    # Vergrößere das Bild auf die gewünschte Größe von 450x450 Pixeln
    # imageResized = cv.resize(imageCropped, (roi_size, roi_size))
    
    src = imageCropped    
        
    b, g, r = cv.split(src)
    
    green_grayscale = cv.cvtColor(g, cv.COLOR_GRAY2BGR)
        
    dst = cv.Canny(green_grayscale, 50, 80, None, 3)
    
    cv.imshow("Frame", dst)
    
    # Copy edges to the images that will display the results in BGR
    cdst = cv.cvtColor(dst, cv.COLOR_GRAY2BGR)
    
    lines = cv.HoughLines(dst, 1, np.pi / 180, 120, 10, 0, 0)
    s = []
   

    intersections = []  # List to store intersection points
        
    if lines is not None:
        for i in range(0, len(lines)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 2000*(-b)), int(y0 + 2000*(a)))
            pt2 = (int(x0 - 2000*(-b)), int(y0 - 2000*(a)))
        

            cv.line(cdst, pt1, pt2, (0,0,255), 1, cv.LINE_AA)
            cv.line(src, pt1, pt2, (0,0,255), 1, cv.LINE_AA)
            s.append(pt1[0])
 
    cv.imshow("Frame1", src)

 
    def intersection(line1, line2):
        rho1, theta1 = line1[0]
        rho2, theta2 = line2[0]
        A = np.array([
            [np.cos(theta1), np.sin(theta1)],
            [np.cos(theta2), np.sin(theta2)]
        ])
        b = np.array([[rho1], [rho2]])
        x0, y0 = np.linalg.solve(A, b)
        x0, y0 = int(np.round(x0)), int(np.round(y0))
        return int(x0), int(y0)


    def segmented_intersections(lines):
        intersections = []
        for i, group in enumerate(lines[:-1]):
            for next_group in lines[i+1:]:
                for line1 in group:
                    for line2 in next_group:
                        intersections.append(intersection(line1, line2)) 


        return intersections
    
    def segment_by_angle_kmeans(lines, k=2, **kwargs):

        # Define criteria = (type, max_iter, epsilon)
        default_criteria_type = cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER
        criteria = kwargs.get('criteria', (default_criteria_type, 10, 1.0))
        flags = kwargs.get('flags', cv.KMEANS_RANDOM_CENTERS)
        attempts = kwargs.get('attempts', 10)
    
        # returns angles in [0, pi] in radians
        angles = np.array([line[0][1] for line in lines])
        # multiply the angles by two and find coordinates of that angle
        pts = np.array([[np.cos(2*angle), np.sin(2*angle)]
                        for angle in angles], dtype=np.float32)
    
        # run kmeans on the coords
        labels, centers = cv.kmeans(pts, k, None, criteria, attempts, flags)[1:]
        labels = labels.reshape(-1)  # transpose to row vec
    
        # segment lines based on their kmeans label
        segmented = defaultdict(list)
        for i, line in enumerate(lines):
            segmented[labels[i]].append(line)
        segmented = list(segmented.values())
        return segmented
    
    segmented = segment_by_angle_kmeans(lines)
    intersections = segmented_intersections(segmented)
    
    
    def remove_close_points(points, threshold):
       result = []
       n = len(points)
    
       # Iteriere über die Punkte
       for i in range(n):
           point = points[i]
           close_points = [point]  # Liste für nah beieinander liegende Punkte

           x_sum = point[0]
           y_sum = point[1]
    
           # Vergleiche den aktuellen Punkt mit allen anderen Punkten
           for j in range(n):
               if i != j:
                   other_point = points[j]
                   # Berechne den Abstand zwischen den Punkten
                   distance = math.sqrt((point[0] - other_point[0]) ** 2 + (point[1] - other_point[1]) ** 2)
    
                   # Füge den Punkt zur Liste der nah beieinander liegenden Punkte hinzu
                   if distance <= threshold:
                       close_points.append(other_point)
                       x_sum += other_point[0]
                       y_sum += other_point[1]
        
           # Berechne den Mittelpunkt der nah beieinander liegenden Punkte
           if len(close_points) > 1:
               x, y = int(x_sum / len(close_points)), int(y_sum / len(close_points))
               result.append([[x,y]])
           else:
               x, y = point
               result.append([[x,y]])
                               
       return result

    def remove_duplicate_coordinates(data):
        unique_coordinates = []
        seen_coordinates = set()
    
        for coord_list in data:
            for coord in coord_list:
                coord_tuple = tuple(coord)
                if coord_tuple not in seen_coordinates:
                    unique_coordinates.append(coord)
                    seen_coordinates.add(coord_tuple)
        return unique_coordinates


    def create_coordinate_matrix(coordinates):
        sorted_coordinates = sorted(coordinates, key=lambda coord: (coord[1] // 100, coord[0] // 100))
        matrix = [sorted_coordinates[i:i+3] for i in range(0, 9, 3)]
              
        print(matrix)
    
        return matrix
    
    intersections = remove_close_points(intersections, 10)    
    intersections = remove_duplicate_coordinates(intersections)
    
    def add_values_to_coordinates(coordinates, x_value, y_value):
        new_coordinates = []
        for point in coordinates:
            new_point = [point[0] + x_value, point[1] + y_value]
            new_coordinates.append(new_point)
        return new_coordinates
    
    
    intersections = add_values_to_coordinates(intersections, x, y)
    
    for point in intersections:
        pt = (point[0], point[1])
        length = 10
        cv.line(new, (pt[0], pt[1]-length), (pt[0], pt[1]+length), (255, 0, 255), 1)  # vertikale Linie
        cv.line(new, (pt[0]-length, pt[1]), (pt[0]+length, pt[1]), (255, 0, 255), 1)  # horizontale Linie
    
    
    intersections = create_coordinate_matrix(intersections)
    

    
    def order_points(pts):
        # initialzie a list of coordinates that will be ordered
        # such that the first entry in the list is the top-left,
        # the second entry is the top-right, the third is the
        # bottom-right, and the fourth is the bottom-left
        rect = np.zeros((4, 2), dtype="float32")
        # the top-left point will have the smallest sum, whereas
        # the bottom-right point will have the largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        # now, compute the difference between the points, the
        # top-right point will have the smallest difference,
        # whereas the bottom-left will have the largest difference
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        # return the ordered coordinates
        return rect
    
    
    def four_point_transform(image, pts):
        # obtain a consistent order of the points and unpack them
        # individually
        pts = np.array(pts, dtype=np.float32)
        rect = order_points(pts)
        (tl, tr, br, bl) = rect
    
        # get min value
        minY = min(tl[1], tr[1], br[1], bl[1])
        minX = min(tl[0], tr[0], br[0], bl[0])
    
        # shift whole rectangel to max left up
        shiftLeftUp = (minX, minY)
        tl = tl - shiftLeftUp
        tr = tr - shiftLeftUp
        br = br - shiftLeftUp
        bl = bl - shiftLeftUp
    
        # compute the width of the new image, which will be the
        # maximum distance between bottom-right and bottom-left
        # x-coordiates or the top-right and top-left x-coordinates
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        # compute the height of the new image, which will be the
        # maximum distance between the top-right and bottom-right
        # y-coordinates or the top-left and bottom-left y-coordinates
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
    
        # Skalierungsfaktor berechnen
        # x-Richtung
        factorX = image.shape[1] / maxWidth
    
        # y-Richtung
        factorY = image.shape[0] / maxHeight
    
        factor = factorX  # min(factorX, factorY)
    
        tl = tl * factor
        tr = tr * factor
        br = br * factor
        bl = bl * factor
    
        rectNew = (tl, tr, br, bl)
    
        rectNew = np.array(rectNew, dtype=np.float32)
    
        # compute the width of the new image, which will be the
        # maximum distance between bottom-right and bottom-left
        # x-coordiates or the top-right and top-left x-coordinates
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        # compute the height of the new image, which will be the
        # maximum distance between the top-right and bottom-right
        
        # y-coordinates or the top-left and bottom-left y-coordinates
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
    
        # now that we have the dimensions of the new image, construct
        # the set of destination points to obtain a "birds eye view",
        # (i.e. top-down view) of the image, again specifying points
        # in the top-left, top-right, bottom-right, and bottom-left
        # order
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype="float32")
    
        # compute the perspective transform matrix and then apply it
        M = cv.getPerspectiveTransform(rectNew, dst)
        warped = cv.warpPerspective(image, M, (maxWidth, maxHeight))
    
        # return the warped image
        return warped, M
    
    def calculate_distance(mid, x_Laser, y_Laser, ref1, ref2):
        x_distance = abs(mid[0] - x_Laser)
        y_distance = abs(mid[1] - y_Laser)
    
        distance_in_pixels = (x_distance, y_distance)
        
        # Angenommener Wert für die Umrechnungsfaktoren von Pixeln zu Millimetern für die Baumer VCXG-24C
        pixel_to_mm = 100/(abs(ref1[0] - ref2[0]))
        
        distance_in_mm = (x_distance * pixel_to_mm, y_distance * pixel_to_mm)
    
        return distance_in_pixels, distance_in_mm

    def apply_perspective_transformation(M, points):
        transformed_points = []
        for row in points:
            transformed_row = []
            for point in row:
                # Convert point to homogeneous coordinates
                homogeneous_point = np.array(point + [1])  # Add 1 as the last element for each point
    
                # Apply the perspective transformation
                transformed_point = np.dot(M, homogeneous_point)
    
                # Convert back to Cartesian coordinates
                cartesian_point = transformed_point[:2] / transformed_point[2]
                transformed_row.append(cartesian_point.tolist())
            transformed_points.append(transformed_row)
    
        return transformed_points
    
    corners = [intersections[0][0], intersections[0][2], intersections[2][0], intersections[2][2]]
    warped, M = four_point_transform(new, corners)
    transformed_points = apply_perspective_transformation(M, intersections)
    
    distance = calculate_distance(transformed_points[1][1], X_Laser, Y_Laser, transformed_points[0][0], transformed_points[0][2] )
    print(distance)
    
    # cv.imshow("Frame", src)
    # cv.waitKey()
    # cv.destroyAllWindows()
    
    mittelpunktUT = int(intersections[1][1][0]), int(intersections[1][1][1])
    laserUT = int(X_Laser), int(Y_Laser)
    lasermittelpunktUT = (int(laserUT[0]), int(mittelpunktUT[1]))
      
    cv.line(laserImage, laserUT, lasermittelpunktUT, (255, 0, 0),2)
    cv.line(laserImage, mittelpunktUT, lasermittelpunktUT, (255, 0, 0),2)

    # Distanz auf Bild anzeigen
    cv.putText(laserImage, 'U ~= {}mm'.format(round(distance[1][0], 2)), lasermittelpunktUT, cv.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
    cv.putText(laserImage, 'T ~= {}mm'.format(round(distance[1][1], 2)), laserUT, cv.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)    
    
    # Creating path of relative path to folder data
    absolutepath = os.path.abspath(__file__)  
    # Path of filedirectory
    fileDirectory = os.path.dirname(absolutepath)
    # Navigate to data directory
    newPath = os.path.join(fileDirectory, 'Snapshots')
    
    nameImage = nameImage + '.png'
    
    os.chdir(newPath)
    
    cv.imwrite(nameImage, laserImage)
    # cv.imshow("Frame", laserImage)
    
    os.chdir(fileDirectory)    
    
    return distance
    
# if __name__ == "__main__":
#     main(sys.argv[1:])