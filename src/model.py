import logging
from multiprocessing import Process, Queue
from typing import Type

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, BooleanProperty

from codec.jobs import StopJob, StreamStartJob, StreamStopJob, TaskRole
from codec.modes import VocoderMode
from config import Config
from monitor import Device, DeviceMonitor
from processes.base_process import BaseProcess, BaseProcessStat
from processes.decoder_process import DecoderProcess
from processes.encoder_process import EncoderProcess
from processes.player_process import PlayerProcess
from processes.recorder_process import RecorderProcess
from processes.serial_process import SerialProcess


class Model(EventDispatcher):
    NAME = 'model'

    device: Device = ObjectProperty(allownone=True)
    active: bool = BooleanProperty(False)
    streaming: bool = BooleanProperty(False)
    test: bool = BooleanProperty(None, allownone=True)

    def __init__(
            self,
            config: Config,
            monitor: DeviceMonitor,
            device_node: str,
    ):
        super().__init__()
        self._logger = logging.getLogger(self.NAME)
        self._config = config
        self._monitor = monitor
        self._device_node = device_node

        self._stat_queue = Queue()
        self._queues: dict[TaskRole, Queue] = {}

        self._monitor.bind(
            on_attached=self._on_device_attached,
            on_detached=self._on_device_detached,
        )

    def _on_device_attached(self, _, device: Device):
        if device.device_node == self._device_node:
            self.device = device

    def _on_device_detached(self, _, device: Device):
        if device.device_node == self._device_node:
            self.stop()
            self.device = None

    def start(self):
        if self.active:
            self._logger.warning('already running')
            return
        self._logger.debug('start {blue}%s{reset}', self.device.device_node)

        self._queues = {role: Queue() for role in TaskRole}

        targets = [
            (
                TaskRole.SERIAL,
                SerialProcess,
            ),
            (
                TaskRole.ENCODER,
                EncoderProcess,
            ),
            (
                TaskRole.DECODER,
                DecoderProcess,
            ),
            (
                TaskRole.PLAYER,
                PlayerProcess,
            ),
            (
                TaskRole.RECORDER,
                RecorderProcess,
            ),
        ]
        for role, cls in reversed(targets):
            process = Process(
                target=self._process_wrapper,
                kwargs=dict(
                    cls=cls,
                    config=self._config,
                    role=role,
                    device_node=self._device_node,
                    stat_queue=self._stat_queue,
                    queues=self._queues,
                )
            )
            process.start()

        self.active = True

    def stop(self):
        if not self.active:
            self._logger.warning('not running')
            return
        self._logger.debug('stop')

        self._send_queue_stop()

        self.active = False

    @staticmethod
    def _process_wrapper(
            cls: Type[BaseProcess],
            config: Config,
            role: TaskRole,
            device_node: str,
            stat_queue: Queue,
            queues: dict[TaskRole, Queue],
    ):
        p = cls(
            config=config,
            role=role,
            device_node=device_node,
            stat_queue=stat_queue,
            queues=queues,
        )
        p.run()

    def _send_queue_stop(self):
        for queue in self._queues.values():
            queue.put(StopJob())

    def stream_start(
            self,
            mode: VocoderMode,
            test: bool,
    ):
        self._logger.info('start stream %s, test: %s', mode.name, 'true' if test else 'false')
        self.streaming = True
        self.test = test
        job = StreamStartJob(
            mode=mode,
            test=test,
        )
        for role in [TaskRole.ENCODER, TaskRole.RECORDER]:
            queue = self._queues[role]
            queue.put(job)

    def stream_stop(self):
        self.streaming = False
        self.test = None
        job = StreamStopJob()
        for role in [TaskRole.RECORDER, TaskRole.ENCODER]:
            queue = self._queues[role]
            queue.put(job)

    def get_stats(self) -> dict[TaskRole, BaseProcessStat]:
        stats: dict[TaskRole, BaseProcessStat] = {}

        # --- get last stats ---

        while not self._stat_queue.empty():
            stat:  BaseProcessStat = self._stat_queue.get(block=False)
            stats[stat.role] = stat
        return stats
