from dataclasses import dataclass

from pycodec2 import Codec2

from codec.jobs import StopJob, PacketKind, SendJob, TaskRole
from codec.modes import VocoderMode
from processes.base_process import BaseProcess, BaseProcessStat
from processes.packet import encode_stream_start, encode_stream_frame, encode_stream_stop
from utils import timestamp_now


@dataclass
class EncoderProcessStat(BaseProcessStat):
    tx_packets: int


class EncoderProcess(BaseProcess):

    def _init(self):
        self._stat = EncoderProcessStat(
            role=self._role,
            tx_packets=0,
        )

    def _run(self):
        serial_queue = self._queues[TaskRole.SERIAL]
        encoder_queue = self._queues[TaskRole.ENCODER]

        buffer = bytearray()
        vocoder: Codec2 = None
        tx_test = False
        tx_mode: VocoderMode = None
        start_time: float = None
        chunks = 0
        packet_index = 0

        def send_stream_start():
            packet = encode_stream_start(
                test=tx_test,
                mode=tx_mode,
            )
            serial_queue.put(SendJob(
                kind=kind,
                data=packet,
            ))

        def send_stream_frame():
            nonlocal packet_index, chunks

            packet_index += 1
            packet = encode_stream_frame(
                test=tx_test,
                data=bytes(buffer),
                duration=timestamp_now() - start_time,
                packet_index=packet_index,
            )
            serial_queue.put(SendJob(
                kind=kind,
                data=packet,
            ))

            buffer.clear()
            chunks = 0

        def send_stream_stop():
            packet = encode_stream_stop(
                test=tx_test,
                duration=timestamp_now() - start_time,
            )
            serial_queue.put(SendJob(
                kind=kind,
                data=packet,
            ))

        while True:
            job = encoder_queue.get(block=True)
            if isinstance(job, StopJob):
                break

            kind = PacketKind.from_job(job)
            match kind:

                case PacketKind.STREAM_START:
                    tx_mode = job.mode
                    tx_test = job.test
                    vocoder = Codec2(tx_mode.rate)
                    packet_index = 0
                    start_time = timestamp_now()

                    send_stream_start()
                    self._stat.tx_packets += 1

                case PacketKind.STREAM_FRAME:

                    if vocoder is None or tx_mode is None or start_time is None:
                        self._logger.warning('mode not defined')
                    else:
                        encoded: bytes = vocoder.encode(job.frame)
                        buffer.extend(encoded)
                        chunks += 1
                        if chunks >= self._config.vocoder.chunks:
                            send_stream_frame()
                            self._stat.tx_packets += 1

                case PacketKind.STREAM_STOP:

                    if len(buffer):
                        send_stream_frame()
                        self._stat.tx_packets += 1

                    send_stream_stop()
                    self._stat.tx_packets += 1

            self._send_stat()
