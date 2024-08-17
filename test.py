import os
import sys
import re
import cv2
from time import sleep
import requests
import pandas as pd
from datetime import *
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup as BS
from tqdm import tqdm, trange
from PIL import Image
from urllib.request import urlopen

# my modules
from donor_checkers.utils.format_image import format_image, get_ascii_url
from donor_checkers.utils.yandex_api import get_new_link, create_folder, upload_file
from donor_checkers.utils.change_dateend import change_dateend

product_page = requests.get("https://100kwatt.ru/nasos-nrg-2500/")
product_html = BS(product_page.content, 'html.parser')

title = product_html.find_all("bdi")
print(title)

# title = product_html.find("div", {"class": "ut2-pb__title ut2-pb__title-wrap"}).h1.text.strip()