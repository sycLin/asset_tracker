"""Sends yield farming results to Telegram."""

import argparse
import logging
import sys
import textwrap
from typing import Any, Dict

from selenium import webdriver
import telegram

import sonar_dashboard


_WAIT_FOR_SONAR_LOADING_SECONDS = 20.0


def _format_data_row(data_row: Dict[str, Any]) -> str:
    return textwrap.dedent(f"""\
        {data_row['Asset']} ({data_row['Platform']})
        - APR: {data_row['APR']}
        - Pending: {data_row['Pending']}
        - Value: {data_row['Value']}""")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-a',
                        '--address',
                        required=True,
                        help='The Solana address.')
    parser.add_argument('-c',
                        '--telegram_chat_id',
                        required=True,
                        help='The telegram chat to send message to.')
    parser.add_argument('-t',
                        '--telegram_bot_token',
                        required=True,
                        help='The telegram bot token to send notification.')
    parser.add_argument('--wait',
                        help='The duration in seconds for Sonar to load.',
                        type=float,
                        default=_WAIT_FOR_SONAR_LOADING_SECONDS)
    parser.add_argument('--debug',
                        action='store_true',
                        help='To enable debug mode.')
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
            telegram_message = '🧑‍🌾 🧑‍🌾 🧑‍🌾 Yield Farmer 🧑‍🌾 🧑‍🌾 🧑‍🌾\n\n'
            telegram_message += '\n\n'.join(
                _format_data_row(row) for row in section.data_table.data_rows)
            telegram_message += f'\n\nhttps://sonar.watch/dashboard/{args.address}'
            bot = telegram.Bot(token=args.telegram_bot_token)
            bot.send_message(text=telegram_message,
                             chat_id=args.telegram_chat_id,
                             disable_web_page_preview=True)


if __name__ == '__main__':
    main()
