[![Python 3.7-3.10](https://img.shields.io/badge/Python-3.7--3.10-green)](https://www.python.org/downloads/)
# Скрипт для загрузки с FTP сервера 
## на примере ftp.zakupki.gov.ru
* Логирование 
* Загрузка новых файлов
* Обработка разрывов соединения

#### Установка:
```shell
git clone https://github.com/anra-dev/eis_ftp_loader.git
mkdir files
mkdir logs
python3 -m venv venv

```
#### Задать константы:
```python
FTP_LOGIN = 'free'
FTP_PASSWORD = 'free'
FTP_HOST = 'ftp.zakupki.gov.ru'
FTP_DIR = 'fcs_regions/Volgogradskaja_obl/notifications/'
```
#### Запуск:
```shell
source venv/bin/activate
python main.py
```