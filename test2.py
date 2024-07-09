from bs4 import BeautifulSoup as BS
import requests
import time
import re
import tqdm

# main_r = requests.get('https://wiederkraft.ru/shop')
# html = BS(main_r.content, 'html.parser')
for i in tqdm.trange(140):
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
            price = float(''.join(re.findall(r'\d+', product_html.find("bdi").text)))

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
            description = []
            page_description = product_html.find("div", {"id": "tab-description"}).stripped_strings
            for string in page_description:
                description.append(string)

            additional_info = product_html.find("div", {"id": "tab-additional_information"}).table.children
            for line in additional_info:
                string = line.get_text().strip().replace("\n", " ")
                description.append(string)

            description = '\n'.join(description).replace("\n\n", "\n")

            # картинки
            image_links = []
            images = product_html.find("figure", {"class": "woocommerce-product-gallery__wrapper swiper-wrapper"}).find_all("div")
            for div in images:
                image_links.append(div.a["href"])
            
            origURL = image_links[0]
            filename = origURL.split('/')[-1]
            resized_img = format_image(origURL)
            cv2.imwrite(filename, resized_img)
            upload_file(filename, f'{yandex_image_folder_path}/{filename}', headers, True)
            os.remove(filename)
            new_URL = get_new_link(filename, yandex_image_folder_path)
            imageUrls.append(new_URL) # главная картинка в формате 4:3

            print(title)
            print(vendorCode)
            print(price)
            print(category)
            print(description)
            print(image_links)
            print('=============================')

            # запись
            # new_count += 1
            # df.loc[new_index, 'Id'] = vendorCode
            # df.loc[new_index, 'Title'] = title
            # df.loc[new_index, 'Price'] = price
            # df.loc[new_index, 'Category'] = category
            # df.loc[new_index, 'Description'] = description
            # df.loc[new_index, 'ImageUrls'] = imageUrls
