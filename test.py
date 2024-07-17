import os
import sys
import re
import cv2
import time
import requests
import pandas as pd
from datetime import *
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup as BS
from tqdm import tqdm, trange
from PIL import Image
from urllib.request import urlopen


new_count = 0
first_page = requests.get(f"https://wiederkraft.ru/shop/page/{1}/")
html = BS(first_page.content, 'html.parser')

max_page_number = 0
for product in html.find_all("a", {"class": "page-numbers"}):
    if product.text.isdigit() and int(product.text) > max_page_number:
        max_page_number = int(product.text)

print(max_page_number)