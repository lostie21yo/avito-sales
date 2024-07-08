from bs4 import BeautifulSoup as BS
import requests

main_r = requests.get('https://wiederkraft.ru/')
html = BS(main_r.content, 'html.parser')

for cat in html.find("ul", {"id": "secondary_menu"}).children:
    if cat != '\n':
        category = cat.contents[0].text
        print(f'========== {category} ==========')
        for subcat in cat.ul.find_all('li'):
            subcategory = subcat.text
            link = subcat.a['href']
            print(f"{subcategory} - {link}")

