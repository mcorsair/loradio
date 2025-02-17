from common.enums import ExtraEnum


class VocoderMode(ExtraEnum):
    MODE_700 = (
        1,
        700,
        4,
        320,
    )
    MODE_1200 = (
        2,
        1200,
        6,
        320,
    )
    MODE_1300 = (
        3,
        1300,
        7,
        320,
    )
    MODE_1400 = (
        4,
        1400,
        7,
        320,
    )
    MODE_1600 = (
        5,
        1600,
        8,
        320,
    )
    MODE_2400 = (
        6,
        2400,
        6,
        160,
    )
    MODE_3200 = (
        7,
        3200,
        8,
        160,
    )

    def __init__(
            self,
            _: int,  # value
            rate: int,
            encoded_len: int,
            samples_per_frame: int,
    ):
        self.rate = rate
        self.encoded_len = encoded_len
        self.samples_per_frame = samples_per_frame

    @staticmethod
    def from_code(code: int):
        for mode in VocoderMode:
            if mode.value == code:
                return mode
        return None

    @staticmethod
    def from_rate(rate: int):
        for mode in VocoderMode:
            if mode.rate == rate:
                return mode
        return None
