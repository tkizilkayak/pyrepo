import time

# pid konfigürasyon katsayıları:
kp = 0.8
ki = 0.0000000001
kd = 0.09

# şerit verileri:
ortanokta = 640  # 1280 pixel olan genişlik değerinin yarısı
solnokta = 0
sagnokta = 0

# gerekli parametreler:
pid_i = 0.0  # integral parametresi
error = 0  # anlık hata
last_error = 0  # bir önceki hata
timer = 0.0  # anlık zaman değişkeni
ts = 0.0  # bir önceki iterasyondaki zamanı tutacak değişken

arac_hareketi = False  # aracın hareket durumu

def pid_control():
    global pid_i, error, last_error, ts, timer

    if not arac_hareketi:
        #print("araç hareketsiz olduğu için değerler sıfırlandı (PID kapalı)")
        pid_reset()
    else:
        if sagnokta != 0 and solnokta != 0:
            error = (solnokta + ((sagnokta - solnokta) / 2)) - ortanokta  # hatanın hesaplanması
            timer = time.time()
            delta_time = timer - ts  # bir önceki iterasyondan bu yana geçen zaman alınıyor
            ts = timer

        if error == 0:  # hata 0 olduğunda değerler sıfırlanır ve pid çalışmaz
            print("pid kapalı")
            last_error = error
            pid_i = 0
            command = 0
            try:
                f = open("pid_output.txt", "w+")
                f.write(str(command))  # araç hala hareket halinde olduğundan yeni bir hata olmaması için direksiyon 0 konumuna getirilir
                f.seek(0)
                f.close()
            except:
                print("dosya kullanımda")
        else:  # başlangıçta delta_time tanımlanmadan hesap yapılmasın diye bu else var
            pid_p = error
            pid_d = (error - last_error) / delta_time  # geçen zamana oranla hatadaki değişim
            pid_i += error * delta_time

            command = (kp * pid_p) + (ki * pid_i) + (kd * pid_d)
            last_error = error

            try:
                f = open("pid_output.txt", "w+")
                f.write(str(command))
                f.seek(0)
                f.close()
            except:
                print("dosya kullanımda")

            #print("pid ile hesaplanan komut değeri: " + str(command))
            print("delta time: " + str(delta_time))
            #print("pid_derivative = " + str(pid_d))
            #print("pid_integral = " + str(pid_i))
        #print("sag = " + str(sagnokta))
        #print("sol = " + str(solnokta))
        print("error " + str(error))

def pid_reset():
    global pid_i, last_error, ts, timer
    #print("pid_reset")

    pid_i = 0
    last_error = 0
    ts = 0.0
    timer = 0.0
