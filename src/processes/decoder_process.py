from dataclasses import dataclass

import numpy as np
from pycodec2 import Codec2

from codec.audio import generate_tone
from codec.jobs import StopJob, RecvJob, PacketKind, PlayJob, TaskRole
from codec.modes import VocoderMode
from processes.base_process import BaseProcess, BaseProcessStat
from processes.packet import decode_payload, MAGIC_WORD
from utils import timestamp_now


@dataclass
class DecoderProcessStat(BaseProcessStat):
    rx_packets: int
    rx_duration: float
    rx_mode: VocoderMode | None
    rx_current: int | None
    rx_speed: int | None
    rx_delay: float | None
    rx_lost: int | None


class DecoderProcess(BaseProcess):

    def _init(self):
        self._buffer = bytearray()

        self._stat = DecoderProcessStat(
            role=self._role,
            rx_packets=0,
            rx_duration=0,
            rx_mode=None,
            rx_current=None,
            rx_speed=None,
            rx_delay=None,
            rx_lost=None,
        )

        sound_rate = self._config.vocoder.sound_rate
        self._stream_start_tone = generate_tone(
            sr=sound_rate,
            freq=440 * 2,
            duration=0.1,
            amplitude=0.3,
        )
        self._stream_stop_tone = generate_tone(
            sr=sound_rate,
            freq=440,
            duration=0.1,
            amplitude=0.2,
        )
        self._stream_test_tone = generate_tone(
            sr=sound_rate,
            freq=660,
            duration=0.1,
            amplitude=0.1,
        )
        self._stream_error_tone = generate_tone(
            sr=sound_rate,
            freq=440 * 4,
            duration=0.1,
            amplitude=0.1,
        )

    def _yield_blocks(self):
        while True:

            # --- header ---

            index = self._buffer.find(MAGIC_WORD)
            if index < 0:
                # no packet header
                break
            index += len(MAGIC_WORD)

            # --- payload size ---

            if index + 2 > len(self._buffer):
                # no enough for payload size
                break
            payload_size = self._buffer[index]
            index += 1

            # --- payload ---

            if index + payload_size > len(self._buffer):
                # no enough for payload
                break
            payload = self._buffer[index: index + payload_size]
            index += payload_size

            self._buffer = self._buffer[index:]
            yield decode_payload(bytes(payload))

    def _run(self):
        decoder_queue = self._queues[TaskRole.DECODER]
        player_queue = self._queues[TaskRole.PLAYER]

        vocoder: Codec2 = None
        last_index: int = None
        start_time: float = None

        while True:
            job = decoder_queue.get(block=True)
            if isinstance(job, StopJob):
                break

            if isinstance(job, RecvJob):
                self._buffer.extend(job.data)
                for kind, test, payload in self._yield_blocks():
                    self._stat.rx_packets += 1

                    match kind:
                        case PacketKind.STREAM_START:
                            (self._stat.rx_mode,) = payload
                            self._stat.rx_duration = 0
                            self._stat.rx_lost = 0
                            self._stat.rx_current = 0
                            vocoder = Codec2(self._stat.rx_mode.rate)
                            self._logger.info('vocoder: {blue}%s{reset} bps', self._stat.rx_mode.rate)
                            last_index = 0
                            start_time = timestamp_now()

                            samples = self._stream_start_tone

                        case PacketKind.STREAM_FRAME:
                            block, duration, packet_index = payload
                            self._stat.rx_duration = timestamp_now() - start_time
                            if test:
                                self._stat.rx_delay = self._stat.rx_duration - duration
                                if last_index is not None and packet_index != last_index + 1:
                                    delta = packet_index - last_index + 1
                                    if 0 < delta <= 10:
                                        self._stat.rx_lost = self._stat.rx_lost + delta
                                last_index = packet_index

                                samples = self._stream_test_tone
                            else:
                                frames = []
                                while len(block):
                                    chunk, block = block[:self._stat.rx_mode.encoded_len], block[self._stat.rx_mode.encoded_len:]
                                    frame: np.ndarray = vocoder.decode(chunk)
                                    frames.append(frame)

                                samples = np.concatenate(frames)

                        case PacketKind.STREAM_STOP:
                            duration, = payload
                            self._stat.rx_duration = timestamp_now() - start_time
                            if test:
                                self._stat.rx_delay = self._stat.rx_duration - duration
                            else:
                                pass

                            samples = self._stream_stop_tone

                        case _:
                            raise NotImplementedError()

                    player_queue.put(PlayJob(
                        samples=samples,
                    ))

                self._stat.rx_current += len(job.data)
                self._stat.rx_speed = self._stat.rx_current / self._stat.rx_duration if self._stat.rx_duration else None
                self._send_stat()
