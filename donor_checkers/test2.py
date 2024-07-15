from bs4 import BeautifulSoup as BS
import requests
from time import sleep
import re

import os
import sys
import cv2
import pandas as pd
import requests
from datetime import *
from tqdm import tqdm, trange
from PIL import Image
from urllib.request import urlopen

# my modules
from utils.format_image import format_image
from utils.yandex_api import get_new_link, create_folder, upload_file
from utils.change_dateend import change_dateend

def wiederkraft_check(donor_link, discount, days_delta, yandex_token, yandex_image_folder_path, annex, check_new, excel_file_name, currencies, periodic_save_delta):
    
    yesterday = (datetime.now() - timedelta(days=1)).date().strftime("%Y-%m-%d")

    # для работы с Yandex.Диском
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {yandex_token}'}
    create_folder(yandex_image_folder_path, headers) # создание папки, если ее нет

    # открываем xlsx файл выгрузки
    df = pd.read_excel(f"{excel_file_name}.xlsx", sheet_name='Sheet1')
    unique_Ids = df["Id"]

    # main_r = requests.get('https://wiederkraft.ru/shop')
    # html = BS(main_r.content, 'html.parser')
    new_count = 0

    offset = 0

    # добавление новых позиций
    for i in trange(140-offset):
        page = requests.get(f"{donor_link}/{i+1+offset}/")
        html = BS(page.content, 'html.parser')
        try:
            for product in html.find("ul", {"class": "products"}).children:
                if product != '\n':
                    new_index = len(df.index)

                    # страница продукта
                    product_page = requests.get(product.a['href'])
                    product_html = BS(product_page.content, 'html.parser')
                    
                    # цена
                    price = float(''.join(re.findall(r'\d+', product_html.find("bdi").text)))

                    # артикул
                    try:
                        vendorCode = product_html.find("span", {"class": "sku"}).text
                    except:
                        vendorCode = "no data"
                    # title
                    title = product_html.find("h1", {"class": "product_title entry-title"}).text
                    
                    # получаем категории
                    category = []
                    for cat in product_html.find("nav", {"class": "woocommerce-breadcrumb"}).children:
                        category.append(cat.string)
                    category = ' | '.join(category[1:-1])

                    # описание 
                    description = []
                    page_description = product_html.find("div", {"id": "tab-description"}).stripped_strings
                    for string in page_description:
                        description.append(string)

                    try:
                        additional_info = product_html.find("div", {"id": "tab-additional_information"}).table.children
                        for line in additional_info:
                            string = line.get_text().strip().replace("\n", " ")
                            description.append(string)
                    except:
                        pass
                    description = '\n'.join(description).replace("\n\n", "\n")

                    # картинки
                    imageUrls = []
                    try:
                        images = product_html.find("figure", {"class": "woocommerce-product-gallery__wrapper swiper-wrapper"}).find_all("div")
                        for div in images:
                            imageUrls.append(div.a["href"])
                        
                        origURL = imageUrls[0]
                        filename = origURL.split('/')[-1]
                        resized_img = format_image(origURL)
                        cv2.imwrite(filename, resized_img)
                        upload_file(filename, f'{yandex_image_folder_path}/{filename}', headers, True)
                        os.remove(filename)
                        new_URL = get_new_link(filename, yandex_image_folder_path)
                        imageUrls[0] = new_URL # главная картинка в формате 4:3
                        imageUrls = " | ".join(imageUrls)
                    except:
                        imageUrls = 'no data'

                    # запись
                    new_count += 1
                    df.loc[new_index, 'Id'] = vendorCode
                    df.loc[new_index, 'Title'] = title
                    df.loc[new_index, 'Price'] = price
                    df.loc[new_index, 'Category'] = category
                    df.loc[new_index, 'Description'] = description
                    df.loc[new_index, 'ImageUrls'] = imageUrls
                    # периодический сейв
                    if new_count!=0 and (new_count%periodic_save_delta == 0):
                        print('saved 15')
                        df = df.drop_duplicates(subset=["Id"], keep='last')
                        df.to_excel(f'{excel_file_name}.xlsx', sheet_name='Sheet1', index=False)
        except:
            break
        
    # обработка перед финальным сохранением и сохранение
    df['DateEnd'] = pd.to_datetime(df.DateEnd).dt.strftime('%Y-%m-%d')
    df = df.drop_duplicates(subset=["Id"], keep='last')
    df.to_excel(f'{excel_file_name}.xlsx', sheet_name='Sheet1', index=False)
    upload_file(f'{excel_file_name}.xlsx', f'/{excel_file_name}.xlsx', headers, replace=True)

    return {'new': new_count, 'old': 'old_count'}


currencies = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
donor_links = "https://wiederkraft.ru/shop/page"
discount = 15
days_delta = 14
yandex_token = "y0_AgAAAAB3PjE7AAwShgAAAAEJ30hAAABEzz9MQBNKkLSRUWhuWW3Ezc9xxQ"
yandex_image_folder_path = "WiederKraft Main pictures"
annex = "<p><br/></p> <p><strong>✅✅✅✅✅ Гарантия 12 месяцев! 💫💫💫💫💫</strong></p> <p><strong>🚕🚕🚕🚕🚕 Оперативная Доставка по России Транспортными компаниями 🚛🚛🚛 Доставляем по СПб за 1 час! 🚁🚁🚁🚁🚁</strong></p> <p><strong>🔥🔥🔥🔥🔥 Добавляйте объявление в избранное что бы не потерять  🔥🔥🔥🔥🔥</strong></p> <p><strong>🔫🔨🔧 Оперативный гарантийный сервис! 🔫🔨🔧</strong></p> <p><strong>📲📲📲 Обращайтесь за помощью в сообщениях или по телефону, всегда на связи! 📞📞📞</strong></p>"
check_new = True
excel_file_name = 'Выгрузка WiederKraft'

wiederkraft_check(donor_links, discount, days_delta, yandex_token, yandex_image_folder_path, annex, check_new, excel_file_name, currencies, 15)