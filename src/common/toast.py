from enum import auto

from kivy.clock import mainthread
from kivy.metrics import sp
from kivymd.app import MDApp
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from common.enums import LowerEnum
from common.md_defs import CUSTOM, FontStyle


class ToastKind(LowerEnum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()


@mainthread
def toast(
        text,
        kind: ToastKind,
):
    app: MDApp = MDApp.get_running_app()
    match kind:
        case ToastKind.INFO:
            text_color = app.theme_cls.primaryContainerColor
            bg_color = app.theme_cls.onPrimaryContainerColor
        case ToastKind.WARNING:
            text_color = app.theme_cls.primaryContainerColor
            bg_color = 'yellow'
        case ToastKind.ERROR:
            text_color = 'white'
            bg_color = 'red'
        case _:
            raise ValueError('Unknown ToastKind: %s', kind)
    snack = MDSnackbar(
        MDSnackbarText(
            text=str(text),
            theme_text_color=CUSTOM,
            text_color=text_color,
            font_style=FontStyle.TITLE,
        ),
        y=sp(8),
        pos_hint=dict(
            center_x=.5,
        ),
        size_hint_x=.8,
        background_color=bg_color,
    )
    snack.open()
