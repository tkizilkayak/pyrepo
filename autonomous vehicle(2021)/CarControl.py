import time
import math
import serial
#import pyautogui
#import Object_detection_webcam as odw

signCarrier = [False,False,False,False,False,False,False,False,False,False,False,False]
dizi2 = ['girisyok','sag','sol','sagadonulmez','soladonulmez','ilerisag','ilerisol','kirmizi','dur','durak','park','parkyasak']
text = 'tabela yok'

carState = 'stopped'
old_carState = 'moving'
turnControl = 0
parkx = 640     #park tabelasının kameraya göre x konumu
ortax = 640     #kameranın x eksenine göre ortadaki pixel konumu
parkpay = 50   #parka yönlenirken sürekli dönüş yapmaması için gereken pay
Turning = False

leftdistance = 0.0
rightdistance = 0.0
middistance = 0.0
upleftdistance = 0.0
uprightdistance = 0.0
backlidardistance = 0.0
kavsak_backlidardistance = 0.0 # problemsiz kavşak için

#çapraz için lidar kaydı:
old_rightdistance = 0.0
old_backlidardistance = 0.0

ts = 0
tsd = 0
capraz_ts = 0
kavsak_ts = 0

serialcomm = serial.Serial('COM7', 9600, timeout=0.05) #AKS

message = ''
message2 = ''

midstop = 1500.0
aciklik = 8000.0
turnstop = 500.0

parkcontrol = False
leftsave = False
capraz_save = False
problemsiz_kavsak = False


def bef(sign, befx):
    global signCarrier
    global parkx

    if sign == 'girisyok':
        signCarrier[0] = True
    elif sign == 'sag':
        signCarrier[1] = True
    elif sign == 'sol':
        signCarrier[2] = True
    elif sign == 'sagadonulmez':
        signCarrier[3] = True
    elif sign == 'soladonulmez':
        signCarrier[4] = True
    elif sign == 'ilerisag':
        signCarrier[5] = True
    elif sign == 'ilerisol':
        signCarrier[6] = True
    elif sign == 'kirmizi':
        signCarrier[7] = True
    elif sign == 'dur':
        signCarrier[8] = True
    elif sign == 'durak':
        signCarrier[9] = True
    elif sign == 'park':
        signCarrier[10] = True
    elif sign == 'parkyasak':
        signCarrier[11] = True

    parkx = befx


def cont():
    global leftdistance
    global rightdistance
    global middistance
    global old_rightdistance
    global old_backlidardistance
    global upleftdistance
    global uprightdistance
    global backlidardistance
    global kavsak_backlidardistance

    outfile = open('lidar_distances.txt', 'r')
    liste = outfile.readline()
    if liste != "":
        liste = liste.replace(",", ".")
        a, b, c, d, e, f = liste.split("_")
        leftdistance = float(a)
        rightdistance = float(b)
        middistance = float(c)
        upleftdistance = float(d)
        uprightdistance = float(e)
        backlidardistance = float(f)

        #simden gelen lidar verileri 1000 kat az oldugundan 1000 ile çarpıyoruz: (unity = metre)(lidar = minimetre)
        '''
        leftdistance *= 1000.0
        rightdistance *= 1000.0
        middistance *= 1000.0
        upleftdistance *= 1000.0
        uprightdistance *= 1000.0
        backlidardistance *= 1000.0
        '''
        backlidardistance += 700.0  #  aracın lidar ile arkadaki lidarın konumu arasındaki farkı sıfırlamak için daha dışarda olan arka lidara 700 eklenir
        print(leftdistance, rightdistance, middistance, upleftdistance, uprightdistance, backlidardistance)

    if Turning == False:
        old_rightdistance = uprightdistance
        old_backlidardistance = backlidardistance
        if problemsiz_kavsak:
            kavsak_backlidardistance = backlidardistance # old_backlidardistance bunun yerine aynı işi yapabilir gibi. bunu canın isterse kontrol et


def AutonomousDrive():
    global carState
    global text
    global signCarrier
    global Turning
    global message
    global message2
    global old_carState
    
    if (carState == 'stopped' and middistance < midstop and middistance != 0.0) or (carState == 'stopped' and old_carState == 'parking') or signCarrier[7] == True:
        carState = 'stopped'
    else:
        carState = old_carState
    
    cont()
    if carState != 'stopped': # stopped case'i tabelalar yüzünden değişmesin diye var bu if
        checkParking()
        turnCheck()
        checkForPassenger()
        if parkcontrol == True: #and Turning == False: # bu if parking case'ine bir kere girince sürekli orda kalması için
            carState = 'parking'
            old_carState = 'parking'
    checkLight()
    stopTable()

    print('case: '+ carState, str(Turning))    #
    if carState == 'moving':
        old_carState = 'moving'
        ## Burada harekete geç
        message = 'w'
        lidarControl()
        
    elif carState == 'turn':
        message = 'w' #tabela varken direkt turn'e girip movingten w komutunu almayabiliyor. bu yüzden burada da var w
        signCarrierControl() #dönüşü bitirme fonku
        turnControlController() #açıklık tespit etme fonku
        if turnControl == 0:
            lidarControl()
        
        if signCarrier[1] == True and (turnControl == 1 or turnControl == 3):
            turnright()
            Turning = True
        elif signCarrier[2] == True and (turnControl == 2 or turnControl == 3):
            turnleft()
            Turning = True
        elif signCarrier[3] == True or signCarrier[4] == True:
            if (middistance > 16500.0 or middistance == 0.0) and (turnControl == 1 or turnControl == 2 or turnControl == 3): # burdaki 16500.0 kavşakta karşıdaki duvarın uzaklığı (ne kadar kısa olursa o kadar geç dönüş yapar)
                forward()
                Turning = True
            elif (turnControl == 1 or turnControl == 3) and signCarrier[3] == False:
                turnright()
                Turning = True
            elif (turnControl == 2 or turnControl == 3) and signCarrier[4] == False:
                turnleft()
                Turning = True
        elif (signCarrier[5] == True or signCarrier[6] == True) and (turnControl == 1 or turnControl == 2 or turnControl == 3):
            forward()
            Turning = True
        elif signCarrier[0] == True:
            if turnControl == 1 or turnControl == 3:
                turnright()
                Turning = True
            elif turnControl == 2:
                turnleft()
                Turning = True
        print(turnControl)     #
    elif carState == 'getPassenger':
        print('yolcu almak icin araci durdur')
        message = 's'
        serialcomm.write(message.encode()) #time sleep oldugundan zaten aşağıda yapıyo diyemezsin
        time.sleep(0.1)
        print(message.encode())
        #pyautogui.press(message) #time sleep oldugundan zaten aşağıda yapıyo diyemezsin
        time.sleep(35)
        carState = 'moving'
        old_carState = 'moving'
    
    elif carState == 'parking':
        message = 'w'
        if ortax - parkx < -parkpay:
            print('saga don')
            message2 = 'n'
        elif ortax - parkx > parkpay:
            print('sola don')
            message2 = 'b'
        elif ortax - parkx < parkpay and ortax - parkx > -parkpay:
            print('direksiyonu duzle')
            message2 = 'o'

        if middistance <= 3000.0 and middistance != 0.0:
            carState = 'stopped'

    
    elif carState == 'stopped':
        print('arabayi durdur')
        message = 's'
    
    for i in range(0,12):
        if signCarrier[i] == True:
            if text != 'tabela yok':
                text = text + dizi2[i] + '\t'
            else:
                text = dizi2[i] + '\t'
    print(text)
    text = 'tabela yok'
    
    
    for i in range(7,12):
        signCarrier[i] = False

    
    if message !='':

        time.sleep(0.30)
        while serialcomm.write((message).encode()) < 1:
            print('message tekrar')

            pass 
        serialcomm.reset_output_buffer()
        print(message.encode())

        #pyautogui.press(message)
        message=''

                                # burada iki mesaj arasına bir süre konulması gerekebilir(biri gelip biri gelmiyorsa)

    if message2 !='':

        time.sleep(0.30)
        while serialcomm.write((message2).encode()) < 1:
            print('message2 tekrar')

            pass
        serialcomm.reset_output_buffer()
        print(message2.encode())

        #pyautogui.press(message2)
        message2=''

    #print(serialcomm.readline().decode('ascii'))
    
    
    
def lidarControl():
    global carState
    global message2
    global leftsave
    global problemsiz_kavsak

    print(old_backlidardistance - old_rightdistance) #

    if (rightdistance > aciklik or rightdistance == 0.0) and carState != 'turn' and leftsave == False:
        turnright()
    elif (leftdistance > aciklik or leftdistance == 0.0) and carState != 'turn':
        turnleft()
        leftsave = True
    else: # burda ilk önde engel var mı ona bakıp sonra çapraz sistemi ile yolda düzgün tutar. Ancak sola veya sağa çok yaklaşırsa araç çapraz olmasa bile eski sistem el ense yapıp aracı kenardan uzaklaştırır
        leftsave = False
        if middistance < midstop and middistance != 0.0:
            carState = 'stopped'
        if problemsiz_kavsak and kavsak_ts + 4 >= time.time():
            print('kavis bypass ediliyor')
            message2 = 'o'
        else:
            problemsiz_kavsak = False
            if (old_backlidardistance - old_rightdistance) > 80.0 and old_backlidardistance != 0.0:
                print('sola gel')
                message2 = 'b'
            elif (old_backlidardistance - old_rightdistance) < -80.0 and old_backlidardistance != 0.0:
                print('saga gel')
                message2 = 'n'
            elif (old_backlidardistance - old_rightdistance) > 160.0 and old_backlidardistance != 0.0:
                print('sola gel2')
                message2 = 'g'
            elif (old_backlidardistance - old_rightdistance) < -160.0 and old_backlidardistance != 0.0:
                print('saga gel2')
                message2 = 'h'
            elif upleftdistance > uprightdistance + 2000.0:
                print('kurtarici sola')
                message2 = 'g'
            elif uprightdistance > upleftdistance + 2000.0:
                print('kurtarici saga')
                message2 = 'h'
            else:
                print('direksiyonu duzle')
                message2 = 'o'

def signCarrierControl(): # dönüşün bitirilmeye karar verildiği fonksiyon
    global carState
    global old_carState
    global Turning
    global turnControl
    global signCarrier
    global kavsak_ts
    if math.fabs(uprightdistance - upleftdistance) <= 1400.0 and uprightdistance != 0.0 and upleftdistance != 0.0 and Turning == True and leftdistance != 0.0 and rightdistance != 0.0 and leftdistance < aciklik and rightdistance < aciklik:
        turnControl = 0
        carState = 'moving'
        old_carState = 'moving'
        Turning = False
        kavsak_ts = time.time() # problemsiz kavsak için sayaç burada sıfırlanır ve işlemin süresi başlar
        for i in range(0,7):
            signCarrier[i] = False
     

def turnControlController():
    global turnControl
    if Turning == False or (signCarrier[3] == True and turnControl == 1 and signCarrier[4] == False) or (signCarrier[4] == True and turnControl == 2 and signCarrier[3] == False):
        if (rightdistance > aciklik and leftdistance > aciklik) or (rightdistance == 0.0 and leftdistance == 0.0) or (rightdistance == 0.0 and leftdistance > aciklik) or (leftdistance == 0.0 and rightdistance > aciklik):
            turnControl = 3
        elif rightdistance >= leftdistance + aciklik or rightdistance == 0.0:
            turnControl = 1
        elif leftdistance >= rightdistance + aciklik or leftdistance == 0.0:
            turnControl = 2


def checkLight():
    global carState
    if signCarrier[7] == True:
        carState = 'stopped'
        print('checklight')



def turnCheck():
    global carState
    global old_carState
    if signCarrier[0] == True or signCarrier[1] == True or signCarrier[2] == True or signCarrier[3] == True or signCarrier[4] == True or signCarrier[5] == True or signCarrier[6] == True:
        carState = 'turn'
        old_carState = 'turn'


def checkForPassenger():
    global carState
    global old_carState
    global ts
    if signCarrier[9] == True and (ts + 100) <= time.time():
        carState = 'getPassenger'
        old_carState = 'getPassenger'
        print('getPassenger')
        ts = time.time()


def checkParking():
    global carState
    global old_carState
    global parkcontrol
    if signCarrier[10] == True and signCarrier[11] == True:# and Turning == False:
        carState = 'parking'
        old_carState = 'parking'
        parkcontrol = True
        
def stopTable():
    global tsd
    global message
    if signCarrier[8] == True and (tsd + 20) <= time.time():
        print('dur tabelasi, arabayi durdur')
        message = 's'

        serialcomm.write(message.encode())
        time.sleep(0.1)
        print(message.encode())

        #pyautogui.press(message)
        
        time.sleep(4)
        tsd = time.time()

def forward(): #14.02.2021
    global message2
    global capraz_save
    global capraz_ts
    global problemsiz_kavsak

    print("çapright:" + str(old_rightdistance) + "  çapright:" + str(old_backlidardistance) + "     çapfark: " + str(old_backlidardistance - old_rightdistance))
    if old_backlidardistance - old_rightdistance > 300.0: #buradaki 300 çapraz olduğunu anlama payı

        if middistance != 0.0 and middistance < 7500.0:
            print('sola don2')
            message2 = 'g'
            capraz_save = True
            capraz_ts = time.time()
        elif capraz_save == True:
            print('Tdireksiyonu duzle')
            message2 = 'o'
            if capraz_ts + 2 <= time.time() and capraz_ts + 4 > time.time():
                print('saga don')
                message2 = 'n'
            elif capraz_ts + 4 <= time.time():
                capraz_save = False
        else:
            print('Tdireksiyonu duzle')
            message2 = 'o'


    elif old_rightdistance - old_backlidardistance > 300.0: #buradaki 300 çapraz olduğunu anlama payı

        if middistance != 0.0 and middistance < 7500.0:
            print('saga don2')
            message2 = 'h'
            capraz_save = True
            capraz_ts = time.time()
        elif capraz_save == True:
            print('Tdireksiyonu duzle')
            message2 = 'o'
            if capraz_ts + 2 <= time.time() and capraz_ts + 4 > time.time():
                print('sola don')
                message2 = 'b'
            elif capraz_ts + 4 <= time.time():
                capraz_save = False
        else:
            print('Tdireksiyonu duzle')
            message2 = 'o'
    else:
        print("bypass aktive edildi")
        problemsiz_kavsak = True
        print('Tdireksiyonu duzle')
        message2 = 'o'

def turnright():
    global message2
    global carState
    global problemsiz_kavsak

    problemsiz_kavsak = False # yanlışlıkla bypass aktive olursa buraya girince hızlıca düzeltilecek

    if middistance < turnstop and middistance != 0.0:
        carState = 'stopped'
        
    if uprightdistance >= 3800.0 or uprightdistance == 0.0:
        print('saga don3')
        message2 = 'y'
    elif uprightdistance >= 3200.0:
        print('saga don2')
        message2 = 'h'
    else:
        print('saga don')
        message2 = 'n'
        
def turnleft():
    global message2
    global carState
    global problemsiz_kavsak

    problemsiz_kavsak = False # yanlışlıkla bypass aktive olursa buraya girince hızlıca düzeltilecek

    if middistance < turnstop and middistance != 0.0:
        carState = 'stopped'
        
    if upleftdistance >= 3800.0 or upleftdistance == 0.0:
        print('sola don3')
        message2 = 't'
    elif upleftdistance >= 3200.0:
        print('sola don2')
        message2 = 'g'
    else:
        print('sola don')
        message2 = 'b'
        
def acilstop():
    global carState
    global old_carState
    global message
    global message2
    global text
    global ts
    global tsd
    global turnControl
    global Turning
    global signCarrier
    
    carState = 'stopped'
    old_carState = 'moving'
    message = 's\n'
    message2 = 'o\n'
    text = 'tabela yok'
    ts = 0
    tsd = 0
    turnControl = 0
    Turning = False

    serialcomm.write(message.encode())
    time.sleep(0.1)
    print(message.encode())
    
    serialcomm.write(message2.encode())
    time.sleep(0.1)
    #print(serialcomm.readline().decode('ascii'))

    #pyautogui.press(message)
    #pyautogui.press(message2)
    
    for i in range(0,12):
        signCarrier[i] = False

    # yapay zekanın aracı sıfırlama işi bitince AKS ile bağlantısının kesilmesi için AKS'ye acilstop_so gönder                    !!!!! B12 !!!!!

    message = 'acilstop_so\n'
    if message != '':

        time.sleep(0.30)
        while serialcomm.write((message).encode()) < 1:
            print('message tekrar')

            pass
        serialcomm.reset_output_buffer()
        print(message.encode())

        # pyautogui.press(message)
        message = ''

    print('...BEF-Otonom Durduruldu...')
    message = ''
    message2 = ''