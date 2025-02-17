import logging
from functools import partial

from kivy.clock import mainthread, Clock
from kivy.core.window import Window
from kivy.metrics import sp, dp
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.divider import MDDivider
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.widget import MDWidget

from codec.jobs import TaskRole
from codec.modes import VocoderMode
from common.handle_error import handle_error
from common.info_group import InfoGroup
from common.md_defs import ThemeStyle, Orientation
from common.side_button import SideButton
from config import Config
from common.controls import hspacer
from monitor import DeviceMonitor
from model import Model
from processes.decoder_process import DecoderProcessStat
from processes.encoder_process import EncoderProcessStat
from processes.serial_process import SerialProcessStat
from utils import rate_limit, no_exceptions


class MainApp(MDApp):
    NAME = 'app'

    TITLE = 'LoRaDio'

    THEME = ThemeStyle.DARK
    PRIMARY_PALETTE = 'Blue'

    SIDE_WIDTH = sp(240)

    BUTTON_FONT_SIZE = sp(20)
    PRESS_RATE_LIMIT_INTERVAL = 0.1
    PAD = sp(12)

    PERIODIC_INTERVAL = 0.2

    def __init__(
            self,
            config: Config,
            monitor: DeviceMonitor,
            model: Model,
            device_node: str,
            **kwargs,
    ):
        super().__init__(
            **kwargs,
        )
        self._logger = logging.getLogger(self.NAME)
        self._config = config
        self._monitor = monitor
        self._model = model

        self.title = f'{self.TITLE}'

        self.theme_cls.theme_style = self.THEME
        self.theme_cls.primary_palette = self.PRIMARY_PALETTE
        self.theme_cls.theme_style_switch_animation = True

        self._vocoder_mode = config.vocoder.mode

        Window.bind(
            on_request_close=self._request_close,
        )

        model.bind(
            device=lambda _, device: self._update_state(reason='device: %s' % device.device_node if device else 'none'),
            active=lambda _, active: self._update_state(reason='active: %s' % (active and 'true' or 'false')),
            streaming=lambda _, streaming: self._update_state(reason='streaming: %s' % (streaming and 'true' or 'false')),
        )

        # --- UI ---

        self._device_info = InfoGroup(
            name='DEVICE',
            value=device_node,
        )

        self._start_button = SideButton(
            text='START',
            icon='flash',
            font_size=self.BUTTON_FONT_SIZE,
            on_press=self._on_start_clicked,
        )

        self._ptt_button = SideButton(
            text='PTT',
            icon='radio-tower',
            font_size=self.BUTTON_FONT_SIZE,
            height=4 * self.BUTTON_FONT_SIZE,
            on_press=self._on_ptt_press,
            on_release=self._on_ptt_release,
        )

        self._ptt_test_button = SideButton(
            text='PTT TEST',
            icon='radio-tower',
            font_size=self.BUTTON_FONT_SIZE,
            on_press=self._on_ptt_test_press,
            on_release=self._on_ptt_test_release,
        )

        self._vocoder_mode_button = SideButton(
            text=f'CODEC2',
            icon='star',
            font_size=self.BUTTON_FONT_SIZE,
            on_press=self._on_vocoder_mode_clicked,
        )

        self._rx_codec_info = InfoGroup(
            name='RX CODEC',
        )
        self._rx_total_info = InfoGroup(
            name='RX TOTAL',
            value='0',
        )
        self._rx_current_info = InfoGroup(
            name='RX CURRENT',
            value='0',
        )
        self._rx_packets_info = InfoGroup(
            name='RX PACKETS',
            value='0',
        )
        self._rx_delay_info = InfoGroup(
            name='RX DELAY',
            value='0.0',
        )
        self._rx_lost_info = InfoGroup(
            name='RX LOST',
            value='0',
        )
        self._rx_speed_info = InfoGroup(
            name='RX SPEED',
            value='0',
        )
        self._rx_duration_info = InfoGroup(
            name='RX DURATION',
            value='0.0',
        )
        self._tx_codec_info = InfoGroup(
            name='TX CODEC',
        )
        self._tx_total_info = InfoGroup(
            name='TX TOTAL',
            value='0',
        )
        self._tx_packets_info = InfoGroup(
            name='TX PACKETS',
            value='0',
        )
        self._tx_duration_info = InfoGroup(
            name='TX DURATION',
            value='0.0',
        )
        self._tx_current_info = InfoGroup(
            name='TX CURRENT',
            value='0',
        )
        self._tx_speed_info = InfoGroup(
            name='TX SPEED',
            value='0',
        )

        self._test_button = SideButton(
            text='TEST',
            icon='play',
            font_size=self.BUTTON_FONT_SIZE,
            on_press=self._on_test_clicked,
        )

        quit_button = SideButton(
            text='QUIT',
            icon='exit-run',
            font_size=self.BUTTON_FONT_SIZE,
            on_press=self._on_quit_clicked,
        )

        controls = [
            self._device_info,
            self._start_button,

            hspacer(sp(4)),

            self._vocoder_mode_button,

            hspacer(sp(4)),

            self._ptt_button,

            hspacer(sp(4)),

            self._ptt_test_button,

            hspacer(sp(4)),

            self._rx_delay_info,
            self._rx_lost_info,

            MDWidget(),
            # self._test_button,
            quit_button,
        ]
        side_layout = MDBoxLayout(
            *controls,
            orientation=Orientation.VERTICAL,
            padding=self.PAD,
            spacing=self.PAD,
            size_hint_x=None,
            width=self.SIDE_WIDTH,
        )

        controls = [
            self._rx_codec_info,
            self._rx_duration_info,
            self._rx_packets_info,
            self._rx_total_info,
            self._rx_current_info,
            self._rx_speed_info,
            MDWidget(),
        ]
        rx_layout = MDBoxLayout(
            *controls,
            orientation=Orientation.VERTICAL,
            padding=self.PAD,
            spacing=self.PAD,
        )

        controls = [
            self._tx_codec_info,
            self._tx_duration_info,
            self._tx_packets_info,
            self._tx_total_info,
            self._tx_current_info,
            self._tx_speed_info,
            MDWidget(),
        ]
        tx_layout = MDBoxLayout(
            *controls,
            orientation=Orientation.VERTICAL,
            padding=self.PAD,
            spacing=self.PAD,
        )

        controls = [
            side_layout,
            MDDivider(orientation=Orientation.VERTICAL),
            rx_layout,
            MDDivider(orientation=Orientation.VERTICAL),
            tx_layout,
        ]
        self._root = MDBoxLayout(
            *controls,
            orientation=Orientation.HORIZONTAL,
            # padding=self.PAD,
            # spacing=self.PAD,
        )

        # --- initialized ---

        self._update_state('init')
        Clock.schedule_interval(self._periodic_tick, self.PERIODIC_INTERVAL)
        monitor.enum_devices()
        monitor.start()

    def build(self):
        return MDScreen(
            self._root,
            md_bg_color=self.theme_cls.backgroundColor,
        )

    def _cleanup(self):
        self._model.stop()

    @handle_error
    def _request_close(self, *_, **__):
        self._logger.info('request close')
        self._cleanup()

    @rate_limit(interval=PRESS_RATE_LIMIT_INTERVAL)
    @handle_error
    def _on_quit_clicked(self, *_):
        self._cleanup()
        self.stop()

    @rate_limit(interval=PRESS_RATE_LIMIT_INTERVAL)
    @handle_error
    def _on_start_clicked(self, *_):
        if self._model.active:
            self._model.stop()
        else:
            self._model.start()

    @rate_limit(interval=PRESS_RATE_LIMIT_INTERVAL)
    @handle_error
    def _on_ptt_press(self, *_):
        self._model.stream_start(
            mode=self._vocoder_mode,
            test=False,
        )

    @rate_limit(interval=PRESS_RATE_LIMIT_INTERVAL)
    @handle_error
    def _on_ptt_release(self, *_):
        self._model.stream_stop()

    @rate_limit(interval=PRESS_RATE_LIMIT_INTERVAL)
    @handle_error
    def _on_ptt_test_press(self, *_):
        self._model.stream_start(
            mode=self._vocoder_mode,
            test=True,
        )

    @rate_limit(interval=PRESS_RATE_LIMIT_INTERVAL)
    @handle_error
    def _on_ptt_test_release(self, *_):
        self._model.stream_stop()

    @rate_limit(interval=PRESS_RATE_LIMIT_INTERVAL)
    @handle_error
    def _on_test_clicked(self, *_):
        pass

    @rate_limit(interval=PRESS_RATE_LIMIT_INTERVAL)
    @handle_error
    def _on_vocoder_mode_clicked(self, *_):

        def menu_clicked(param: VocoderMode):
            menu.dismiss()
            self._vocoder_mode = param
            self._update_state(reason='mode: %s' % param.name)

        menu_items = [dict(
            id=f'mode{idx:02d}',
            text=f'{mode.rate}',
            leading_icon='check' if mode == self._vocoder_mode else 'circle-small',
            on_release=partial(menu_clicked, param=mode),
            height=dp(60),
        ) for idx, mode in enumerate(VocoderMode)]
        menu = MDDropdownMenu(
            caller=self._vocoder_mode_button,
            items=menu_items,
            padding=sp(2),
        )
        menu.open()

    def _periodic_tick(self, *_):
        with no_exceptions():
            stats = self._model.get_stats()

            if stat := stats.get(TaskRole.SERIAL):
                stat: SerialProcessStat
                self._rx_total_info.set_ceil_frac(stat.rx_total, digits=0)
                self._tx_total_info.set_ceil_frac(stat.tx_total, digits=0)
                self._tx_duration_info.set_ceil_frac(stat.tx_duration, digits=1)
                self._tx_current_info.set_ceil_frac(stat.tx_current, digits=0)
                self._tx_speed_info.set_ceil_frac((stat.tx_speed or 0) * 8, digits=0)

            if stat := stats.get(TaskRole.ENCODER):
                stat: EncoderProcessStat
                self._tx_packets_info.set_ceil_frac(stat.tx_packets, digits=0)

            if stat := stats.get(TaskRole.DECODER):
                stat: DecoderProcessStat
                self._rx_duration_info.set_ceil_frac(stat.rx_duration, digits=1)
                self._rx_packets_info.set_ceil_frac(stat.rx_packets, digits=0)
                self._rx_current_info.set_ceil_frac(stat.rx_current, digits=0)
                self._rx_codec_info.value = f'{stat.rx_mode.rate}' if stat.rx_mode else ' '
                self._rx_delay_info.set_ceil_frac(stat.rx_delay, digits=1)
                self._rx_lost_info.set_ceil_frac(stat.rx_lost, digits=0)
                self._rx_speed_info.set_ceil_frac((stat.rx_speed or 0) * 8, digits=0)

    @mainthread
    def _update_state(self, reason: str | None):
        if reason:
            self._logger.debug('update, reason: {blue}%s{reset}', reason)

        device = self._model.device
        attached = device is not None
        active = self._model.active
        streaming = self._model.streaming
        test = self._model.test

        self._device_info.disabled = not attached

        self._start_button.disabled = not attached
        self._start_button.active = active
        self._start_button.text_button.text = 'STOP' if active else 'START'

        self._ptt_button.disabled = not active or (streaming and test)
        self._ptt_button.active = streaming and not test

        self._ptt_test_button.disabled = not active or (streaming and not test)
        self._ptt_test_button.active = streaming and test

        self._vocoder_mode_button.text_button.text = f'CODEC2   [b]{self._vocoder_mode.rate}[/b]'

        self._tx_codec_info.value = f'{self._vocoder_mode.rate}'
