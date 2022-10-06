import ftplib
import logging
import os
import socket
import time


FTP_LOGIN = 'free'
FTP_PASSWORD = 'free'
FTP_HOST = 'ftp.zakupki.gov.ru' #'77.246.101.195'
FTP_DIR = 'fcs_regions/Volgogradskaja_obl/notifications/'
FTP_SENDING_TIMEOUT = 90
LOG_DIR = 'logs'
LOCAL_DIR = 'files'


def ftpwalk(ftp, flist, depth=5, dirname='.'):
    """
    :param ftp: дескриптор открытого ftp-соединения.
    :param flist: итоговый список файлов.
    :param depth: глубина рекурсии, ограничение по уровню
    директорий относительно корня.
    :param dirname: текущая директория (необходима для формирования
    списка файлов относительно корня)
    """
    ftp_nlst = ftp_retry_until_success(ftp.nlst)
    for entry in (path for path in ftp_nlst if path not in ('.', '..')):
        try:
            if depth >= 0:
                ftp_retry_until_success(ftp.cwd, entry)
                ftpwalk(ftp, flist, depth - 1, dirname=f'{dirname}/{entry}')
                ftp_retry_until_success(ftp.cwd, '..')
            else:
                continue
        except ftplib.error_perm:
            flist.append(f'{dirname}/{entry}')


def ftp_retry_until_success(func, *args, **kwargs):
    """
    Вызывает функцию пока та не перестанет рейзить таймауты.

    При работе с FTP через плохую сеть или с проблемным сервером,
    FTP-команды периодически падают по таймауту. Данная функция
    вызывает переданную функцию с переданными аргументами до тех
    пор, пока она не отработает без таймаутов.

    :param func: функция (из ftplib, например FTP#retbinary).
    :param args: аргументы для func
    :param kwargs: аргументы для func
    :return: то же, что и func.
    """
    assert callable(func), 'First argument must be callable, %r given' % func

    # Пока пробуем 10 раз и выкидываем ошибку. В будущем можно изменить.
    attempts = 10
    while True:
        try:
            return func(*args, **kwargs)
        except socket.timeout as timeout_error:
            attempts -= 1
            logging.debug(timeout_error)
            if not attempts:
                raise


def get_connection():
    """
    Соединение с сервером
    """
    assert FTP_LOGIN and FTP_PASSWORD and FTP_HOST

    _ftp = ftplib.FTP(
        host=FTP_HOST,
        timeout=FTP_SENDING_TIMEOUT,
    )
    ftp_retry_until_success(_ftp.login, FTP_LOGIN, FTP_PASSWORD)

    logging.debug(f'Connect to server: {FTP_HOST}')
    logging.debug(_ftp.getwelcome())

    return _ftp


def is_same_size(ftp, local_file, remote_file):
    """
    Определите, равен ли размер удаленного файла локальному файлу
    Параметры:
    local_file: локальный файл
    remote_file: удаленный файл
    """
    try:
        remote_file_size = ftp.size(remote_file)
    except Exception as err:
        logging.debug(f'get remote file_size failed, Err: {err}')
        remote_file_size = -1

    try:
        local_file_size = os.path.getsize(local_file)
    except Exception as err:
        logging.debug(f'get local file_size failed, Err: {err}')
        local_file_size = -1

    return remote_file_size == local_file_size


def load_and_save_file(ftp, file_name):
    logging.debug(f'Load file - {file_name}')
    local_file_path = LOCAL_DIR.rstrip("/") + "/" + file_name.lstrip("./")
    if os.path.exists(local_file_path) and is_same_size(ftp, local_file_path, file_name):
        logging.debug('This file was uploaded earlier')
        return
    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
    handle = open(local_file_path, 'wb+')
    _msg = ftp_retry_until_success(
        ftp.retrbinary,
        "RETR %s" % file_name,
        handle.write,
    )
    logging.debug(_msg)


def log_activate():
    current_time = time.time()
    str_time = time.strftime('%Y%m%d', time.localtime(current_time))
    log_file_name = f'{LOG_DIR}/ftp_load_{str_time}.log'
    # Информация по настройке формата тут:
    # https://docs.python.org/3/library/logging.html#logrecord-attributes
    LOG_FORMAT = '%(asctime)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_PATH = os.path.join(os.getcwd(), log_file_name)
    logging.basicConfig(
        level=logging.DEBUG,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        filemode='a',  # перезаписать 'w'
        filename=LOG_PATH
    )


def main():
    log_activate()
    ftp = get_connection()
    logging.debug(f'Open directory {FTP_DIR}')
    _msg = ftp_retry_until_success(ftp.cwd, FTP_DIR)
    logging.debug(_msg)
    ftp_file_list = []
    ftpwalk(ftp, ftp_file_list, depth=1)
    for ftp_file in ftp_file_list:
        load_and_save_file(ftp, ftp_file)
    logging.debug('The script has finished working')


if __name__ == '__main__':
    main()
