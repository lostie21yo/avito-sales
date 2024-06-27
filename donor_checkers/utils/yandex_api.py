import requests

def create_folder(path, headers):
    """Создание папки. \n path: Путь к создаваемой папке."""
    requests.put(f'https://cloud-api.yandex.net/v1/disk/resources?path={path}', headers=headers)

def upload_file(loadfile, savefile, headers, replace=False):
    """Загрузка файла.
    savefile: Путь к файлу на Диске
    loadfile: Путь к загружаемому файлу
    replace: true or false Замена файла на Диске"""
    res = requests.get(f'https://cloud-api.yandex.net/v1/disk/resources/upload?path={savefile}&overwrite={replace}', headers=headers).json()
    with open(loadfile, 'rb') as f:
        if res.get("href"):
            requests.put(res['href'], files={'file':f})
        else:
            print(res)

def get_new_link(filename, yandex_folder):
    filename = fr'{filename}'

    new_link = f'yandex_disk://{yandex_folder}/{filename}'

    return new_link

