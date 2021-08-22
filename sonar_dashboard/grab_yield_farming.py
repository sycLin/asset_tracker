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

import sonar_dashboard


_WAIT_FOR_SONAR_LOADING_SECONDS = 15


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-a', '--address', help='The target Solana address.',
                        required=True)
    parser.add_argument('--wait',
                        help='The duration in seconds for Sonar to load.',
                        type=float,
                        default=_WAIT_FOR_SONAR_LOADING_SECONDS)
    parser.add_argument('--debug',
                        help='Enable debug mode.',
                        action='store_true')
    args = parser.parse_args()

    # Set up logging.
    logger = logging.getLogger(name=__name__)
    logging_level = logging.DEBUG if args.debug else logging.WARNING
    logger.setLevel(logging_level)

    # Init web driver.
    try:
        options = webdriver.ChromeOptions()
        options.headless = False if args.debug else True
        driver = webdriver.Chrome(options=options)
    except:
        logger.exception('Cannot initialize selenium web driver.')
        sys.exit(1)

    # Find Sonar dashboard sections. (History, Wallet tokens, ...)
    # Our target is the "Yield farming" section.
    sections = sonar_dashboard.get_sonar_dashboard_sections(
        selenium_driver=driver,
        solana_address=args.address,
        wait_for_loading=args.wait)

    for section in sections:
        if section.title == 'Yield farming':
            print(json.dumps(section.data_table.data_rows, indent=2))


if __name__ == '__main__':
    main()
