from bs4 import BeautifulSoup as BS
import requests
import time
import re

# main_r = requests.get('https://wiederkraft.ru/shop')
# html = BS(main_r.content, 'html.parser')
for i in range(1):
    page = requests.get(f"https://wiederkraft.ru/shop/page/{i+1}/")
    time.sleep(1)
    html = BS(page.content, 'html.parser')
    for product in html.find("ul", {"class": "products"}).children:
        if product != '\n':
            # страница продукта
            product_page = requests.get(product.a['href'])
            time.sleep(1)
            product_html = BS(product_page.content, 'html.parser')
            
            # цена
            price = float(''.join(re.findall('\d+', product_html.find("bdi").text)))

            # артикул
            vendorCode = product_html.find("span", {"class": "sku"}).text

            # title
            title = product_html.find("h1", {"class": "product_title entry-title"}).text
            
            # получаем категории
            category = []
            for cat in product_html.find("nav", {"class": "woocommerce-breadcrumb"}).children:
                category.append(cat.string)
            category = ' | '.join(category[1:-1])

            # описание 
            

            # картинки


            print(title)
            print(vendorCode)
            print(price)
            print(category)


            # запись
            # new_count += 1
            # df.loc[new_index, 'Id'] = vendorCode
            # df.loc[new_index, 'Title'] = title
            # df.loc[new_index, 'Price'] = price
            # df.loc[new_index, 'Category'] = category
            # df.loc[new_index, 'Description'] = description
            # df.loc[new_index, 'ImageUrls'] = imageUrls
