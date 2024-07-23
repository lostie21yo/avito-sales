import json
import time as t
from datetime import *
# import sched
import schedule 
import requests

# my modules
from donor_checkers.utils.yandex_api import download_file
from donor_checkers.mkslift_checker import mkslift_check
from donor_checkers.ironmac_checker import ironmac_check
from donor_checkers.garopt_checker import garopt_check
from donor_checkers.wiederkraft_checker import wiederkraft_check
from donor_checkers.optimus_checker import optimus_check

# периодичность и время
first_launch_date = datetime.now().date()
check_new = True
start_time = "06:00"
retry_time_intervals = [300, 600, 900, 1500, 1800] + [3600]*21
periodic_save_delta = 15

# уведомление о первоначальном запуске
bot_token = "7227476930:AAHz9Aldcx4G2cTiyyZsEfkpyUirNeSffqY"
chat_id = "904798847"
message = f"Произведена инициализация бота {first_launch_date}. Проверка доноров ежедневно в {start_time}."
requests.get(f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}").json()
print(f'{message}')

# appendix = ' test'
appendix = ''
attempt = 0

def CheckUp():
    daily_report = {}
    try:
        # получение информации о валютах
        currencies = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
        attempt = 0

        # подгрузка настроек из json-файла
        with open('env.json', encoding='utf-8') as settings_file:
            settings = json.load(settings_file)

        accounts = settings['accounts']
        for account in accounts:
            data = account['data']
            yandex_token = data['yandex_token']
            annex = data['annex']
            excel_file_name = data['excel_file_name']
            # скачивание последних версий выгрузок с яндекс диска
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {yandex_token}'}
            # download_file(f'{excel_file_name}.xlsx', headers)
            for donor in data['donors']:
                # mkslift
                if donor['name'] == 'mkslift':
                    print(f"\n-=== Account name: {account['name']}, donor name: {donor['name']}, discount: {donor['discount']}, file: {excel_file_name} ===-")
                    daily_report['mkslift'] = mkslift_check(donor['link'], donor['discount'], donor['days_delta'], yandex_token, 
                                donor['yandex_image_folder_path'], annex, check_new, excel_file_name + appendix, currencies, periodic_save_delta)
                # ironmac
                if donor['name'] == 'ironmac':
                    print(f"\n-=== Account name: {account['name']}, donor name: {donor['name']}, discount: {donor['discount']}, file: {excel_file_name} ===-")
                    daily_report['ironmac'] = ironmac_check(donor['link'], donor['discount'], donor['days_delta'], yandex_token, 
                                donor['yandex_image_folder_path'], annex, check_new, excel_file_name + appendix, currencies, periodic_save_delta)
                # garopt1
                if donor['name'] == 'garopt1':
                    print(f"\n-=== Account name: {account['name']}, donor name: {donor['name']}, discount: {donor['discount']}, file: {excel_file_name} ===-")
                    daily_report['garopt1'] = garopt_check(donor['link'],  donor['discount'], donor['days_delta'], yandex_token, 
                            donor['yandex_image_folder_path'], annex, check_new, excel_file_name + appendix, currencies, periodic_save_delta)
                # garopt2
                if donor['name'] == 'garopt2':
                    print(f"\n-=== Account name: {account['name']}, donor name: {donor['name']}, discount: {donor['discount']}, file: {excel_file_name} ===-")
                    daily_report['garopt2'] = garopt_check(donor['link'],  donor['discount'], donor['days_delta'], yandex_token, 
                            donor['yandex_image_folder_path'], annex, check_new, excel_file_name + appendix, currencies, periodic_save_delta) 
                # garopt3
                if donor['name'] == 'garopt3':
                    print(f"\n-=== Account name: {account['name']}, donor name: {donor['name']}, discount: {donor['discount']}, file: {excel_file_name} ===-")
                    daily_report['garopt3'] = garopt_check(donor['link'],  donor['discount'], donor['days_delta'], yandex_token, 
                            donor['yandex_image_folder_path'], annex, check_new, excel_file_name + appendix, currencies, periodic_save_delta)
                # WiederKraft
                # if donor['name'] == 'wiederkraft':
                #     print(f"\n-=== Account name: {account['name']}, donor name: {donor['name']}, discount: {donor['discount']}, file: {excel_file_name} ===-")
                #     daily_report['wiederkraft'] = wiederkraft_check(donor['link'],  donor['discount'], donor['days_delta'], yandex_token, 
                #             donor['yandex_image_folder_path'], annex, check_new, excel_file_name + appendix, currencies, periodic_save_delta)
                # Optimus
                # if donor['name'] == 'optimus':
                #     print(f"\n-=== Account name: {account['name']}, donor name: {donor['name']}, discount: {donor['discount']}, file: {excel_file_name} ===-")
                #     daily_report['optimus'] = optimus_check(donor['link'],  donor['discount'], donor['days_delta'], yandex_token, 
                #             donor['yandex_image_folder_path'], annex, check_new, excel_file_name + appendix, currencies, periodic_save_delta)
                                
        message = f"\nУспешное обновление выгрузки!"              
        print(message)
        requests.get(f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}").json()

    except Exception as e:
        print(e)
        attempt += 1
        if attempt <= len(retry_time_intervals):
            t.sleep(retry_time_intervals[attempt-1])
            message = f'Попытка перезапуска №{attempt}'
            requests.get(f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}").json()
            print(f'Попытка перезапуска №{attempt}')
            CheckUp()
        else:
            attempt = 0
            print(f'Достигнуто максимальное количество попыток {len(retry_time_intervals)}. Отправлено уведомление. Попытки продолжаются...')
            message = f"Похоже какая-то херня с донором, интернет-то есть, глянь-ка!"
            requests.get(f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}").json()
            CheckUp()
    finally:
        print(f'Результаты:')
        for key in daily_report:
            # print(f'{key}: новые - {daily_report[key]['new']}, старые - {daily_report[key]['old']}')
            print(f'{key}: {daily_report[key]}')
        print(f"\nСледующая проверка завтра в {start_time}")

CheckUp()           
schedule.every().day.at(start_time).do(CheckUp) 
# schedule.every().minute.at(start_time).do(CheckUp) 

while True:
    schedule.run_pending()
    t.sleep(1)