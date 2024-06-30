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

# my modules
from donor_checkers.utils.format_image import format_image
from donor_checkers.utils.yandex_api import get_new_link, create_folder, upload_file
from donor_checkers.utils.change_dateend import change_dateend

def garopt_check(donor_links, discount, days_delta, yandex_token, yandex_image_folder_path, annex, check_new, excel_file_name, currencies, periodic_save_delta):
    
    for link in donor_links:
        # парсим xml донора
        xml_response = requests.get(donor_link)
        root = ET.fromstring(xml_response.text)
        offer_list = root.find('shop').find('offers').findall('offer')

        # открываем xlsx файл выгрузки
        df = pd.read_excel(f"{excel_file_name}.xlsx", sheet_name='Sheet1')
        unique_Ids = df["Id"]

        yesterday = str((datetime.now() - timedelta(days=1)).date().strftime("%d.%m.%Y"))

        # для работы с Yandex.Диском
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {yandex_token}'}
        create_folder(yandex_image_folder_path, headers) # создание папки, если ее нет
        new_count = 0

        # добавление новых позиций
        if check_new:
            # загрузка категорий
            categoryDict = {}
            for category in root.find('shop').find('categories').findall('category'):
                categoryID = category.attrib['id']
                categoryDict[categoryID] = category.text

            print('Добавление новых позиций')
            for offer in offer_list[:]:
                # vendorCode
                vendorCode = offer.find('vendorCode').text
                if vendorCode not in unique_Ids.values:
                    new_index = len(df.index)
                    
                    # price
                    try:
                        valute = offer.find('currencyId').text
                        if valute != "RUB":
                            course = currencies['Valute'][valute]['Value']
                        else:
                            course = 1
                        price = round(float(donor_df['Цена'][i])*((100 - discount)/100) * float(course), 0) 
                        if float(price) < 3000:
                            continue
                    except:
                        price = -1
                    
                    # title
                    title = offer.find('name').text

                    # category
                    categoryID = offer.find('categoryId').text
                    try:
                        category = categoryDict[categoryID]
                    except:
                        category = ""

                    # main Photo + dop
                    imageUrls = []
                    pictures = offer.findall('picture')
                    try:
                        origURL = pictures[0]
                        filename = origURL.split('/')[-1]
                        resized_img = format_image(origURL)
                        cv2.imwrite(filename, resized_img)
                        upload_file(filename, f'{yandex_image_folder_path}/{filename}', headers, True)
                        os.remove(filename)
                        new_URL = get_new_link(filename, yandex_image_folder_path)
                        imageUrls.append(new_URL) # главная картинка в формате 4:3
                    except:
                        imageUrls.append('invalid link') 
                        
                    images = ""
                    try:
                        images = donor_df['Фото доп'][i].split(',')
                        for image in images:
                            imageUrls.append(image.strip()) # дополнительные картинки
                    except:
                        pass
                    imageUrls = " | ".join(imageUrls)

                    # description
                    if not pd.isna(donor_df['Описание'][i]):
                    #     description_long = []
                    #     for sentence in elem.find('description_long').text.split('.'):
                    #         sentence = re.sub(" +", " ", sentence)
                    #         sentence = re.sub("\n+", "\n", sentence)
                    #         sentence = re.sub("\n ", "\n", sentence)
                    #         description_long.append(sentence.strip())
                    #     description_long = '\n'.join(description_long)
                    #     description = f"{description_long}\n{params}\n\n{annex}"
                    # else:
                        description = f"{donor_df['Описание'][i]}\n{annex}"

                    # запись
                    new_count += 1
                    df.loc[new_index, 'Id'] = vendorCode
                    df.loc[new_index, 'Title'] = title
                    df.loc[new_index, 'Price'] = price
                    df.loc[new_index, 'Category'] = category
                    df.loc[new_index, 'Description'] = description
                    df.loc[new_index, 'ImageUrls'] = imageUrls
                    # периодический сейв
                    if i!=0 and i%periodic_save_delta == 0:
                        df['DateEnd'] = pd.to_datetime(df['DateEnd']).dt.date
                        df = df.drop_duplicates(subset=["Id"], keep='last')
                        df.to_excel(f'{excel_file_name}.xlsx', sheet_name='Sheet1', index=False)

        old_count = 0
        # Обновление существующих позиций в выгрузке
        print('Обновление существующих')
        for i in trange(len(df)):
            vendorCode = df.loc[i, 'Id']
            # dateend = change_dateend(str(df.loc[i, 'Availability']), str(df.loc[i, 'AvitoStatus']), yesterday)
            for j in range(len(donor_df)):
                donor_id = f'ironmac-{donor_df['id'][j]}'
                
                if vendorCode == donor_id:
                    # цена
                    try:
                        valute = donor_df['Валюта'][i]
                        if valute != "RUB":
                            course = currencies['Valute'][valute]['Value']
                        else:
                            course = 1
                        price = round(float(donor_df['Цена'][i])*(1 - discount/100) * float(course), 0)
                    except:
                        continue

                    if float(price) < 0 or float(price) > 3000: 
                        # наличие
                        if donor_df['Статус'][j] == "В наличии":
                            availability = "В наличии"
                        else:
                            availability = "Нет в наличии"
                    else: # делаем позиции неактивными с ценой меньше 3к
                        availability = "Нет в наличии"

                    # DateEnd
                    dateend = change_dateend(availability, str(df.loc[i, 'AvitoStatus']), yesterday)

                    # запись
                    df.loc[i, 'Price'] = price
                    df.loc[i, 'Availability'] = availability
                    df.loc[i, 'DateEnd'] = dateend
                    old_count += 1
                    break
            
        # обработка перед финальным сохранением и сохранение
        df['DateEnd'] = pd.to_datetime(df['DateEnd']).dt.date
        df = df.drop_duplicates(subset=["Id"], keep='last')
        df.to_excel(f'{excel_file_name}.xlsx', sheet_name='Sheet1', index=False)
        upload_file(f'{excel_file_name}.xlsx', f'/{excel_file_name}.xlsx', headers, replace=True)

        return {'new': new_count, 'old': old_count}
    
    

currencies = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
donor_links = ["https://garopt.online/yandexmarket/95605b0a-b97e-49ea-8026-82ed7393f9b8.xml", 
              "https://garopt.online/yandexmarket/5e13177a-8ca9-483d-b442-b9f3a7f3fcbc.xml",
              "https://garopt.online/yandexmarket/9fc40bc6-b745-48be-a919-ec4a4572b21a.xml"]
discount = 25
days_delta = 14
yandex_token = "y0_AgAAAAB2eAMkAAvtEgAAAAEHDYscAAAO0qWJlTtHEYrzMF1eVgrRvisOSQ"
yandex_image_folder_path = "Garopt Main pictures"
annex = "<p><br/></p> <p><strong>✅✅✅✅✅ Гарантия 12 месяцев! 💫💫💫💫💫</strong></p> <p><strong>🚕🚕🚕🚕🚕 Оперативная Доставка по России Транспортными компаниями 🚛🚛🚛 Доставляем по СПб за 1 час! 🚁🚁🚁🚁🚁</strong></p> <p><strong>🔥🔥🔥🔥🔥 Добавляйте объявление в избранное что бы не потерять  🔥🔥🔥🔥🔥</strong></p> <p><strong>🔫🔨🔧 Оперативный гарантийный сервис! 🔫🔨🔧</strong></p> <p><strong>📲📲📲 Обращайтесь за помощью в сообщениях или по телефону, всегда на связи! 📞📞📞</strong></p>"
check_new = True
excel_file_name = 'Выгрузка Garopt'

garopt_check(donor_links, discount, days_delta, yandex_token, yandex_image_folder_path, annex, check_new, excel_file_name, currencies, 15)