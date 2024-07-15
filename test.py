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
            req = requests.get(link)
            product_page = BS(req.content, 'html.parser')
            pages = (link)
            try:
                pagination = product_page.find("ul", {"class": "page-numbers"})
                for a in pagination.find_all('a', href=True):
                    pages.add(a['href'])
            except:
                pass
            print(pages)

            # for page in pages:
            #     if page != '\n':
            #         print(page)

            print()
            # for page_number in range(page_count):
            #     link = f"{link}/page/{page_number}"
            #     print(link)
