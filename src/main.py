#!/usr/bin/env python

import argparse
import logging
import logging.config
import os
import sys
from pathlib import Path

from kivy.core.window import Window
from kivy.metrics import Metrics

from config import load_config
from monitor import DeviceMonitor
from model import Model
from utils import load_yaml

DEVICE_VENDOR_ID = 0x1a86
DEVICE_MODEL_ID = 0x7523


def parse_args():
    parser = argparse.ArgumentParser(
        prog='LoRaDio',
        description='LoRa Radio',
    )
    parser.add_argument(
        '-d', '--device',
        dest='device',
        help='USB device',
        default='/dev/ttyUSB0',
    )
    parser.add_argument(
        '--start',
        action='store_true',
        dest='start',
        help='auto start',
        default=False,
    )
    args = parser.parse_args()
    return args


def init_logging(filename):
    cfg = load_yaml(filename)
    logging.config.dictConfig(cfg)
    logging.info('log config: {blue}%s{reset}', filename)


def main():

    # --- init dirs ---

    cur_dir = Path(sys.argv[0]).resolve().parent
    os.chdir(cur_dir)
    root_dir = cur_dir.parent
    config_dir = root_dir / 'config'

    # --- init logging ---

    init_logging(
        filename=config_dir / 'log.yml',
    )

    # --- args ---

    args = parse_args()

    # --- load config ---

    config = load_config(
        filename=config_dir / 'config.yml',
    )

    # --- apply font_scale ---

    font_scale = config.app.font_scale
    logging.info('using font_scale {blue}%.2f{reset}', font_scale)
    Metrics.fontscale = font_scale

    # --- app icon ---

    filename = cur_dir / 'app_icon.png'
    Window.icon = str(filename)

    # --- monitor ---

    monitor = DeviceMonitor(
        vendor_id=DEVICE_VENDOR_ID,
        model_id=DEVICE_MODEL_ID,
    )

    # --- model ---

    model = Model(
        config=config,
        monitor=monitor,
        device_node=args.device,
    )

    # --- app ---

    from app import MainApp
    app = MainApp(
        config=config,
        monitor=monitor,
        model=model,
        device_node=args.device,
    )
    app.run()


if __name__ == '__main__':
    main()
