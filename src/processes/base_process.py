import logging
from dataclasses import dataclass
from multiprocessing import Queue

from codec.jobs import StopJob, TaskRole
from config import Config


@dataclass
class BaseProcessStat:
    role: TaskRole


class BaseProcess:
    def __init__(
            self,
            config: Config,
            role: TaskRole,
            device_node: str,
            stat_queue: Queue,
            queues: dict[TaskRole, Queue],
    ):
        self._logger = logging.getLogger(role.value)
        self._config = config
        self._role = role
        self._device_node = device_node
        self._stat_queue = stat_queue
        self._queues = queues

        self._stat: BaseProcessStat = None

        self._init()

    def _send_stat(self):
        if self._stat:
            self._stat_queue.put(self._stat)

    def run(self):
        self._logger.info('started')
        try:
            self._run()
        except KeyboardInterrupt:
            self._logger.info('interrupted')
        except Exception as ex:
            self._logger.exception('ERROR: %s', ex)
        finally:
            self._logger.info('finished')
            for queue in self._queues.values():
                queue.put(StopJob())

    def _init(self):
        pass

    def _run(self):
        pass
