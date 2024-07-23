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
from donor_checkers.utils.format_image import format_image
from donor_checkers.utils.yandex_api import get_new_link, create_folder, upload_file
from donor_checkers.utils.change_dateend import change_dateend

def wiederkraft_check(donor_link, discount, days_delta, yandex_token, yandex_image_folder_path, annex, check_new, excel_file_name, currencies, periodic_save_delta):
    
    yesterday = (datetime.now() - timedelta(days=1)).date().strftime("%Y-%m-%d")

    # для работы с Yandex.Диском
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {yandex_token}'}
    create_folder(yandex_image_folder_path, headers) # создание папки, если ее нет
    
    # открываем xlsx файл выгрузки
    df = pd.read_excel(f"{excel_file_name}.xlsx", sheet_name='Sheet1')
    unique_Ids = df["Id"]

    # выявление последней страницы
    first_page = requests.get(f"{donor_link}/{1}/")
    html = BS(first_page.content, 'html.parser')
    max_page_number = 0
    for product in html.find_all("a", {"class": "page-numbers"}):
        if product.text.isdigit() and int(product.text) > max_page_number:
            max_page_number = int(product.text)

    new_count = 0

    # добавление новых позиций
    if check_new:
        for i in trange(max_page_number):
            page = requests.get(f"{donor_link}/{i+1}/")
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
                        # if price < 8000:
                        #     price_lower_count += 1
                        #     break

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
                        category = category[1:-1]
                        while len(category) < 3:
                            category.append('')
                        # category = ' | '.join(category[1:-1])

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
                        description = f"{title}\n{description}\n{annex}"

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
                        df.loc[new_index, 'Category'] = category[0]
                        df.loc[new_index, 'GoodsType'] = category[1]
                        df.loc[new_index, 'ProductType'] = category[2]
                        df.loc[new_index, 'Description'] = description
                        df.loc[new_index, 'ImageUrls'] = imageUrls
                        if 70 < len(df) and 80 > len(df):
                            print(f'new_count {new_count}, len(df) {len(df)}, vendorCode {vendorCode}')
                        # периодический сейв
                        if new_count!=0 and (new_count%periodic_save_delta == 0):
                            # df = df.drop_duplicates(subset=["Id"], keep='last')
                            df.to_excel(f'{excel_file_name}.xlsx', sheet_name='Sheet1', index=False)
                            sleep(1)

                            
            except Exception as e:
                print(e)
                break

    old_count = 0
    # Обновление существующих позиций в выгрузке
    # print("Обновление существующих позиций:")
    # for i in trange(len(df)):
    #     # description = f"{df.loc[i, 'Title']}\n{df.loc[i, 'Description']}\n{annex}"

    #     # запись
    #     old_count += 1
    #     # df.loc[i, 'Description'] = description
        
    # обработка перед финальным сохранением и сохранение
    df['DateEnd'] = pd.to_datetime(df.DateEnd).dt.strftime('%Y-%m-%d')
    df = df.drop_duplicates(subset=["Id"], keep='last')
    df.to_excel(f'{excel_file_name}.xlsx', sheet_name='Sheet1', index=False)
    upload_file(f'{excel_file_name}.xlsx', f'/{excel_file_name}.xlsx', headers, replace=True)

    return {'new': new_count, 'old': old_count}
    