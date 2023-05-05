using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class lamba : MonoBehaviour
{

    public GameObject kirmizi, sari, yesil;
    public float redTime = 30.0f;
    public float greenTime = 70.0f;
    public float yellowTime = 72.0f;
    public float ts = 0.0f;

    void Update()
    {

        ts += Time.deltaTime; // son frameden bu yana geçen zaman sayaca eklenir

        if (ts >= yellowTime)
        {
            ts = 0.0f;  // bir ışık döngüsü tamamlandığında sayaç tekrar başlangıç konumuna döner
        }

        if (ts < redTime)  // kırmızı ışığın yandığı süre aralığı
        {
            kirmizi.GetComponent<Renderer>().material.EnableKeyword("_EMISSION");
            sari.GetComponent<Renderer>().material.DisableKeyword("_EMISSION");
            yesil.GetComponent<Renderer>().material.DisableKeyword("_EMISSION");
        }
        if (ts > redTime && ts < greenTime)  // yeşil ışığın yandığı süre aralığı
        {
            kirmizi.GetComponent<Renderer>().material.DisableKeyword("_EMISSION");
            sari.GetComponent<Renderer>().material.DisableKeyword("_EMISSION");
            yesil.GetComponent<Renderer>().material.EnableKeyword("_EMISSION");
        }
        if (ts > greenTime)  // sarı ışığın yandığı süre aralığı
        {
            kirmizi.GetComponent<Renderer>().material.DisableKeyword("_EMISSION");
            sari.GetComponent<Renderer>().material.EnableKeyword("_EMISSION");
            yesil.GetComponent<Renderer>().material.DisableKeyword("_EMISSION");
        }

    }
}