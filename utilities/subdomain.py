import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup


def parse_page(url):
    for attempt in range(5):  # До 5 попыток для одной страницы
        try:
            response = requests.get(url)
            if response.status_code == 404:  # Проверка на несуществующую страницу
                return None
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            data = set()  # Используем множество для уникальных доменов
            rows = soup.select('table tbody tr')

            if not rows:  # Если на странице нет строк, возвращаем None
                return None

            for row in rows:
                columns = row.find_all('td')
                if len(columns) > 3 and columns[2].text.strip() == 'A':  # Проверка на тип записи 'A'
                    domain = columns[0].text.strip()  # Извлечение столбца 'Domain'
                    data.add(domain)  # Добавляем в множество

            time.sleep(random.choice([2, 3, 4, 5]))  # Случайная задержка между запросами
            
            if attempt > 0:
                print(f"Успешная загрузка {url} после {attempt}-й попытки.")
            return data

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print(f"Ошибка загрузки {url}. Пробуем еще раз... (Попытка {attempt + 1})")
                time.sleep(5)  # Фиксированная задержка перед повторной попыткой
            else:
                raise e


def parse_all_pages(base_url):
    all_domains = set()  # Используем множество для уникальных доменов
    page = 1  # Всегда начинаем с первой страницы
    keep_parsing = True

    empty_page_attempts = 0  # Счётчик пустых страниц
    recent_pages_data = []  # Список для хранения данных последних страниц

    while keep_parsing:
        print(f"Парсим страницу {page}")
        url = f"{base_url}?page={page}"

        try:
            result = parse_page(url)
            if result is None:  # Если страница пуста или не существует
                print(f"Страница {page} не существует или пуста. Проверяем еще раз...")
                empty_page_attempts += 1
                time.sleep(5)  # Ожидание перед повторной проверкой
                if empty_page_attempts >= 3:
                    print(f"Страница {page} пуста после 3 попыток. Остановка.")
                    keep_parsing = False
                    break
                else:
                    continue  # Переходим к следующей попытке
            else:
                empty_page_attempts = 0  # Обнуляем счётчик, если нашли данные
                all_domains.update(result)  # Добавляем новые домены в множество
                print(f"Разбор страницы {page} завершен.")

                # Добавляем данные страницы в список для сравнения
                recent_pages_data.append(result)
                if len(recent_pages_data) > 3:  # Храним данные только последних 3 страниц
                    recent_pages_data.pop(0)

                # Проверяем, повторяются ли данные на последних трёх страницах
                if len(recent_pages_data) == 3 and recent_pages_data[0] == recent_pages_data[1] == recent_pages_data[2]:
                    print(f"Данные на последних трёх страницах одинаковы. Остановка парсинга.")
                    keep_parsing = False
                    break

        except Exception as e:
            print(f"Ошибка парсинга страницы {page}: {e}")
            raise e

        page += 1  # Переход к следующей странице

    return all_domains


def get_subdomain_url():
    base_url = 'https://rapiddns.io/subdomain/{url}'
    url = input("Введите URL: ")
    full_url = base_url.format(url=url)
    return full_url  # Возвращаем полный URL


base_url = get_subdomain_url()  # Вызов функции для получения полного URL

domains = parse_all_pages(base_url)

# Запись результата в файл
with open('tmdb.txt', 'w') as file:
    for domain in sorted(domains):  # Сортируем домены перед записью
        file.write(f"{domain}\n")

print(f"Найдено {len(domains)} A записей. \nРезультаты сохранены в tmdb.txt.")
