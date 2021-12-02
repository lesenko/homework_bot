import logging
import os
import sys
import time

import requests
from requests.exceptions import HTTPError
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
)
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

def send_message(bot, message):
    """Функция для отправки сообщений."""
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f'Удачная отправка сообщения: {logging.info}')
    except Exception as error:
        logger.error(f'Сбой при отправке сообщения: {error}')

def get_api_answer(current_timestamp):
    """Делаем запрос к API Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        api_answer = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )      
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')
    if api_answer.status_code != 200:
        logger.error('Ошибка статуса страницы.')
        raise Exception 
    return api_answer.json()

def check_response(response):
    """Проверяем ответ API на корректность."""
    if not isinstance(response, dict):
        logger.error('В ответе не словарь.')
        raise TypeError ('В ответе не словарь.')
    if len(response) == 0:
        logger.error('Словарь пустой.')
        raise IndexError ('Словарь пустой.')
    if 'homeworks' not in response.keys():
        logger.error('В словаре нет ключа homeworks.')
        raise KeyError ('В словаре нет ключа homeworks.')
    if not isinstance(response.get('homeworks'), list):
        logger.error('Домашние работы указаны не в виде списка.')
        raise TypeError ('Домашние работы указаны не в виде списка.')
    return response.get('homeworks')

def parse_status(homework):
    """Получаем статус домашней работы."""
    try:
        homework_name = homework.get('homework_name')
    except KeyError as error:
        logger.error(f'Не найден ключ homework_name: {error}')
    try:
        homework_status = homework.get('status')
    except KeyError as error:
        logger.error(f'Не найден ключ homework_status: {error}')
    if homework_status not in HOMEWORK_STATUSES:
        logger.error('Такого статуса нет в словаре.')
        raise KeyError('Такого статуса нет в словаре.')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'

def check_tokens():
    """Проверяем доступность переменных окружения."""
    try:
        if PRACTICUM_TOKEN or TELEGRAM_TOKEN or TELEGRAM_CHAT_ID:
            return True
        else:
            return False
    except KeyError:
        logger.critical(f'Отсутствуют переменные окружения: {KeyError}.')

def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework_dict = check_response(response)
            if len(homework_dict) > 0:
                homework = check_response(response)[0]
                message = parse_status(homework)
                send_message(bot, message)
            else:
                logger.debug('Работу пока не проверили.')
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}.'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            break


if __name__ == '__main__':
    main()
