import cv2
from urllib.request import urlopen
import numpy as np

def format_image(link, target_size = (1280, 960)):
    req = urlopen(link)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img = cv2.imdecode(arr, -1) # 'Load it as it is'
    h, w = img.shape[:2]

    coef1 = target_size[0]/w
    coef2 = target_size[1]/h

    if coef1 < coef2:
        new_w, new_h = target_size[0], round(h*coef1)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        line_height = round((target_size[1] - new_h)/2)
        nul = np.full((line_height, new_w, 3), 255)
        img = np.vstack((nul, img))
        img = np.vstack((img, nul))
    else:
        new_w, new_h = round(w*coef2), target_size[1]
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        line_width = round((target_size[0] - new_w)/2)
        nul = np.full((new_h, line_width, 3), 255)
        img = np.hstack((nul, img))
        img = np.hstack((img, nul))

    # конечный ресайз
    # img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
    # сохранение
    # cv2.imwrite("prog1/new_image.jpg", img)
    return img
