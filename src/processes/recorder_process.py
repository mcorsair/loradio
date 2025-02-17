import numpy as np
import pyaudio

from codec.jobs import StopJob, TaskRole, StreamFrameJob, StreamStartJob, StreamStopJob
from processes.base_process import BaseProcess
from utils import ignore_stderr


class RecorderProcess(BaseProcess):

    def _run(self):
        encoder_queue = self._queues[TaskRole.ENCODER]
        recorder_queue = self._queues[TaskRole.RECORDER]

        def stream_callback(in_data, _frame_count, _time_info, _status):
            frame: np.ndarray = np.frombuffer(in_data, dtype=np.int16)

            encoder_queue.put(StreamFrameJob(
                frame=frame,
            ))

            return frame, pyaudio.paContinue

        while True:
            job = recorder_queue.get(block=True)
            if isinstance(job, StopJob):
                break

            if isinstance(job, StreamStartJob):
                with ignore_stderr():
                    audio = pyaudio.PyAudio()
                try:
                    stream = audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=self._config.vocoder.sound_rate,
                        input=True,
                        stream_callback=stream_callback,
                        frames_per_buffer=self._config.vocoder.frames_per_buffer,
                    )
                    try:
                        while stream.is_active():
                            job = recorder_queue.get(block=True)
                            if isinstance(job, (StopJob, StreamStopJob)):
                                stream.stop_stream()
                                break

                    finally:
                        stream.close()
                finally:
                    audio.terminate()
