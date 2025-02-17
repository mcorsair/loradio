import logging
from dataclasses import dataclass
from typing import Dict

import pyudev
from kivy.event import EventDispatcher


@dataclass(frozen=True)
class Device:
    vendor_id: int
    vendor: str
    model_id: int
    model: str
    device_node: str

    @staticmethod
    def from_dict(device: Dict):
        return Device(
            vendor_id=int(device.get('ID_VENDOR'), base=16),
            vendor=device.get('ID_VENDOR_FROM_DATABASE'),
            model_id=int(device.get('ID_MODEL_ID'), base=16),
            model=device.get('ID_MODEL_FROM_DATABASE'),
            device_node=device.get('DEVNAME'),
        )

    @property
    def hex_id(self):
        return f'{self.vendor_id:04x}:{self.model_id:04x}'


class DeviceMonitor(EventDispatcher):
    NAME = 'monitor'

    def __init__(
            self,
            vendor_id: int,
            model_id: int,
    ):
        super().__init__()
        self._logger = logging.getLogger(self.NAME)
        self._vendor_id = vendor_id
        self._model_id = model_id

        for s in ['on_attached', 'on_detached']:
            # noinspection PyUnresolvedReferences
            self.register_event_type(s)

        self._context = pyudev.Context()
        self._monitor = pyudev.Monitor.from_netlink(context=self._context)
        self._monitor.filter_by(
            subsystem='tty',
        )
        self._monitor_thread = pyudev.MonitorObserver(
            name=self.NAME,
            monitor=self._monitor,
            callback=self._monitor_callback,
        )

    def start(self):
        self._monitor_thread.start()

    def enum_devices(self):
        devices = self._context.list_devices(
            subsystem='tty',
            DEVTYPE='usb_device',
            ID_VENDOR=f'{self._vendor_id:04x}',
            ID_MODEL_ID=f'{self._model_id:04x}',
        )
        for dev in devices:
            device = Device.from_dict(dev)
            # noinspection PyUnresolvedReferences
            self.dispatch('on_attached', device)

    def on_attached(self, device: Device):
        self._logger.debug('attached: %s', device)

    def on_detached(self, device: Device):
        self._logger.debug('detached: %s', device)

    def _monitor_callback(self, dev: pyudev.Device):
        device = Device.from_dict(dev)
        if device.vendor_id == self._vendor_id and device.model_id == self._model_id:
            match dev.action:
                case 'add':
                    # noinspection PyUnresolvedReferences
                    self.dispatch('on_attached', device)
                case 'remove':
                    # noinspection PyUnresolvedReferences
                    self.dispatch('on_detached', device)
