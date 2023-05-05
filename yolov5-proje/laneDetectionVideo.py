import cv2
import numpy as np
from matplotlib import pyplot as plt
import math
import PID
import time

oldrightLine = (1, 0)
oldleftLine = (-1, 0)
polygon_c = [(196, 720), (430, 585), (850, 585), (1084, 720)]  # Kamera boyutuna göre ayarlanmış çokgenin koordinatları

def ROI(image):

    polygons = np.array([polygon_c])

    # Sıfırlardan oluşan 'image' boyutunda bir dizi
    zeroMask = np.zeros_like(image)

    # Çokgen içerisinde kalan alanın değerlerini 1 ile değiştirir
    region_of_interest = cv2.fillPoly(zeroMask, polygons, 1)

    # And(&) işlemi ile sadece içi doldurulan alan alınır (0 & 1 : 0 [Bu durumlar görüntüden atılır])
    region_of_interest_image = cv2.bitwise_and(image, region_of_interest)

    return region_of_interest_image

def coordinateCalculation(frame, lines):

    slope, yIntercept = lines[0], lines[1]

    # Y1 Koordinat
    y1 = frame.shape[0]

    # Y2 Koordinat
    y2 = int(y1 - 110)

    # X1 Koordinat hesabı: y = mx+c
    x1 = int((y1 - yIntercept) / slope)

    # X2 Koordinat hesabı: y = mx+c
    x2 = int((y2 - yIntercept) / slope)

    return np.array([x1, y1, x2, y2])

def getLines(frame, lines):

    global oldrightLine, oldleftLine
    copyImage = frame.copy()
    leftLine, rightLine = [], []
    lineFrame = np.zeros_like(frame)
    for line in lines:
        x1, y1, x2, y2 = line[0]
        # slope(eğim) & y-intercept hesabı
        lineData = np.polyfit((x1, x2), (y1, y2), 1)
        slope, yIntercept = round(lineData[0], 4), lineData[1]
        if slope < 0:
            leftLine.append((slope, yIntercept))
        elif slope == 0:
            slope = 0.001
        else:
            rightLine.append((slope, yIntercept))

    if leftLine:
        #leftLineAverage = np.average(leftLine, axis=0) # Tespit edilen şeritlerin ortalaması alınarak denendi fakat çok fazla titreşim olduğu için kullanılmıyor
        leftLineAverage = enYakin(oldleftLine, leftLine)
        left = coordinateCalculation(frame, leftLineAverage)
        oldleftLine = leftLineAverage
        PID.solnokta = abs((left[2] + left[0]) / 2)  # berkay
        #print("                  sol nokta = " + str(PID.solnokta))
        try:
            cv2.line(lineFrame, (left[0], left[1]), (left[2], left[3]), (255, 0, 0), 2)
        except Exception as e:
            print('Error', e)
    if rightLine:
        #rightLineAverage = np.average(rightLine, axis=0)
        rightLineAverage = enYakin(oldrightLine, rightLine)
        right = coordinateCalculation(frame, rightLineAverage)
        oldrightLine = rightLineAverage
        PID.sagnokta = abs((right[2] + right[0]) / 2)  # berkay
        #print("                   sag nokta = " + str(PID.sagnokta))
        try:
            cv2.line(lineFrame, (right[0], right[1]), (right[2], right[3]), (255, 0, 0), 2)
        except Exception as e:
            print('Error:', e)

    return cv2.addWeighted(copyImage, 0.85, lineFrame, 0.85, 0.0)

def enYakin(select, datas):

    # İlk değere göre değişkenlere değer atanması
    enyakin = 0
    yakinlik = 10
    y = 0
    for i in datas:
        x = i[0] # “x”in girilmesi
        # Koşullar kontrol edilirken “yakinlik” ve “enyakin” değerlerin değiştirilmesi
        if abs(x - select[0]) < yakinlik:
            yakinlik = abs(x - select[0])
            enyakin = x
            y = i[1]

    return [enyakin, y]

def serit_takip(frame):

    # 1. Grayscale Dönüşümü
    grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 2. Görüntüdeki noiseları kaldırmak için GaussianBlur uygulanması
    kernel_size = 1
    gaussianFrame = cv2.GaussianBlur(grayFrame,(kernel_size,kernel_size),kernel_size)

    # 3. Canny edge detection
    low_threshold = 75
    high_threshold = 160
    edgeFrame = cv2.Canny(gaussianFrame, low_threshold, high_threshold)

    # 4. Belirli bir alanı maskeleme
    roiFrame = ROI(edgeFrame)

    # 5. Hough Algoritması ile çizgilerin tespiti
    lines = cv2.HoughLinesP(roiFrame, rho=1, theta=np.pi/180, threshold=20, lines = np.array([]), minLineLength=10, maxLineGap=180)

    PID.pid_control()  # Berkay PID

    # 5. Tespit edilen şeritlerin sınıflandırılması
    imageWithLines = getLines(frame, lines)

    imageWithLines = cv2.polylines(imageWithLines,
                                   [np.array([polygon_c]).reshape((-1, 1, 2))],
                                   True, (255, 0, 0), 2)

    cv2.imshow("serit", imageWithLines)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
