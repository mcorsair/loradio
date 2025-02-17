import struct

from codec.jobs import PacketKind
from codec.modes import VocoderMode

MAGIC_WORD = 'PaCkEt'.encode()

DURATION_FORMAT = 'f'
DURATION_SIZE = struct.calcsize(DURATION_FORMAT)

INDEX_FORMAT = 'i'
INDEX_SIZE = struct.calcsize(INDEX_FORMAT)


class Flags:
    TEST = 1 << 7


def encode_payload(
        payload: bytes | None,
):
    payload = payload or []
    assert len(payload) < 256, 'max 256 payload'
    payload_size = len(payload)
    buffer = bytearray()

    buffer.extend(MAGIC_WORD)
    buffer.append(payload_size)
    buffer.extend(payload)

    return bytes(buffer)


def encode_stream_start(
        test: bool,
        mode: VocoderMode,
):
    payload = bytearray()

    flags = PacketKind.STREAM_START.value | (Flags.TEST if test else 0)
    payload.append(flags)

    payload.append(mode.value)

    return encode_payload(payload)


def encode_stream_frame(
        test: bool,
        data: bytes,
        duration: float,
        packet_index: int | None,
):
    payload = bytearray()

    flags = PacketKind.STREAM_FRAME.value | (Flags.TEST if test else 0)
    payload.append(flags)

    if test:
        payload.extend(struct.pack(DURATION_FORMAT, duration))
        payload.extend(struct.pack(INDEX_FORMAT, packet_index))

        if (pad_len := len(data) - (DURATION_SIZE + INDEX_SIZE)) > 0:
            payload.extend([0] * pad_len)

    else:
        payload.extend(data)

    return encode_payload(payload)


def encode_stream_stop(
        test: bool,
        duration: float,
):
    payload = bytearray()

    flags = PacketKind.STREAM_STOP.value | (Flags.TEST if test else 0)
    payload.append(flags)

    if test:
        payload.extend(struct.pack(DURATION_FORMAT, duration))
    else:
        pass

    return encode_payload(payload)


def decode_payload(
        payload: bytes,
):
    index = 0

    # --- flags ---

    flags = payload[index]
    test = bool(Flags.TEST & flags)
    kind = flags & (Flags.TEST - 1)
    kind = PacketKind(kind)
    index += 1

    match kind:
        case PacketKind.STREAM_START:

            mode = payload[index]
            mode = VocoderMode.from_code(mode)
            index += 1

            return kind, test, (mode,)

        case PacketKind.STREAM_FRAME:

            if test:
                b = payload[index: index + DURATION_SIZE]
                duration, = struct.unpack(DURATION_FORMAT, b)
                index += DURATION_SIZE

                b = payload[index: index + INDEX_SIZE]
                packet_index, = struct.unpack(INDEX_FORMAT, b)
                index += INDEX_SIZE

                block = None
            else:
                block = payload[index:]
                duration = None
                packet_index = None

            return kind, test, (block, duration, packet_index)

        case PacketKind.STREAM_STOP:

            if test:
                b = payload[index: index + DURATION_SIZE]
                duration, = struct.unpack(DURATION_FORMAT, b)
                index += DURATION_SIZE
            else:
                duration = None

            return kind, test, (duration,)

        case _:
            raise NotImplementedError()
