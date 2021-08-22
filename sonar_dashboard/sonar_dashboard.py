"""Module for Sonar Dashboard parsing.

This module provides the "get_sonar_dashboard_sections" function that will
return all sections of the Sonar Dashboard.
"""
import dataclasses
import time
from typing import Any, Dict, List, Optional, Tuple

from selenium import webdriver


@dataclasses.dataclass
class DataTable:
    """Generic type for a table."""
    headers: Tuple[str]
    data_rows: Tuple[Dict[str, Any]]


@dataclasses.dataclass
class SonarDashboardSection:
    title: str
    data_table: Optional[DataTable] = None  # A section might not have a table.


def get_sonar_dashboard_sections(
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
