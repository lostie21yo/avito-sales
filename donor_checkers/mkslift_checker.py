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

def mkslift_check(donor_link, discount, days_delta, yandex_token, yandex_image_folder_path, annex, check_new, excel_file_name, currencies, periodic_save_delta):

    # парсим xml донора
    xml_response = requests.get(donor_link)
    root = ET.fromstring(xml_response.text)
    offer_list = root.find('shop').find('offers').findall('offer')

    # открываем xlsx файл выгрузки
    df = pd.read_excel(f"{excel_file_name}.xlsx", sheet_name='Sheet1')

    yesterday = str((datetime.now() - timedelta(days=1)).date().strftime("%d.%m.%Y"))

    # для работы с Yandex.Диском
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {yandex_token}'}
    create_folder(yandex_image_folder_path, headers) # создание папки, если ее нет

    for i in trange(len(df)):
        vendorCode = df.loc[i, 'Id']
        # dateend = change_dateend(str(df.loc[i, 'Availability']), str(df.loc[i, 'AvitoStatus']), yesterday)
        for offer in offer_list[:]:
            if vendorCode == offer.find('vendorCode').text: # обработка существующих позиций из выгрузки
                # index = df[df['Id'] == offerVendorCode].index[0]
                # vendorCode = df.loc[index, 'Id']
                # цена
                try:
                    price = round(float(offer.find('price').text)*((100 - discount)/100), 0)
                except:
                    continue

                if float(price) > 3000: 
                    # наличие
                    if offer.attrib['available'] == "true":
                        availability = "В наличии"
                    if offer.attrib['available'] == "false":
                        availability = "Нет в наличии"
                else: # делаем позиции неактивными с ценой меньше 3к
                    availability = "Нет в наличии"

                # DateEnd
                dateend = change_dateend(availability, str(df.loc[i, 'AvitoStatus']), yesterday)

                # запись
                df.loc[i, 'Price'] = price
                df.loc[i, 'Availability'] = availability
                df.loc[i, 'DateEnd'] = dateend
                break
        

    # обработка перед финальным сохранением и сохранение
    df['DateEnd'] = pd.to_datetime(df['DateEnd']).dt.date
    df = df.drop_duplicates(subset=["Id"], keep='last')
    df.to_excel(f'{excel_file_name}.xlsx', sheet_name='Sheet1', index=False)
    upload_file(f'{excel_file_name}.xlsx', f'/{excel_file_name}.xlsx', headers, replace=True)

        # проверка наличия и добавление новых позиций
    #     if False: # check_new   |   first_launch_date == datetime.now().date()
            
    #         # загрузка категорий
    #         categoryDict = {}
    #         for category in root.find('shop').find('categories').findall('category'):
    #             categoryID = category.attrib['id']
    #             categoryDict[categoryID] = category.text

    #         for offer in tqdm(offer_list[:]):

    #             new_index = len(df.index)

    #             # url
    #             page_url = offer.find('url').text

    #             # артикул
    #             vendorCode = offer.find('vendorCode').text

    #             # категории ID
    #             categoryID = offer.find('categoryId').text
    #             try:
    #                 categoryIDtext = categoryDict[categoryID]
    #             except:
    #                 categoryIDtext = ""

    #             # получаем и формируем title
    #             vendor = offer.find('vendor').text  
    #             title = f"{offer.find('name').text.split(vendor)[-1].split(vendorCode)[-1].strip()} {vendorCode} {vendor}"
                
    #             # цена
    #             try:
    #                 price = round(float(offer.find('price').text)*0.95, 0)
    #             except:
    #                 price = -1

    #             # наличие
    #             isAvailable = ""
    #             if offer.attrib['available'] == "true":
    #                 isAvailable = "В наличии"
    #             if offer.attrib['available'] == "false":
    #                 isAvailable = "Нет в наличии"

    #             # описание и категория
    #             category = ""
    #             params = []
    #             for param in offer.findall('param'):
    #                 # if param.attrib['name'] != 'articul':
    #                 pattern = "(?<=&gt;)(.*)(?=&lt;)|(?<=;'>)(.*)(?=</span>)"
    #                 name = param.attrib['name']
    #                 # извлечение значения 
    #                 if "span" in param.text:
    #                     value = re.search(pattern, param.text)[0]
    #                 elif param.text == "":
    #                     value = ""
    #                 else:
    #                     value = param.text
    #                 # извлечение unit'а
    #                 unit = ""
    #                 if 'unit' in param.attrib:
    #                     if "span" in param.attrib['unit']:
    #                         unit = re.search(pattern, param.attrib['unit'])[0]
    #                     elif param.text == "":
    #                         unit = ""
    #                     else:
    #                         unit = param.attrib['unit']
    #                 params.append(f'{name}   {value} {unit}')

    #                 # обновление param категории
    #                 if name == "Категория":
    #                     category = param.text
                

    #             # выявление категории


    #             params = '\n'.join(params)
    #             if offer.find('description_long').text is not None:
    #                 description_long = []
    #                 for sentence in offer.find('description_long').text.split('.'):
    #                     sentence = re.sub(" +", " ", sentence)
    #                     sentence = re.sub("\n+", "\n", sentence)
    #                     sentence = re.sub("\n ", "\n", sentence)
    #                     description_long.append(sentence.strip())
    #                 description_long = '\n'.join(description_long)
    #                 description = f"{description_long}\n{params}\n\n{annex}"
    #             else:
    #                 description = f"{params}\n{annex}"
    #             # print(description)
                
    #             # images urls
    #             imageUrls = []
    #             if offer.find('picture') is not None:
    #                 origURL = offer.find('picture').text
    #                 origURL = origURL.replace("http://www.mkslift.ruhttp://www.mkslift.ru", "http://www.mkslift.ru")
    #                 filename = origURL.split('/')[-1]
    #                 # resized_img = format_image(origURL)
    #                 # cv2.imwrite(filename, resized_img)
    #                 # upload_file(filename, f'{y_folder}/{filename}')
    #                 # os.remove(filename)
    #                 new_URL = get_new_link(filename, yandex_image_folder_path)
    #                 imageUrls.append(new_URL) # главная картинка в формате 4:3

    #             if offer.find('images') is not None:
    #                 for image in offer.find('images').findall('image'):
    #                     imageUrls.append(image.text) # дополнительные картинки
    #             imageUrls = " | ".join(imageUrls)

    #             # video url
    #             page_url_response = requests.get(page_url)
    #             html = BS(page_url_response.content, 'html.parser')
    #             try:
    #                 frame = html.find_all('iframe')[0]
    #                 videoUrl = frame.get('src').split('embed/')
    #                 videoUrl = videoUrl[0] + 'watch?v=' + videoUrl[1].split("?")[0]
    #             except:
    #                 videoUrl = ""

    #             # добавление с фильтрацией
    #             if float(price) < 0 or float(price) > 3000:
    #                 df.loc[new_index, 'paramCategory'] = category
    #                 df.loc[new_index, 'categoryIDtext'] = categoryIDtext
    #                 df.loc[new_index, 'Id'] = vendorCode
    #                 df.loc[new_index, 'Title'] = title
    #                 df.loc[new_index, 'Price'] = price
    #                 df.loc[new_index, 'Availability'] = isAvailable
    #                 df.loc[new_index, 'Description'] = description
    #                 df.loc[new_index, 'ImageUrls'] = imageUrls
    #                 df.loc[new_index, 'VideoUrl'] = videoUrl
    #                 # категории
    #                 # df.loc[new_index, 'categoryIDtext'] = categoryIDtext

    #             df.to_excel(f'output/{file_name}', sheet_name='Sheet1', index=False)

    return {'info': 'to be continued...'}
    