"""Script to grab the "Yield farming" section of Sonar dashboard.

This script uses selenium and Chrome drivers, please make sure you have
ChromeDriver installed in your PATH.
(See https://selenium-python.readthedocs.io/installation.html#drivers)

The script waits for the Sonar dashboard to load. We can override the default
wait duration using command-line argument.
"""
import argparse
import dataclasses
import json
import logging
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from selenium import webdriver


_WAIT_FOR_SONAR_LOADING_SECONDS = 15


@dataclasses.dataclass
class DataTable:
    """Generic type for a table."""
    headers: Tuple[str]
    data_rows: Tuple[Dict[str, Any]]


@dataclasses.dataclass
class SonarDashboardSection:
    title: str
    data_table: Optional[DataTable] = None  # A section might not have a table.


def _get_sonar_dashboard_sections(
    selenium_driver: webdriver.chrome.webdriver.WebDriver,
    solana_address: str,
    wait_for_loading: float) -> List[SonarDashboardSection]:
    """Returns all Sonar dashboard sections.

    Args:
        selenium_driver: The selenium web driver.
        solana_address: The Solana address.
        wait_for_loading: Duration in seconds to wait for Sonar dashboard.
    """
    sonar_dashboard_url = f'https://sonar.watch/dashboard/{solana_address}'
    selenium_driver.get(sonar_dashboard_url)
    sections = selenium_driver.find_elements_by_class_name('mt-6')
    ret = []
    time.sleep(wait_for_loading)
    for section in sections:
        # Find the title and the data table
        title = section.find_element_by_class_name('text-h6').text
        logging.info('Parsing section: %s', title)
        try:
            # Note: We will take the first table only if there are multiple.
            table_element = section.find_element_by_tag_name('table')
        except:
            table_element = None
        if table_element is not None:
            data_table = _parse_data_table(table=table_element)
        else:
            data_table = None
        ret.append(SonarDashboardSection(title=title, data_table=data_table))
    return ret


def _parse_data_table(table: webdriver.remote.webelement.WebElement) -> DataTable:
    header_row = tuple(
        th.find_element_by_tag_name('span').text
        for th in table.find_elements_by_tag_name('th'))

    data_rows = []
    try:
        tbody = table.find_element_by_tag_name('tbody')
    except:
        # Note that we need this because some Sonar dashboard section
        # has <table> but without a <tbody>.
        tbody = None
    if tbody is None or tbody.find_elements_by_class_name('v-data-table__empty-wrapper'):
        data_rows = []  # There is no data in this table.
    else:
        for tr in tbody.find_elements_by_tag_name('tr'):
            tds = tr.find_elements_by_tag_name('td')
            td_values = [_get_td_raw_string_value(td) for td in tds]
            data_rows.append(td_values)

    # Transform data rows to dicts.
    data_rows = tuple(dict(zip(header_row, data_row)) for data_row in data_rows)
    return DataTable(headers=header_row, data_rows=data_rows)


def _get_td_raw_string_value(td_element):
    all_elements = [td_element, *td_element.find_elements()]
    return ' '.join(e.text for e in all_elements)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-a', '--address', help='The target Solana address.',
                        required=True)
    parser.add_argument('--wait', help='The duration in seconds for Sonar to load.',
                        type=float, default=_WAIT_FOR_SONAR_LOADING_SECONDS)
    parser.add_argument('--debug', help='Enable debug mode.', action='store_true')
    args = parser.parse_args()

    # Set up logging.
    logging_level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=logging_level)

    # Init web driver.
    try:
        options = webdriver.ChromeOptions()
        options.headless = False if args.debug else True
        driver = webdriver.Chrome(options=options)
    except:
        logging.exception('Cannot initialize selenium web driver.')
        sys.exit(1)

    # Find Sonar dashboard sections. (History, Wallet tokens, ...)
    # Our target is the "Yield farming" section.
    sections = _get_sonar_dashboard_sections(selenium_driver=driver,
                                             solana_address=args.address,
                                             wait_for_loading=args.wait)

    for section in sections:
        if section.title == 'Yield farming':
            print(json.dumps(section.data_table.data_rows, indent=2))


if __name__ == '__main__':
    main()
