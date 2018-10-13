"""
<keywords>
test, python
</keywords>
<description>
'https://www.top500.org/lists/top500/'

pip install requests BeautifulSoup4
</description>
<seealso>
</seealso>
"""
import time
import os
import pickle
import logging
import datetime as dt

import requests
from bs4 import BeautifulSoup

top500_lists = 'https://www.top500.org'

logger = logging.getLogger("")
logger.setLevel(logging.INFO)


class MyFormatter(logging.Formatter):
    converter = dt.datetime.fromtimestamp
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            t_str = ct.strftime(datefmt)
        else:
            t_str = ct.strftime("%Y-%m-%d %H:%M:%S")
            t_str = "{},{:03d}".format(t_str, int(record.msecs))
        return t_str


console = logging.StreamHandler()
formatter = MyFormatter(
    fmt='%(asctime)s-%(name)s-%(levelname)-8s] - %(message)s',
)
console.setFormatter(formatter)
logger.addHandler(console)


def find_unique_top_500_lists(base_url):
    """

    :param base_url:
    :return:
    """
    logger.info('fetch all releases urls')
    response = requests.get(base_url + '/lists/top500')
    soup = BeautifulSoup(response.text, 'html.parser')

    # find all the lists that have an href of the format '/list/YYYY/MM'
    lists_boxes = soup.find_all(
        lambda tag: tag.has_attr('href')
        and '/lists/' in tag['href']
        and len(tag['href'].split('/')[2]) == 4
    )

    # keep the unique hrefs for the lists
    lists_dates = set()
    for list_date in lists_boxes:
        _list_date = list(
            filter(
                lambda x: x != '',
                list_date['href'].replace('/lists/', '').split('/')
            )
        )
        lists_dates.add('/'.join(_list_date))

    return sorted(lists_dates)


def find_entries_in_top_500_list(base_url, release_date):
    """

    :param release_date:
    :return:
    """
    logger.info(f'\tfetch info of release {release_date}')
    systems = {}
    for page in range(1, 6):
        page_url = f'{base_url}/list/{release_date}/?page={page}'
        systems_on_page = find_entries_in_top_500_list_page(base_url, page_url)
        systems.update(systems_on_page)

    return systems


def find_entries_in_top_500_list_page(base_url, page_url):
    """

    :return:
    """
    logger.info(f'\t\tfind systems on page {page_url}')
    response = requests.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # find all the unique systems on the page
    system_tags = soup.find_all(
        lambda tag: tag.has_attr('href')
        and tag['href'].startswith('/system')
    )

    systems_info = {}
    for system_index, system_tag in enumerate(system_tags):
        system_url = f"{base_url}{system_tag['href']}"
        system_rank, system_info = fetch_system_details(system_url)
        systems_info[system_rank] = system_info
        # if system_index == 1:
        #     break

    time.sleep(1.0)
    return systems_info


def fetch_system_details(system_url):
    """

    :return:
    """
    logger.info(f'\t\t\tfind system info {system_url}')
    response = requests.get(system_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # find the table rows with the system specs
    system_tags = soup.find_all(
        lambda _tag: _tag.name == 'tr'
        and _tag.findChild('th') is not None
        and _tag.findChild('td') is not None
    )

    # store the system specs into a dict
    system_info = {}
    for tag in system_tags:
        item = tag.find_all('th')[0].text.replace(':', '')
        value = tag.find_all('td')[0].text
        system_info[item] = value

    bottom_table = soup.find_all('tr', attrs={'class': 'sublist odd'})[0]
    system_rank = int(bottom_table.find_all('td')[1].text)

    return system_rank, system_info


available_lists = find_unique_top_500_lists(top500_lists)

with open(os.path.expanduser('~/tmp/top500.pkl'), 'wb') as fobj:

    all_releases_info = {}

    for list_release_date in list(reversed(available_lists)):

        list_release_info = find_entries_in_top_500_list(
            top500_lists,
            list_release_date
        )

        fname = os.path.expanduser(
            f"~/tmp/sandbox/top500_{list_release_date.replace('/', '_')}.pkl"
        )
        with open(fname, 'wb') as _fobj:
            pickle.dump(list_release_info, _fobj)
        logger.info(f'\tdump release info {fname}')

        all_releases_info[list_release_date] = list_release_info

    pickle.dump(all_releases_info, fobj)
    logger.info(f'dump release info {fname}')

print('done')
