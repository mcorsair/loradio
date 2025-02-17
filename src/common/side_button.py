from kivy.metrics import sp
from kivy.properties import BooleanProperty
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon

from common.md_defs import CUSTOM


class SideButton(MDButton):
    BUTTON_RADIUS = 8
    STYLE = 'outlined'
    DOWN_BUTTON_COLOR = 'green'

    active: bool = BooleanProperty(False)

    def __init__(
            self,
            text: str,
            icon: str,
            font_size: float,
            on_press,
            height: float | None = None,
            on_release=None,
            **kwargs,
    ):
        height = height or font_size * 2.5
        self._text_button = MDButtonText(
            text=text,
            theme_font_size=CUSTOM,
            font_size=font_size,
            markup=True,
        )
        self._icon_button = MDButtonIcon(
            icon=icon,
            theme_font_size=CUSTOM,
            font_size=font_size,
        )
        self._user_on_press = on_press
        super().__init__(
            self._icon_button,
            self._text_button,
            style=self.STYLE,
            theme_bg_color=CUSTOM,
            theme_width=CUSTOM,
            radius=sp(self.BUTTON_RADIUS),

            on_press=self._on_press_wrapper,

            ripple_scale=0,

            size_hint_y=None,
            height=height,

            **kwargs,
        )
        if on_release:
            self.bind(on_release=on_release)

    @property
    def icon_button(self):
        return self._icon_button

    @property
    def text_button(self):
        return self._text_button

    def _on_press_wrapper(self, *args, **kwargs):
        if self.disabled:
            return True
        return self._user_on_press(*args, **kwargs)

    def on_active(self, _, active: bool):
        self.md_bg_color = self.DOWN_BUTTON_COLOR if active else self.theme_cls.surfaceColor
