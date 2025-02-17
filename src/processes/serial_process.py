import time
from dataclasses import dataclass

from serial import Serial

from codec.jobs import RecvJob, StopJob, SendJob, PacketKind, TaskRole
from processes.base_process import BaseProcess, BaseProcessStat
from utils import queue_get_non_blocking, timestamp_now


@dataclass
class SerialProcessStat(BaseProcessStat):
    rx_total: int
    tx_total: int
    tx_duration: float | None
    tx_current: int | None
    tx_speed: float | None


class SerialProcess(BaseProcess):
    DELAY = 0.01

    def _init(self):
        self._stat = SerialProcessStat(
            role=self._role,
            rx_total=0,
            tx_total=0,
            tx_duration=None,
            tx_current=None,
            tx_speed=None,
        )

    def _run(self):
        serial_queue = self._queues[TaskRole.SERIAL]
        decoder_queue = self._queues[TaskRole.DECODER]

        tx_start_time = None

        with Serial(port=self._device_node) as ser:
            while True:
                time.sleep(self.DELAY)

                while n := ser.in_waiting:
                    received = ser.read(n)
                    # self._logger.debug('got {blue}%d{reset} bytes', n)
                    job = RecvJob(
                        data=received,
                    )
                    decoder_queue.put(job)

                    self._stat.rx_total += len(received)
                    self._send_stat()

                if job := queue_get_non_blocking(serial_queue):
                    if isinstance(job, StopJob):
                        break

                    if isinstance(job, SendJob):
                        match job.kind:
                            case PacketKind.STREAM_START:
                                tx_start_time = timestamp_now()
                                self._stat.tx_current = 0
                            case PacketKind.STREAM_FRAME:
                                pass
                            case PacketKind.STREAM_STOP:
                                pass

                        # self._logger.debug('sending {blue}%d{reset} bytes', len(job.data))
                        ser.write(job.data)

                        self._stat.tx_duration = timestamp_now() - tx_start_time
                        self._stat.tx_total += len(job.data)
                        self._stat.tx_current += len(job.data)
                        self._stat.tx_speed = self._stat.tx_current / self._stat.tx_duration
                        self._send_stat()
