from kivy.config import Config
# Enable virtual keyboard - must be before other kivy imports
Config.set('kivy', 'keyboard_mode', 'systemanddock')
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from SaunaContext import SaunaContext
from SaunaController import SaunaController

class SettingsScreen(Screen):
    """Settings configuration screen"""

    _ctx: SaunaContext = None
    _sc: SaunaController = None

    def __init__(self, ctx: SaunaContext=None, sc: SaunaController=None, **kwargs):
        super().__init__(**kwargs)

        self._ctx = ctx
        self._sc = sc

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Header
        header = BoxLayout(size_hint_y=0.1)
        header.add_widget(Label(text='Settings', font_size='30sp', bold=True))
        layout.add_widget(header)

        # Settings list with input fields
        scroll_view = ScrollView(size_hint=(1, 0.9))
        settings_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=10)
        settings_layout.bind(minimum_height=settings_layout.setter('height'))

        # Load values from context or use defaults
        settings = [
            ('Max Hot Room Temperature (°F)', str(self._ctx.getHotRoomMaxTempF())),
            ('Preset Medium Hot Room Temperature (°F)', str(self._ctx.getTargetTempPresetMedium())),
            ('Preset High Hot Room Temperature (°F)', str(self._ctx.getTargetTempPresetHigh())),
            ('Heater On Lower Temperature Threshold (°F)', str(self._ctx.getLowerHotRoomTempThresholdF())),
            ('Heater Off Upper Temperature Threshold (°F)', str(self._ctx.getUpperHotRoomTempThresholdF())),
            ('Hot Room Cooling Grace Period (seconds)', str(self._ctx.getCoolingGracePeriod())),
            ('Heater Health Check Warmup Time (seconds)', str(self._ctx.getHeaterHealthWarmUpTime())),
            ('Heater Health Check Cooldown Time (seconds)', str(self._ctx.getHeaterHealthCooldownTime())),
            ('RS485 Serial Port', self._ctx.getRs485SerialPort()),
            ('RS485 Baud Rate', str(self._ctx.getRs485SerialBaudRate())),
            ('RS485 Timeout (seconds)', str(self._ctx.getRs485SerialTimeout())),
            ('RS485 Retries', str(self._ctx.getRs485SerialRetries()))
        ]

        self.setting_inputs = {}

        for setting_name, default_value in settings:
            # Setting Label
            label = Label(
                text=setting_name,
                font_size='16sp',
                size_hint_y=None,
                height=50,
                halign='left',
                valign='middle'
            )
            label.bind(size=label.setter('text_size'))
            settings_layout.add_widget(label)

            # Setting input field
            input_field = TextInput(
                text=default_value,
                multiline=False,
                font_size='16sp',
                size_hint_y=None,
                height=50
            )
            self.setting_inputs[setting_name] = input_field
            settings_layout.add_widget(input_field)

        scroll_view.add_widget(settings_layout)
        layout.add_widget(scroll_view)

        # Save button
        save_btn = Button(
            text='Ok',
            size_hint=(None, None),
            size=(200, 60),
            pos_hint={'center_x': 0.5},
            font_size='20sp',
            background_color=(0.5, 0.8, 1.0, 1)
        )
        save_btn.bind(on_press=self.save_settings)
        layout.add_widget(save_btn)

        self.add_widget(layout)

    def save_settings(self, instance):
        """Save all settings"""
        print("Saving settings:")
        # Save temperature settings
        self._ctx.setHotRoomMaxTempF(int(self.setting_inputs['Max Hot Room Temperature (°F)'].text))
        self._ctx.setTargetTempPresetMedium(int(self.setting_inputs['Preset Medium Hot Room Temperature (°F)'].text))
        self._ctx.setTargetTempPresetHigh(int(self.setting_inputs['Preset High Hot Room Temperature (°F)'].text))
        self._ctx.setLowerHotRoomTempThresholdF(int(self.setting_inputs['Heater On Lower Temperature Threshold (°F)'].text))
        self._ctx.setUpperHotRoomTempThresholdF(int(self.setting_inputs['Heater Off Upper Temperature Threshold (°F)'].text))
        self._ctx.setCoolingGracePeriod(int(self.setting_inputs['Hot Room Cooling Grace Period (seconds)'].text))
        self._ctx.setLHeaterHealthWarmupTime(int(self.setting_inputs['Heater Health Check Warmup Time (seconds)'].text))
        self._ctx.setHeaterHealthCooldownTime(int(self.setting_inputs['Heater Health Check Cooldown Time (seconds)'].text))
        # Save RS485 settings # TODO - reset connection
        self._ctx.setRs485SerialPort(self.setting_inputs['RS485 Serial Port'].text)
        self._ctx.setRs485SerialBaudRate(int(self.setting_inputs['RS485 Baud Rate'].text))
        self._ctx.setRs485SerialTimeout(float(self.setting_inputs['RS485 Timeout (seconds)'].text))
        self._ctx.setRs485SerialRetries(int(self.setting_inputs['RS485 Retries'].text))

        self.manager.current = 'main'