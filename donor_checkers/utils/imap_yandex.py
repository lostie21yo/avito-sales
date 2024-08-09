from imbox import Imbox
import pandas as pd
from time import sleep
from datetime import *
from bs4 import BeautifulSoup as BS
from donor_checkers.utils.yandex_api import download_file
from donor_checkers.utils.yandex_api import upload_file


def imap_download(number, excel_file_name, password, headers):

    yesterday = (datetime.now() - timedelta(days=1)).date().strftime("%Y-%m-%d")
    with Imbox('imap.yandex.ru',
            username='ipkazakovivandmit@yandex.ru',
            password=password,
            ssl=True,
            ssl_context=None,
            starttls=False) as imbox:

        inbox_messages = imbox.messages(sent_from='autoload@avito.ru', date__on=datetime.strptime(yesterday, '%Y-%m-%d').date())
        isDownloaded = False
        for uid, message in inbox_messages[::-1]:
            message_html = message.body['plain'][0]
            bs = BS(message_html, 'html.parser')
            for link in bs.find_all('a'):
                url = link.get('href')
                df = None
                if 'download' in url and not isDownloaded:
                    df = pd.read_excel(url, sheet_name='Объявления')
                    contact_number = str(df.loc[0, 'ContactPhone'])
                    if contact_number == number:
                        isDownloaded = True
                        df.to_excel(f'{excel_file_name}.xlsx', sheet_name='Объявления', index=False)
                        upload_file(f'{excel_file_name}.xlsx', f'/{excel_file_name}.xlsx', headers, replace=True)
                        print(f'\nФайл {excel_file_name}.xlsx от {message.date} скачан из обратной выгрузки с почты')
                        break
            if isDownloaded:
                break
        else:
            # скачивание последних версий выгрузок с яндекс диска
            print(f'Файл {excel_file_name}.xlsx скачан с Яндекс диска')
            download_file(f'{excel_file_name}.xlsx', headers)