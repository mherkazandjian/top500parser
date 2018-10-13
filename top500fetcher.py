#!/usr/bin/env python
# coding=utf-8
"""
<keywords>
top, 500, hpc, list, web, scrapping
</keywords>
<description>
Script that scrapps the top500 list HPC website

The system specs of each system is fetched for all the releases dating
back to 1993 (as of the time of writing this script)

.. see-also: https://www.top500.org

</description>
<seealso>
</seealso>
"""
import time
import pickle
import logging
import datetime as dt

import requests
from bs4 import BeautifulSoup


class MyFormatter(logging.Formatter):
    """
    Custom formatter for stdout
    """
    converter = dt.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        """
        Custom time formatter

        :param record: a record
        :param datefmt: the date time format
        :return:
        """
        ct = self.converter(record.created)
        if datefmt:
            t_str = ct.strftime(datefmt)
        else:
            t_str = ct.strftime("%Y-%m-%d %H:%M:%S")
            t_str = "{},{:03d}".format(t_str, int(record.msecs))
        return t_str


class Fetcher(object):
    """
    Fetch the raw systems data of the top 500 list of HPC systems
    """
    def __init__(self, base_url: str='https://www.top500.org'):
        """
        Constructor

        :param base_url: the url of the top500 list
        """
        self.base_url = base_url
        """the url of the top500 list"""

        self.available_releases = None
        """The list of available releases"""

        self.all_releases_data = None
        """Dict that holds the data of all the releases"""

        self.log = None
        """An instance of the logging object"""

        self._setup_logger()

    def _setup_logger(self):
        """
        Configure the logger
        """
        console = logging.StreamHandler()
        formatter = MyFormatter(
            fmt='%(asctime)s-%(name)s-%(levelname)-8s] - %(message)s',
        )
        console.setFormatter(formatter)

        logger = logging.getLogger("")
        logger.setLevel(logging.INFO)
        logger.addHandler(console)
        self.log = logger

    @staticmethod
    def _url_as_soup(url: str) -> BeautifulSoup:
        """
        Return the parsed html soup
        :param url: the url to be downlaoded and parsed
        :return: An instance of a beautiful soup parsed object
        """
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup

    def query_available_releases(self):
        """
        Find the list of all the released lists in the format YYYY/MM
        :return: list of strings
        """
        self.log.info('fetch all releases urls')
        soup = self._url_as_soup(self.base_url + '/lists/top500')

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

        self.available_releases = list(reversed(sorted(lists_dates)))

    def find_entries_in_top_500_list(self, release_date: str) -> dict:
        """
        Fetch the systems in a particular release

        For example, a certain release date 2001/06 is used along with the base
        url https://www.top500.org to fetch the list of system in that release.
        Since it is a top500 list, the returned dict contains the info of 500
        systems.

        :param release_date: the release date e.g 2001/06
        :return: the info of all the systems of the specified release
        """
        self.log.info(f'\tfetch info of release {release_date}')
        systems = {}
        for page in range(1, 6):
            page_url = f'{self.base_url}/list/{release_date}/?page={page}'
            systems_on_page = self.find_entries_in_top_500_list_page(page_url)
            systems.update(systems_on_page)

        return systems

    def find_entries_in_top_500_list_page(self, page_url: str) -> dict:
        """
        Return the info of the systems of a particlular page

        :param page_url: the url of the a page of a certain release
        :return: dict of systems info that are on the page_url
        """
        self.log.info(f'\t\tfind systems on page {page_url}')
        soup = self._url_as_soup(page_url)

        # find all the unique systems on the page
        system_tags = soup.find_all(
            lambda tag: tag.has_attr('href')
            and tag['href'].startswith('/system')
        )

        systems_info = {}
        for system_index, system_tag in enumerate(system_tags):
            system_url = f"{self.base_url}{system_tag['href']}"
            system_rank, system_info = self.fetch_system_details(system_url)
            systems_info[system_rank] = system_info
            # DEBUG
            # if system_index == 1:
            #     break
            # time.sleep(1.0)

        return systems_info

    def fetch_system_details(self, system_url: str) -> tuple:
        """
        Fetch the system info from the system url

        :return: dict
        """
        self.log.info(f'\t\t\tfind system info {system_url}')
        soup = self._url_as_soup(system_url)

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

    def download_all_releases_data(self):
        """
        Use the content of self.available_releases to download all their data
        :return: data of all the releases as a dict
        """
        all_releases_info = {}

        for list_release_date in self.available_releases:
            list_release_info = self.find_entries_in_top_500_list(
                list_release_date
            )

            # DEBUG: save the individial releases
            # fname = f"top500_{list_release_date.replace('/', '_')}.pkl"
            # with open(fname, 'wb') as _fobj:
            #     pickle.dump(list_release_info, _fobj)
            # self.log.info(f'\tdump release info {_fobj.name}')

            all_releases_info[list_release_date] = list_release_info

    def save(self):
        """
        Dump the content of self.all_releases_data into a pickle
        """
        with open('top500.pkl', 'wb') as fobj:
            pickle.dump(self.all_releases_data, fobj)
        self.log.info(f'dump release info {fobj.name}')


def main():
    """
    The main function executed upon entry
    """
    fetcher = Fetcher()
    fetcher.query_available_releases()
    fetcher.download_all_releases_data()
    fetcher.save()


if __name__ == '__main__':
    main()
