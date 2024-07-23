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
from collections import Counter

df = pd.read_excel(f"Выгрузка Avito3.xlsx", sheet_name='Sheet1')
unique_Ids = df["Id"]

print(len(df))
df = df.drop_duplicates(subset=["Id"], keep='first')
print(len(df))

c = Counter(unique_Ids)
# print(c)

df.to_excel(f'Выгрузка Avito3.xlsx', sheet_name='Sheet1', index=False)
