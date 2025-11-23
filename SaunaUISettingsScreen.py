from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.clock import Clock
from SaunaContext import SaunaContext
import logging


class SaunaUISettingsScreen(Screen):
    """Settings configuration screen"""

    _ctx: SaunaContext = None

    def __init__(self, ctx: SaunaContext=None, **kwargs):
        super().__init__(**kwargs)

        self._ctx = ctx

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Header
        header = BoxLayout(size_hint_y=0.08)
        header.add_widget(Label(text='Settings', font_size='30sp', bold=True))
        layout.add_widget(header)

        # Create tabbed panel
        tab_panel = TabbedPanel(do_default_tab=False, size_hint_y=0.84)
        tab_panel.tab_height = 50

        self.setting_inputs = {}

        # ==================== USER TAB ====================
        user_tab = TabbedPanelItem(text='User')
        user_scroll = ScrollView()
        user_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, padding=10)
        user_layout.bind(minimum_height=user_layout.setter('height'))

        current_section = None

        # Helper function to add section header
        def add_section_header(parent_layout, title):
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
            parent_layout.add_widget(header_label)

            # Create a new GridLayout for this section's settings
            current_section = GridLayout(cols=2, spacing=10, size_hint_y=None)
            current_section.bind(minimum_height=current_section.setter('height'))
            parent_layout.add_widget(current_section)
            return current_section

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
        current_section = add_section_header(user_layout, 'Temperature Settings')
        add_setting('Max Hot Room Temperature, °F', str(self._ctx.getHotRoomMaxTempF()))
        add_setting('Preset Medium Hot Room Temperature, °F', str(self._ctx.getTargetTempPresetMedium()))
        add_setting('Preset High Hot Room Temperature, °F', str(self._ctx.getTargetTempPresetHigh()))
        add_setting('Heater On Lower Temperature Threshold, °F', str(self._ctx.getLowerHotRoomTempThresholdF()))
        add_setting('Heater Off Upper Temperature Threshold, °F', str(self._ctx.getUpperHotRoomTempThresholdF()))
        add_setting('Hot Room Cooling Grace Period, minutes', str(self._ctx.getCoolingGracePeriodMin()))

        # Heater Health Check Settings
        current_section = add_section_header(user_layout, 'Heater Health Check Settings')
        add_setting('Heater Health Check Warmup Time, minutes', str(self._ctx.getHeaterHealthWarmUpTimeMin()))
        add_setting('Heater Health Check Cooldown Time, minutes', str(self._ctx.getHeaterHealthCooldownTimeMin()))
        add_setting('Heater Max Safe Runtime, minutes', str(self._ctx.getHeaterMaxSafeRuntimeMin()))

        # Heater Cycle Control Settings
        current_section = add_section_header(user_layout, 'Heater Cycle Control Settings')
        add_setting('Heater Cycle On Period, minutes', str(self._ctx.getHeaterCycleOnPeriodMin()))
        add_setting('Heater Cycle Off Period, minutes', str(self._ctx.getHeaterCycleOffPeriodMin()))

        # Hot Room Light Settings
        current_section = add_section_header(user_layout, 'Hot Room Light Settings')
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
        current_section = add_section_header(user_layout, 'Display Settings')
        brightness_label = Label(
            text='Display Brightness',
            font_size='20sp',
            size_hint_x=0.6,
            size_hint_y=None,
            height=50,
            halign='left',
            valign='middle'
        )
        brightness_label.bind(size=brightness_label.setter('text_size'))
        current_section.add_widget(brightness_label)

        # Brightness slider
        self.brightness_slider = Slider(
            min=0,
            max=255,
            value=self._ctx.getDisplayBrightness(),
            step=1,
            size_hint_x=0.4,
            size_hint_y=None,
            height=50
        )
        self.brightness_slider.bind(value=self.update_brightness_live)
        current_section.add_widget(self.brightness_slider)

        user_scroll.add_widget(user_layout)
        user_tab.add_widget(user_scroll)
        tab_panel.add_widget(user_tab)

        # ==================== SYSTEM TAB ====================
        system_tab = TabbedPanelItem(text='System')
        system_scroll = ScrollView()
        system_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, padding=10)
        system_layout.bind(minimum_height=system_layout.setter('height'))

        # System Settings
        current_section = add_section_header(system_layout, 'System Settings')

        # CPU Temperature - Read only
        cpu_temp_label = Label(
            text='Current CPU Temperature, °C',
            font_size='20sp',
            size_hint_x=0.6,
            size_hint_y=None,
            height=50,
            halign='left',
            valign='middle'
        )
        cpu_temp_label.bind(size=cpu_temp_label.setter('text_size'))
        current_section.add_widget(cpu_temp_label)

        self.cpu_temp_value = Label(
            text=f'{self._ctx.getCpuTemp():.1f}',
            font_size='28sp',
            size_hint_x=0.4,
            size_hint_y=None,
            height=50,
            color=(0.85, 1, 0.4, 0.8),
            bold=True
        )
        current_section.add_widget(self.cpu_temp_value)

        add_setting('CPU Temperature Warning Threshold, °C', str(self._ctx.getCpuWarnTempC()))
        add_setting('Max Sauna On Time, hours', str(self._ctx.getMaxSaunaOnTimeHrs()))

        # Log Level Spinner
        log_level_label = Label(
            text='Logging Level',
            font_size='20sp',
            size_hint_x=0.6,
            size_hint_y=None,
            height=50,
            halign='left',
            valign='middle'
        )
        log_level_label.bind(size=log_level_label.setter('text_size'))
        current_section.add_widget(log_level_label)

        # Map log level int to string
        log_level_map = {
            logging.DEBUG: 'DEBUG',
            logging.INFO: 'INFO',
            logging.WARNING: 'WARNING',
            logging.ERROR: 'ERROR',
            logging.CRITICAL: 'CRITICAL'
        }
        current_log_level = self._ctx.getLogLevel()
        current_log_level_text = log_level_map.get(current_log_level, 'WARNING')

        self.log_level_spinner = Spinner(
            text=current_log_level_text,
            values=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            font_size='20sp',
            size_hint_x=0.4,
            size_hint_y=None,
            height=50
        )
        current_section.add_widget(self.log_level_spinner)

        # Modbus Communication Settings
        current_section = add_section_header(system_layout, 'Modbus Communication Settings')
        add_setting('Modbus Serial Port', self._ctx.getModbusSerialPort())
        add_setting('Modbus Baud Rate', str(self._ctx.getModbusSerialBaudRate()))
        add_setting('Modbus Timeout, seconds', str(self._ctx.getModbusSerialTimeout()))
        add_setting('Modbus Retries', str(self._ctx.getModbusSerialRetries()))

        # Modbus Register Addresses
        current_section = add_section_header(system_layout, 'Modbus Register Addresses')
        add_setting('Temperature Sensor Address', str(self._ctx.getTempSensorAddr()))
        add_setting('Humidity Sensor Address', str(self._ctx.getHumiditySensorAddr()))
        add_setting('Heater Relay Coil Address', str(self._ctx.getHeaterRelayCoilAddr()))
        add_setting('Hot Room Light Coil Address', str(self._ctx.getHotRoomLightCoilAddr()))
        add_setting('Right Fan Relay Coil Address', str(self._ctx.getRightFanRelayCoilAddr()))
        add_setting('Left Fan Relay Coil Address', str(self._ctx.getLeftFanRelayCoilAddr()))
        add_setting('Fan Module Room Temp Address', str(self._ctx.getFanModuleRoomTempAddr()))
        add_setting('Fan Status Address', str(self._ctx.getFanStatusAddr()))
        add_setting('Fan Speed Address', str(self._ctx.getFanSpeedAddr()))
        add_setting('Number of Fans Address', str(self._ctx.getNumberOfFansAddr()))
        add_setting('Fan Fault Status Address', str(self._ctx.getFanFaultStatusAddr()))
        add_setting('Fan Module Governor Address', str(self._ctx.getFanModuleGovernorAddr()))
        add_setting('Fan Module Reset Governor Value', str(self._ctx.getFanModuleResetGovernorValue()))

        system_scroll.add_widget(system_layout)
        system_tab.add_widget(system_scroll)
        tab_panel.add_widget(system_tab)

        layout.add_widget(tab_panel)

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

        # Schedule CPU temperature updates
        Clock.schedule_interval(self.update_cpu_temp, 2)

    def toggle_light_checkbox(self, instance):
        """Toggle light checkbox state"""
        self.light_checkbox.active = not self.light_checkbox.active
        if self.light_checkbox.active:
            self.light_checkbox.background_normal = 'icons/checkbox-checked.png'
            self.light_checkbox.background_down = 'icons/checkbox-checked.png'
        else:
            self.light_checkbox.background_normal = 'icons/checkbox-unchecked.png'
            self.light_checkbox.background_down = 'icons/checkbox-unchecked.png'

    def update_brightness_live(self, instance, value):
        """Update display brightness in real-time as slider moves"""
        self._ctx.setDisplayBrightness(int(value))

    def update_cpu_temp(self, dt):
        """Update CPU temperature display"""
        self.cpu_temp_value.text = f'{self._ctx.getCpuTemp():.1f}'

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
        self._ctx.setHeaterCycleOnPeriodMin(int(self.setting_inputs['Heater Cycle On Period, minutes'].text))
        self._ctx.setHeaterCycleOffPeriodMin(int(self.setting_inputs['Heater Cycle Off Period, minutes'].text))
        # Save light setting from checkbox (inverted logic: label asks about turning OFF, config is about always ON)
        self._ctx.setHotRoomLightAlwaysOn(not self.light_checkbox.active)
        self._ctx.setModbusSerialPort(self.setting_inputs['Modbus Serial Port'].text)
        self._ctx.setModbusSerialBaudRate(int(self.setting_inputs['Modbus Baud Rate'].text))
        self._ctx.setModbusSerialTimeout(float(self.setting_inputs['Modbus Timeout, seconds'].text))
        self._ctx.setModbusSerialRetries(int(self.setting_inputs['Modbus Retries'].text))
        # Save Modbus register addresses
        self._ctx.setTempSensorAddr(int(self.setting_inputs['Temperature Sensor Address'].text))
        self._ctx.setHumiditySensorAddr(int(self.setting_inputs['Humidity Sensor Address'].text))
        self._ctx.setHeaterRelayCoilAddr(int(self.setting_inputs['Heater Relay Coil Address'].text))
        self._ctx.setHotRoomLightCoilAddr(int(self.setting_inputs['Hot Room Light Coil Address'].text))
        self._ctx.setRightFanRelayCoilAddr(int(self.setting_inputs['Right Fan Relay Coil Address'].text))
        self._ctx.setLeftFanRelayCoilAddr(int(self.setting_inputs['Left Fan Relay Coil Address'].text))
        self._ctx.setFanModuleRoomTempAddr(int(self.setting_inputs['Fan Module Room Temp Address'].text))
        self._ctx.setFanStatusAddr(int(self.setting_inputs['Fan Status Address'].text))
        self._ctx.setFanSpeedAddr(int(self.setting_inputs['Fan Speed Address'].text))
        self._ctx.setNumberOfFansAddr(int(self.setting_inputs['Number of Fans Address'].text))
        self._ctx.setFanFaultStatusAddr(int(self.setting_inputs['Fan Fault Status Address'].text))
        self._ctx.setFanModuleGovernorAddr(int(self.setting_inputs['Fan Module Governor Address'].text))
        self._ctx.setFanModuleResetGovernorValue(int(self.setting_inputs['Fan Module Reset Governor Value'].text))
        # Save display brightness
        self._ctx.setDisplayBrightness(int(self.brightness_slider.value))
        # Save system settings
        self._ctx.setCpuWarnTempC(int(self.setting_inputs['CPU Temperature Warning Threshold, °C'].text))
        self._ctx.setMaxSaunaOnTimeHrs(int(self.setting_inputs['Max Sauna On Time, hours'].text))
        # Save log level
        log_level_str_to_int = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        selected_log_level = log_level_str_to_int.get(self.log_level_spinner.text, logging.WARNING)
        self._ctx.setLogLevel(selected_log_level)
        self._ctx.persist()

        self.manager.current = 'main'
