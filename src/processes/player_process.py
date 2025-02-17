from threading import Lock

import numpy as np
import pyaudio

from codec.jobs import StopJob, PlayJob, TaskRole
from processes.base_process import BaseProcess
from utils import ignore_stderr


class PlayerProcess(BaseProcess):

    def _run(self):
        player_queue = self._queues[TaskRole.PLAYER]

        samples: np.ndarray = np.array([], dtype=np.int16)
        lock = Lock()

        def stream_callback(_in_data, frame_count, _time_info, _status):
            nonlocal samples

            with lock:
                frame, samples = samples[:frame_count], samples[frame_count:]

            # underflow padding
            if (frame_len := len(frame)) != frame_count:
                frame = np.pad(frame, (0, frame_count - frame_len), 'constant', constant_values=0)

            return frame, pyaudio.paContinue

        with ignore_stderr():
            audio = pyaudio.PyAudio()
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self._config.vocoder.sound_rate,
                output=True,
                stream_callback=stream_callback,
                frames_per_buffer=self._config.vocoder.frames_per_buffer,
            )
            try:
                while stream.is_active():
                    job = player_queue.get(block=True)
                    if isinstance(job, StopJob):
                        stream.stop_stream()
                        break

                    if isinstance(job, PlayJob):
                        with lock:
                            samples = np.concatenate([samples, job.samples])
            finally:
                stream.close()
        finally:
            audio.terminate()
