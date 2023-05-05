import time
import pyautogui
import PID

signCarrier = [False, False]  # kırmızı, durak

carState = 'moving'  # araç ilk hamle olarak harekete geçmek ister

ts = 0  # yolcu iniş biniş için ayrılan süreyi tutacak değişken
passenger_moving = False
passenger_in = False

def SignDetected(sign, distance):
    global signCarrier

    if sign == 'kirmizi' and distance <= 6:  # kırmızı ışığın dikkate alınması için belirli bir mesafeden yakın olması gerekir
        signCarrier[0] = True
    elif sign == 'durak' and distance <= 3:  # durak tabelasın dikkate alınması için belirli bir mesafeden yakın olması gerekir
        signCarrier[1] = True

def AutonomousDrive():
    global carState, signCarrier, passenger_in, passenger_moving

    checkLight()  # tabelaların döngülerini etkilememesi için ışık önce gelmeli
    checkForPassenger()

    if carState == 'moving':
        print('harekete geç')
        pyautogui.press("w")  # aracı harekete geçirme işlemi
        PID.arac_hareketi = True  # aracın hareket haline geçtiğini PID kısmına haber veriyor

    elif carState == 'stopped':
        print('arabayi durdur')
        pyautogui.press("s")  # aracın durdurulma işlemi
        PID.arac_hareketi = False  # aracın durduğunu PID kısmına haber veriyor

    for i in range(0, 2):  # hafızaya alınmış tabelaları siler
        signCarrier[i] = False

    if passenger_moving is True:
        if passenger_in:
            print('!!hedefe ulaşıldı!!')
            return 1  # otonom modu kapamak için dönen değer
        else:
            time.sleep(5)  # yolcuya iniş biniş için tanınan süre
            passenger_in = True
            passenger_moving = False
            carState = 'moving'

    return 0  # normal durumda dönen değer


def checkLight():
    global carState

    if signCarrier[0] is True:  # kırmızı ışık
        carState = 'stopped'
    else:
        carState = 'moving'


def checkForPassenger():
    global carState, ts, passenger_moving

    # hata önleme amaçlı 30 saniye boyunca yeni bir durak tabelası kabul etmez.
    # tabelayı geçtiğinde de işlem yapılabilirdi ancak bazen bu tabela görünürken bir anlığına görünmeyip tekrar görünebiliyor
    # görüntü işleme %100 güvenilmediği için böyle olmalı.
    if signCarrier[1] is True and (ts + 30) <= time.time():
        carState = 'stopped'
        passenger_moving = True
        ts = time.time()
        

# Acil duruş sonrasında sistemin tekrar çalışabilmesi amacıyla değişkenleri sıfırlama fonksiyonu
def emergencyStop():
    global carState, signCarrier, ts, passenger_moving

    pyautogui.press("s")
    PID.arac_hareketi = False
    print('araç durduruldu')

    carState = 'moving'
    ts = 0
    passenger_moving = False

    for i in range(0, 2):
        signCarrier[i] = False

    print('...Otonom mod devre dışı...')
