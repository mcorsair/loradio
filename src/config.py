from dataclasses import dataclass
from pathlib import Path

from codec.modes import VocoderMode
from utils import load_yaml


@dataclass(frozen=True)
class AppConfig:
    font_scale: float


@dataclass(frozen=True)
class VocoderConfig:
    mode: VocoderMode
    chunks: int
    sound_rate: int
    frames_per_buffer: int


@dataclass(frozen=True)
class Config:
    app: AppConfig
    vocoder: VocoderConfig


def load_config(
        filename: str | Path,
) -> Config:
    cfg = load_yaml(filename)
    cfg = cfg['config']

    d = cfg['app']
    app = AppConfig(
        font_scale=d.get('font_scale', 1.0)
    )

    d = cfg['vocoder']
    vocoder = VocoderConfig(
        mode=VocoderMode.from_rate(d['mode']),
        chunks=d['chunks'],
        sound_rate=d['sound_rate'],
        frames_per_buffer=d['frames_per_buffer'],
    )

    return Config(
        app=app,
        vocoder=vocoder,
    )
