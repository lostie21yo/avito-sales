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

def kwatt_check(donor_link, discount, days_delta, yandex_token, yandex_image_folder_path, annex, check_new, excel_file_name, currencies, periodic_save_delta):
    
    yesterday = (datetime.now() - timedelta(days=1)).date().strftime("%Y-%m-%d")

    links = donor_link.split(' | ')

    # для работы с Yandex.Диском
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {yandex_token}'}
    create_folder(yandex_image_folder_path, headers) # создание папки, если ее нет
    
    # открываем xlsx файл выгрузки
    excel_file_name = "kwatt"
    df = pd.read_excel(f"{excel_file_name}.xlsx", sheet_name='Объявления')
    unique_Ids = df["Id"]

    annex = annex.split("\nТЕЛО ОПИСАНИЯ\n")
    # выявление последней страницы
    # first_page = requests.get(f"{donor_link}/{1}/")
    # html = BS(first_page.content, 'html.parser')
    # max_page_number = 0
    # for product in html.find_all("a", {"class": "page-numbers"}):
    #     if product.text.isdigit() and int(product.text) > max_page_number:
    #         max_page_number = int(product.text)

    new_count = 0

    # добавление новых позиций
    if check_new:
        print(f'Проверка наличия новых позиций и их добавление:')
        for link in links:
            max_page_number = re.search(r'page-(\d+)', link).group(1)
            link = link.split(max_page_number)[0]
            for p in trange(int(max_page_number)):
                if p < 45:
                    continue
                page = requests.get(f'{link}{p+1}/')
                html = BS(page.content, 'html.parser')
                # print(len(html.find("div", {"id": "categories_view_pagination_contents"}).contents))
                # print(len(html.find_all("div", {"class": "ty-column4"})))
                
                for product in html.find_all("div", {"class": "ty-column4"}):
                    new_index = len(df.index)
                    product_url = product.find("div", {"class": "ut2-gl__image"}).a['href']
                    product_page = requests.get(product_url)
                    product_html = BS(product_page.content, 'html.parser')
                        
                    # цена
                    try:
                        price = int(''.join(re.findall(r'\d+', product_html.find("span", {"class": "ty-price-num"}).text)))
                    except:
                        price = float('nan')
                    # if price < 15000:
                    #     continue

                    # артикул
                    try:
                        vendorCode = "KWT-" + re.search(r': ([\d\w -/]+) \(', product_html.find("div", {"class": "ut2-pb__sku"}).text)[1]
                    except:
                        vendorCode = "no data"
                        print(p+1, 'no vendorCode')

                    if vendorCode not in unique_Ids.values:
                        # title
                        try:
                            title = product_html.find("div", {"class": "ut2-pb__title"}).h1.text.strip()
                        except:
                            title = 'no data'
                            print(p+1, vendorCode, 'no title, wtf?')
                        
                        # получаем категории
                        category = []
                        breadcrumb = product_html.find("div", {"class": "ty-breadcrumbs clearfix"})
                        for cat in breadcrumb.find_all("a"):
                            category.append(cat.string)
                        category = category[2:4]
                        # while len(category) < 2:
                            # category.append('')
                        # category = ' | '.join(category)

                        # описание
                        description = []
                        
                        page_description = product_html.find("div", {"id": "content_description"}).div
                        if page_description is not None:
                            for child in page_description.children:
                                if child.name == 'ul':
                                    for li in child.children:
                                        if li.text != ' ':
                                            if li.text.startswith('-'):
                                                description.append('   ' + li.text)
                                            else:
                                                description.append(' - ' + li.text)
                                elif child.name == 'ol':
                                    counter = 0
                                    for li in child.children:
                                        if li.text != ' ':
                                            counter += 1
                                            description.append(f' {counter}. ' + li.text)
                                elif child.name == 'table':
                                    try:
                                        for col in range(len(child.tbody.tr.contents)):
                                            description.append(f' - {child.tbody.contents[0].contents[col].text}: {child.tbody.contents[1].contents[col].text}')
                                    except:
                                        for tr in child.tbody.children:
                                            description.append(tr.text.strip())
                                else:
                                    description.append(child.text)

                        description = '\n\n'.join([x for x in description if x not in ('', ' ')])
                        # description.replace(r';\d+)', ';\n - ')
                        description = re.sub(r';\d+\)', ';\n - ', description)
                        description = re.sub(r':\n\n\d+\)', ':\n - ', description)
                        description = re.sub(r'\n\n ', '\n ', description)
                        description = re.sub(r';\s*  ', '\n ', description)
                        description = re.sub(r'  ', ' ', description)
                        description = re.sub(r'\n-', ' -', description)
                        description = description.strip()   

                        # основные характеристики
                        try:
                            page_feature = product_html.find("div", {"class": "ut2-pb__first"}).find_all("span", {"class": "ty-control-group"})
                            description += '\n'
                            for feature in page_feature:
                                description = description + f'\n{feature.contents[0].text}: {feature.contents[1].text}'
                                if feature.contents[0].text == "БРЕНД":
                                    brand = feature.contents[1].text
                        except:
                            print(p+1, vendorCode, 'no additional features')

                        
                        # description = f"{title}\n{annex[0]}\n{description}\n{annex[1]}" # чтобы потом изменить

                        # картинки
                        try:
                            imageUrls = []
                            images = product_html.find("div", {"class": "ut2-pb__img-wrapper"}).find_all("a")
                            for a in images:
                                try:
                                    if '/images/' in a["href"]:
                                        imageUrls.append(a["href"])
                                except: pass
                                
                            origURL = get_ascii_url(imageUrls[0])
                            filename = origURL.split('/')[-1].split('.')[0] + '.jpg'
                            resized_img = format_image(origURL)
                            cv2.imwrite(filename, resized_img)
                            upload_file(filename, f'{yandex_image_folder_path}/{filename}', headers, True)
                            os.remove(filename)
                            new_URL = get_new_link(filename, yandex_image_folder_path)
                            imageUrls[0] = new_URL # главная картинка в формате 4:3
                            imageUrls = " | ".join(imageUrls)
                        except:
                            print(f'page {p+1} | {vendorCode} | no images')
                            imageUrls = "no data"

                        # запись
                        new_count += 1
                        df.loc[new_index, 'Id'] = vendorCode
                        df.loc[new_index, 'Brand'] = brand
                        df.loc[new_index, 'Title'] = title
                        df.loc[new_index, 'Price'] = price
                        df.loc[new_index, 'Category'] = category[0]
                        df.loc[new_index, 'GoodsType'] = category[1]
                        df.loc[new_index, 'Description'] = description
                        df.loc[new_index, 'ImageUrls'] = imageUrls

                        # периодический сейв
                        if new_count!=0 and (new_count%periodic_save_delta == 0):
                            # df = df.drop_duplicates(subset=["Id"], keep='last')
                            df.to_excel(f'{excel_file_name}.xlsx', sheet_name='Объявления', index=False)
                            sleep(1)
                            

    old_count = 0
    # # Обновление существующих позиций в выгрузке
    # print("Обновление существующих позиций:")
    # for i in trange(len(df)):
    #     vendorCode = df.loc[i, 'Id'].split('/')[0]
    #     for j in range(len(price_df)):
    #         if vendorCode == price_df.loc[j, 'Id']:
    #             price = price_df.loc[j, 'Price']
    #             valute = price_df.loc[j, 'Unit']
                
    #             # цена
    #             if valute != "RUB":
    #                 course = currencies['Valute'][valute]['Value']
    #             else:
    #                 course = 1
    #             price = round(price * ((100 - discount)/100) * float(course), 0)

    #             # Наличие
    #             availability_info = product_html.find("div", {"class": "ty-product-prices"}).find("div", {"class": "ty-wysiwyg-content"}).text
    #             print(availability_info)
    #             if float(df.loc[i, 'Price']) > 8000:
    #                 availability = "В наличии"
    #             else:
    #                 availability = "Нет в наличии"

                
    #             # description = f"{df.loc[i, 'Title']}\n{df.loc[i, 'Description']}\n{annex}"

    #             # запись
    #             old_count += 1
    #             # df.loc[i, 'Description'] = description
    #             df.loc[i, 'Availability'] = availability
    #             df.loc[i, 'Price'] = price
                
    #             break
        
    #     # DateEnd
    #     dateend = change_dateend(df.loc[i, 'Availability'], str(df.loc[i, 'AvitoStatus']), yesterday)
    #     df.loc[i, 'DateEnd'] = dateend
                
        
    # обработка перед финальным сохранением и сохранение
    df['DateEnd'] = pd.to_datetime(df.DateEnd).dt.strftime('%Y-%m-%d')
    df = df.drop_duplicates(subset=["Id"], keep='first')
    df.to_excel(f'{excel_file_name}.xlsx', sheet_name='Объявления', index=False)
    upload_file(f'{excel_file_name}.xlsx', f'/{excel_file_name}.xlsx', headers, replace=True)
    if check_new:
        check = 'ВКЛ.'
    else:
        check = 'ВЫКЛ.'

    return {'new': new_count, 'old': old_count-new_count, 'check': str(check), 'discount': discount, 'filename': excel_file_name}
    