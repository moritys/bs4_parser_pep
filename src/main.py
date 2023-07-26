import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from configs import configure_argument_parser, configure_logging

from collections import Counter

from constants import (
    BASE_DIR, MAIN_DOC_URL, MAIN_PEP_URL
)
from utils import get_response, find_tag, check_pep_status

from outputs import control_output

import requests_cache

from tqdm import tqdm

import logging


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    section_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(section_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)

        response = get_response(session, version_link)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version = text_match.group('version')
            status = text_match.group('status')
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})

    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_link = urljoin(downloads_url, pdf_a4_link)

    filename = archive_link.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = session.get(archive_link)

    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def status_search(session, url):
    """Поиск статуса на отдельной странице."""
    response = get_response(session, url)
    if response is None:
        return

    soup = BeautifulSoup(response.text,  features='lxml')

    info_block = find_tag(soup, 'dl', {'class': 'rfc2822 field-list simple'})
    all_dt_tags_in_info = info_block.find_all('dt')

    for dt in all_dt_tags_in_info:
        if dt.text == 'Status:':
            status = dt.find_next('dd')
            status_text_tag = status.find('abbr')
            return status_text_tag.text


def pep(session):
    response = get_response(session, MAIN_PEP_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    all_index_table = find_tag(
        soup, 'section', attrs={'id': 'index-by-category'}
    )

    count_pep = 0  # счетчик всех pep
    count_statuses = []  # хранение всех статусов
    results = [('Статус', 'Количество')]  # итоговая таблица

    separated_tables = all_index_table.find_all('tbody')
    for table in separated_tables:
        rows = table.find_all('tr')

        for row in tqdm(rows, desc='Считывание строк pep'):
            status_tag = row.find('td')
            preview_status = status_tag.text[1:]
            number_tag = status_tag.find_next('td')
            link_number_tag = number_tag.find('a')
            link_to_pep_page = link_number_tag['href']
            pep_url = urljoin(MAIN_PEP_URL, link_to_pep_page)
            page_status = status_search(session, pep_url)

            if preview_status:
                check_pep_status(link_to_pep_page, preview_status, page_status)

            count_pep += 1
            count_statuses.append(page_status)

    counter = Counter(count_statuses)  # подсчет каждого статуса
    for status in counter:
        results.append((status, counter[status]))

    results.append(('Total', count_pep))
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)

    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
