from PIL import ImageGrab
import pyvirtualcam
import numpy as np

x = 260
y = 90
width = 1280
height = 720

with pyvirtualcam.Camera(width=width, height=height, fps=30) as cam:
    while True:
        img = ImageGrab.grab(bbox=(x, y, width+x, height+y))
        img_np = np.array(img)

        cam.send(img_np)
        cam.sleep_until_next_frame()
        cam.sleep_until_next_frame()