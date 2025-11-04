from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from SaunaContext import SaunaContext


class SaunaUISettingsScreen(Screen):
    """Settings configuration screen"""

    _ctx: SaunaContext = None

    def __init__(self, ctx: SaunaContext=None, **kwargs):
        super().__init__(**kwargs)

        self._ctx = ctx

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Header
        header = BoxLayout(size_hint_y=0.1)
        header.add_widget(Label(text='Settings', font_size='30sp', bold=True))
        layout.add_widget(header)

        # Settings list with input fields
        scroll_view = ScrollView(size_hint=(1, 0.9))
        settings_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, padding=10)
        settings_layout.bind(minimum_height=settings_layout.setter('height'))

        self.setting_inputs = {}
        current_section = None

        # Helper function to add section header
        def add_section_header(title):
            nonlocal current_section
            header_label = Label(
                text=title,
                font_size='24sp',
                bold=True,
                size_hint_y=None,
                height=40,
                color=(0.5, 0.8, 1.0, 1),
                halign='left',
                valign='middle'
            )
            header_label.bind(size=header_label.setter('text_size'))
            settings_layout.add_widget(header_label)

            # Create a new GridLayout for this section's settings
            current_section = GridLayout(cols=2, spacing=10, size_hint_y=None)
            current_section.bind(minimum_height=current_section.setter('height'))
            settings_layout.add_widget(current_section)

        # Helper function to add setting
        def add_setting(setting_name, default_value):
            label = Label(
                text=setting_name,
                font_size='20sp',
                size_hint_x=0.6,
                size_hint_y=None,
                height=50,
                halign='left',
                valign='middle'
            )
            label.bind(size=label.setter('text_size'))
            current_section.add_widget(label)

            input_field = TextInput(
                text=default_value,
                multiline=False,
                font_size='28sp',
                size_hint_x=0.4,
                size_hint_y=None,
                height=50
            )
            self.setting_inputs[setting_name] = input_field
            current_section.add_widget(input_field)

        # Temperature Settings
        add_section_header('Temperature Settings')
        add_setting('Max Hot Room Temperature, °F', str(self._ctx.getHotRoomMaxTempF()))
        add_setting('Preset Medium Hot Room Temperature, °F', str(self._ctx.getTargetTempPresetMedium()))
        add_setting('Preset High Hot Room Temperature, °F', str(self._ctx.getTargetTempPresetHigh()))
        add_setting('Heater On Lower Temperature Threshold, °F', str(self._ctx.getLowerHotRoomTempThresholdF()))
        add_setting('Heater Off Upper Temperature Threshold, °F', str(self._ctx.getUpperHotRoomTempThresholdF()))
        add_setting('Hot Room Cooling Grace Period, minutes', str(self._ctx.getCoolingGracePeriodMin()))

        # Heater Health Check Settings
        add_section_header('Heater Health Check Settings')
        add_setting('Heater Health Check Warmup Time, minutes', str(self._ctx.getHeaterHealthWarmUpTimeMin()))
        add_setting('Heater Health Check Cooldown Time, minutes', str(self._ctx.getHeaterHealthCooldownTimeMin()))
        add_setting('Heater Max Safe Runtime, minutes', str(self._ctx.getHeaterMaxSafeRuntimeMin()))

        # RS485 Communication Settings
        add_section_header('RS485 Communication Settings')
        add_setting('RS485 Serial Port', self._ctx.getRs485SerialPort())
        add_setting('RS485 Baud Rate', str(self._ctx.getRs485SerialBaudRate()))
        add_setting('RS485 Timeout, seconds', str(self._ctx.getRs485SerialTimeout()))
        add_setting('RS485 Retries', str(self._ctx.getRs485SerialRetries()))

        # Hot Room Light Settings
        add_section_header('Hot Room Light Settings')
        light_label = Label(
            text='Turn Hot Room Light Off When Sauna is Off',
            font_size='20sp',
            size_hint_y=None,
            height=50,
            halign='left',
            valign='middle'
        )
        light_label.bind(size=light_label.setter('text_size'))
        current_section.add_widget(light_label)

        # Checkbox button
        self.light_checkbox = Button(
            size_hint=(None, None),
            size=(45, 45),
            background_normal='icons/checkbox-unchecked.png',
            background_down='icons/checkbox-unchecked.png',
            border=(0, 0, 0, 0)
        )
        # Set initial state based on config (inverted: label asks about turning OFF, config is about always ON)
        self.light_checkbox.active = not self._ctx.getHotRoomLightAlwaysOn()
        if self.light_checkbox.active:
            self.light_checkbox.background_normal = 'icons/checkbox-checked.png'
            self.light_checkbox.background_down = 'icons/checkbox-checked.png'
        self.light_checkbox.bind(on_press=self.toggle_light_checkbox)

        current_section.add_widget(self.light_checkbox)

        # Display Settings
        add_section_header('Display Settings')
        brightness_label = Label(
            text='Display Brightness',
            font_size='20sp',
            size_hint_y=None,
            height=50,
            halign='left',
            valign='middle'
        )
        brightness_label.bind(size=brightness_label.setter('text_size'))
        current_section.add_widget(brightness_label)

        # Brightness slider with value label
        brightness_container = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        self.brightness_slider = Slider(
            min=0,
            max=255,
            value=self._ctx.getDisplayBrightness(),
            step=1,
            size_hint_x=0.7
        )
        self.brightness_value_label = Label(
            text=str(int(self.brightness_slider.value)),
            font_size='20sp',
            size_hint_x=0.3
        )
        self.brightness_slider.bind(value=self.update_brightness_label)
        brightness_container.add_widget(self.brightness_slider)
        brightness_container.add_widget(self.brightness_value_label)
        current_section.add_widget(brightness_container)

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

    def toggle_light_checkbox(self, instance):
        """Toggle light checkbox state"""
        self.light_checkbox.active = not self.light_checkbox.active
        if self.light_checkbox.active:
            self.light_checkbox.background_normal = 'icons/checkbox-checked.png'
            self.light_checkbox.background_down = 'icons/checkbox-checked.png'
        else:
            self.light_checkbox.background_normal = 'icons/checkbox-unchecked.png'
            self.light_checkbox.background_down = 'icons/checkbox-unchecked.png'

    def update_brightness_label(self, instance, value):
        """Update brightness value label when slider changes"""
        self.brightness_value_label.text = str(int(value))

    def save_settings(self, instance):
        # Save temperature settings
        self._ctx.setHotRoomMaxTempF(int(self.setting_inputs['Max Hot Room Temperature, °F'].text))
        self._ctx.setTargetTempPresetMedium(int(self.setting_inputs['Preset Medium Hot Room Temperature, °F'].text))
        self._ctx.setTargetTempPresetHigh(int(self.setting_inputs['Preset High Hot Room Temperature, °F'].text))
        self._ctx.setLowerHotRoomTempThresholdF(int(self.setting_inputs['Heater On Lower Temperature Threshold, °F'].text))
        self._ctx.setUpperHotRoomTempThresholdF(int(self.setting_inputs['Heater Off Upper Temperature Threshold, °F'].text))
        self._ctx.setCoolingGracePeriodMin(int(self.setting_inputs['Hot Room Cooling Grace Period, minutes'].text))
        self._ctx.setHeaterHealthWarmupTimeMin(int(self.setting_inputs['Heater Health Check Warmup Time, minutes'].text))
        self._ctx.setHeaterHealthCooldownTimeMin(int(self.setting_inputs['Heater Health Check Cooldown Time, minutes'].text))
        self._ctx.setHeaterMaxSafeRuntimeMin(int(self.setting_inputs['Heater Max Safe Runtime, minutes'].text))
        # Save light setting from checkbox (inverted logic: label asks about turning OFF, config is about always ON)
        self._ctx.setHotRoomLightAlwaysOn(not self.light_checkbox.active)
        self._ctx.setRs485SerialPort(self.setting_inputs['RS485 Serial Port'].text)
        self._ctx.setRs485SerialBaudRate(int(self.setting_inputs['RS485 Baud Rate'].text))
        self._ctx.setRs485SerialTimeout(float(self.setting_inputs['RS485 Timeout, seconds'].text))
        self._ctx.setRs485SerialRetries(int(self.setting_inputs['RS485 Retries'].text))
        # Save display brightness
        self._ctx.setDisplayBrightness(int(self.brightness_slider.value))

        self.manager.current = 'main'