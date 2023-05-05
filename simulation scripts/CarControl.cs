using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Globalization;
using System.Threading;
// ...

public class CarControl : MonoBehaviour
{
    // Araç dinamikleri için değişkenler
    public WheelCollider w_frontDriver;
    public WheelCollider w_frontPassenger;
    public WheelCollider w_backDriver;
    public WheelCollider w_backPassenger;

    public Transform t_frontDriver;
    public Transform t_frontPassenger;
    public Transform t_backDriver;
    public Transform t_backPassenger;

    // teker dönme efektleri için pozisyon tutacak değişkenler
    private Vector3 pos;
    private Quaternion rot;

    // Sürüş için gereken değişkenler
    public float verticalInput;  // aracın hareket durumu için klavyeden alınan dikey girdi
    public float torque = 267.0f;  // tork
    public float currentSpeed;  // anlık hız
    private float maxSpeed = 8.0f;  // maksimum hız
    private float torqueFactor = 0.4f;  // hıza bağlı hızlama için kullanılan tork katsayısı (Kp)
    public float torqueCommand = 0.0f;  // oransal algoritma ile elde edilen tork komutu
    public bool forward = false;  // aracın hareket durumu
    private float steeringAngle;  //dönüş açısı
    private float step = 0.21f;  // step başına dönülecek açı
    public int stepCount = 0;  // anlık step
    private int maxStep = 63;  // maksimum step
    private float stepNumber;  //pid_kontrol algoritmasından gelen step miktarı

    // Pid_kontrol algoritması ile iletisim için gereken değişkenler
    private string dosyayolu = "C:/yolov5-proje/pid_output.txt";
    private string satir = "";

    // manuel manevra için değişkenler
    private float temp = 0;
    private bool overrided = false;

    public void Start()
    {
        // teker dönme efektleri için pozisyon tutacak değişkenler
        pos = transform.position;
        rot = transform.rotation;
    }

    void Update()
    {
        Drive();
    }

    public void CarBrake()
    {
        w_frontDriver.motorTorque = 0;
        w_frontPassenger.motorTorque = 0;
        w_frontDriver.brakeTorque = torque;
        w_frontPassenger.brakeTorque = torque;
        w_backDriver.brakeTorque = torque;
        w_backPassenger.brakeTorque = torque;
    }

    public void CarDrive()
    {
        w_frontDriver.brakeTorque = 0;
        w_frontPassenger.brakeTorque = 0;
        w_backDriver.brakeTorque = 0;
        w_backPassenger.brakeTorque = 0;

        // hızlandıkça gazdan ayağını çeker gibi çalışan algoritma
        // maksimum hıza 2.5kmh kala torku düşürmeye başlıyor. çünkü konfigürasyon katsayısı 0.4 olduğu için maks hızın 4te birini geçene kadar maks torku uyguluyor
        if (currentSpeed >= maxSpeed)  //istenen hıza gelinir ise araç gazı keser
        {
            w_frontDriver.motorTorque = 0;
            w_frontPassenger.motorTorque = 0;
        }
        else
        {
            torqueCommand = torque * (maxSpeed - currentSpeed) * torqueFactor; // maksimum hıza olan hata miktarı torqueFactor konfigürasyon katsayısı ile çarpılıyor ve oransal katsayı elde edilmiş oluyor
            if (torqueCommand > torque)
            {
                torqueCommand = torque;  // oransal hesap sonrası maksimum torktan daha yüksek bir değer gelir ise tork değeri maksimum değere sabitlenir
            }
            w_frontDriver.motorTorque = torqueCommand;
            w_frontPassenger.motorTorque = torqueCommand;
        }
    }

    public void CarTurn()
    {
        w_frontDriver.steerAngle = steeringAngle;
        w_frontPassenger.steerAngle = steeringAngle;
        Transformations(); // görsel olan tekerleklerin döndürülmesi
    }

    public void Transformations()
    {
        w_frontDriver.GetWorldPose(out pos, out rot); //out: fonksiyondaki işlerin, fonksiyona gönderilen değişkenin adresine yapılmasını sağlıyor
        t_frontDriver.transform.position = pos;
        t_frontDriver.transform.rotation = rot;

        w_frontPassenger.GetWorldPose(out pos, out rot);
        t_frontPassenger.transform.position = pos;
        t_frontPassenger.transform.rotation = rot;

        w_backDriver.GetWorldPose(out pos, out rot);
        t_backDriver.transform.position = pos;
        t_backDriver.transform.rotation = rot;

        w_backPassenger.GetWorldPose(out pos, out rot);
        t_backPassenger.transform.position = pos;
        t_backPassenger.transform.rotation = rot;
    }
    
    private int check_encoder() //konsept
    {
        return 0; //encoder veri alma fonksiyonundan dönen değer dönüdürülür
    }

    public void Drive()
    {

        //stepCount = check_encoder();   //encoder olmadığı için kapalı olmalı

        try
        {
            FileStream fileStream = new FileStream(dosyayolu, FileMode.OpenOrCreate, FileAccess.ReadWrite);
            //dosyadan satır satır okuyup textBox içine yazıdırıyoruz
            using (StreamReader reader = new StreamReader(fileStream))
            {
                satir = reader.ReadLine();
                reader.Close();
            }
            fileStream.Close();
            //print("veri = " + satir);
        }
        catch
        {
            //print("dosya acilamadi");
        }


        stepNumber = float.Parse(satir, CultureInfo.InvariantCulture.NumberFormat);  //Pid_Kontrol algoritmasından gelen step verisi
        //print(step_number);

        // elle döndürme sonrası eski açıya dönüş
        if (overrided == true)
        {
            steeringAngle = temp;
            overrided = false;
        }
        //
        if (stepCount < stepNumber && stepCount < maxStep)
        {
            stepCount++;
            steeringAngle += step;
        }
        else if (stepCount > stepNumber && stepCount > -maxStep)
        {
            stepCount--;
            steeringAngle -= step;
        }
        // elle döndürme kodu
        if (Input.GetKeyDown("d"))
        {
            overrided = true;
            temp = steeringAngle;
            steeringAngle = maxStep * step;
        }
        else if (Input.GetKeyDown("a"))
        {
            overrided = true;
            temp = steeringAngle;
            steeringAngle = -maxStep * step;
        }
        //
        CarTurn();  // alınan dönüş verileri araca uygulanır
        currentSpeed = 2 * Mathf.PI * w_frontDriver.radius * w_frontDriver.rpm * 60 / 1000;  //Anlık araç hızı alınır
        verticalInput = Input.GetAxisRaw("Vertical");  //araç hareket durumu için ileri geri verisini alınır

        if (verticalInput < 0)  //geri tuşuna basılır ise 
        {
            CarBrake();  //Araç durdurulur
            forward = false;
        }
        else if (forward || verticalInput > 0)  //ileri verisi bir kere alındıktan sonra forward true olur. Bu sayede sürekli olarak ileriye basılması gerekmez
        {
            CarDrive();  //Araç harekete geçirilir
            forward = true;
        }

        if (overrided)  //manuel bir dönüş komutu alınmış ise
        {
            Thread.Sleep(50); // otonom gelen kararın manuel dönüş komutunun önüne hemen geçememesi için tanılan süre
        }
    }
}