import math

from kivy.metrics import sp
from kivy.properties import StringProperty
from kivy.utils import hex_colormap
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.widget import MDWidget

from common.md_defs import FontStyle, Role, HAlign


class InfoGroup(MDBoxLayout):
    PAD = sp(0)
    FONT_ROLE = Role.LARGE

    value: str = StringProperty()

    def __init__(
            self,
            name: str,
            value: str = ' ',
    ):
        super().__init__(
            orientation='horizontal',
            padding=self.PAD,
            spacing=self.PAD,
            adaptive_height=True,
        )
        self._name_label = MDLabel(
            text=name,
            font_style=FontStyle.TITLE,
            role=self.FONT_ROLE,
            adaptive_size=True,
            halign=HAlign.LEFT,
        )
        self._value_label = MDLabel(
            text=value,
            markup=True,
            font_style=FontStyle.TITLE,
            role=self.FONT_ROLE,
            adaptive_size=True,
            halign=HAlign.RIGHT,
        )
        self.add_widget(self._name_label)
        self.add_widget(MDWidget())
        self.add_widget(self._value_label)
        self.value = value

    def on_value(self, _, text):
        self._value_label.text = text

    def set_ceil_frac(self, value: float, digits: int):
        if value is None:
            self.value = '  '
            return
        frac, ceil = math.modf(value)
        if digits == 0:
            s = ''
        else:
            frac = round(frac, digits)
            s = f'.{frac}'[2:]
        c = hex_colormap['grey']
        self.value = f'{ceil:.0f}[color={c}]{s}[/color]'
