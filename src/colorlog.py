import logging
import os

ANSI_CODES = {
    'reset': 0,
    'bold': 1,

    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37,
}

LEVEL_COLORS = {
    logging.DEBUG: ['cyan'],
    logging.INFO: ['yellow'],
    logging.WARNING: ['blue'],
    logging.ERROR: ['red'],
    logging.CRITICAL: ['bold', 'red'],
}


def esc(*codes):
    return '\033[' + ';'.join(map(str, codes)) + 'm'


RESET = esc(ANSI_CODES['reset'])
LEVEL_CODES = {level: esc(*map(ANSI_CODES.get, LEVEL_COLORS[level])) for level in LEVEL_COLORS}
COLOR_CODES = {color: esc(ANSI_CODES[color]) for color in ANSI_CODES}
EMPTY_CODES = {color: '' for color in ANSI_CODES}


STYLES = {
    '%': (logging.PercentStyle, logging.BASIC_FORMAT),
    '{': (logging.StrFormatStyle, '{levelname}:{name}:{message}'),
    '$': (logging.StringTemplateStyle, '${levelname}:${name}:${message}'),
}


class ColorFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super(ColorFormatter, self).__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.support_ansi_codes = False
        self.style = STYLES[style]

    def formatMessage(self, record):
        if self.support_ansi_codes:
            color_codes = COLOR_CODES
            level_code = LEVEL_CODES[record.levelno]
        else:
            color_codes = EMPTY_CODES
            level_code = ''
        all_codes = color_codes
        all_codes['levelcolor'] = level_code

        # форматируем сначала само сообщение:
        if '{reset}' in record.message:
            for k, v in all_codes.items():
                record.message = record.message.replace('{' + k + '}', v)

        # выделяем цветом все сообщение об ошибке:
        if record.levelno in [logging.ERROR, logging.CRITICAL]:
            record.message = level_code + record.message + RESET

        # теперь форматируем всю запись:
        record.__dict__.update(all_codes)
        s = super(ColorFormatter, self).formatMessage(record)
        return s


class ColorHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super(ColorHandler, self).__init__(stream)
        self.support_ansi_codes = self.stream.isatty() or 'ANSICON' in os.environ

    def setFormatter(self, fmt):
        super(ColorHandler, self).setFormatter(fmt)
        if isinstance(fmt, ColorFormatter):
            fmt.support_ansi_codes = self.support_ansi_codes
