from dataclasses import dataclass
from enum import Enum, auto

import numpy as np

from codec.modes import VocoderMode
from common.enums import LowerEnum


class TaskRole(LowerEnum):
    SERIAL = auto()
    ENCODER = auto()
    DECODER = auto()
    PLAYER = auto()
    RECORDER = auto()


class Flags(Enum):
    TEST = 1 << 7


class PacketKind(Enum):
    STREAM_START = 1
    STREAM_STOP = 2
    STREAM_FRAME = 3

    @staticmethod
    def from_job(job: 'Job'):
        if isinstance(job, StreamStartJob):
            kind = PacketKind.STREAM_START
        elif isinstance(job, StreamStopJob):
            kind = PacketKind.STREAM_STOP
        elif isinstance(job, StreamFrameJob):
            kind = PacketKind.STREAM_FRAME
        else:
            raise NotImplementedError(str(job))
        return kind


@dataclass(frozen=True)
class Job:
    pass


@dataclass(frozen=True)
class StopJob(Job):
    pass


@dataclass(frozen=True)
class SendJob(Job):
    kind: PacketKind
    data: bytes


@dataclass(frozen=True)
class RecvJob(Job):
    data: bytes


@dataclass(frozen=True)
class StreamStartJob(Job):
    mode: VocoderMode
    test: bool


@dataclass(frozen=True)
class StreamStopJob(Job):
    pass


@dataclass(frozen=True)
class StreamFrameJob(Job):
    frame: np.ndarray


@dataclass(frozen=True)
class PlayJob(Job):
    samples: np.ndarray
