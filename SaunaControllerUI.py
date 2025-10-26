import os

from kivy.config import Config
# Enable virtual keyboard - must be before other kivy imports
Config.set('kivy', 'keyboard_mode', 'systemanddock')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView

import random
from datetime import datetime
from ErrorManager import ErrorManager
from SaunaDevices import SaunaDevices
from SaunaContext import SaunaContext
from SettingsScreen import SettingsScreen

# Set window size for Raspberry Pi touchscreen (portrait)
Window.size = (800, 1280)
Window.rotation = 270

class StatusIcon(Button):
    """Custom status icon button with image"""
    def __init__(self, icon_image, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (50, 50)  # Smaller size
        self.background_normal = icon_image
        self.background_down = icon_image
        self.border = (0, 0, 0, 0)

class MainScreen(Screen):
    """Main sauna control screen"""
    def __init__(self, ctx=None, errorMgr: ErrorManager=None, sd: SaunaDevices=None, **kwargs):
        super().__init__(**kwargs)
        self.ctx = ctx
        self.sd = sd
        self.errorMgr = errorMgr
        self.active_preset = None
        self.preset_buttons = []
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)

        # Top status bar
        self.status_bar = BoxLayout(size_hint_y=0.06, spacing=20)  # Smaller height to move icons up

        self.fan_icon = StatusIcon('icons/fan.png')
        self.fan_icon.bind(on_press=self.open_fan_screen)
        self.status_bar.add_widget(self.fan_icon)

        self.wifi_icon = StatusIcon('icons/wifi.png')
        self.wifi_icon.bind(on_press=self.open_wifi_screen)
        self.status_bar.add_widget(self.wifi_icon)

        self.settings_icon = StatusIcon('icons/settings.png')
        self.settings_icon.bind(on_press=self.open_settings_screen)
        self.status_bar.add_widget(self.settings_icon)

        self.status_bar.add_widget(Label())  # Spacer

        self.heater_icon = StatusIcon('icons/heater_off.png')
        self.status_bar.add_widget(self.heater_icon)

        self.errors_icon = StatusIcon('icons/errors.png')
        self.errors_icon.bind(on_press=self.open_errors_screen)
        self.errors_icon.background_color = (1, 0, 0, 1)  # Red when errors present
        # Don't add errors icon yet - will be added only when there are errors

        layout.add_widget(self.status_bar)

        # Spacer to push content down
        layout.add_widget(Label(size_hint_y=0.12))

        # Clock row
        clock_row = BoxLayout(size_hint_y=0.15, spacing=5)
        current_time = datetime.now().strftime('%I:%M:%S').lstrip('0')
        self.clock_label = Label(
            text=current_time,
            font_size='120sp',
            bold=True,
            font_name='fonts/DSEG7Classic-Bold.ttf',  # 7-segment style font
            color=(0.6, 0.8, 0.6, 1),  # Grey-green color
            halign='center',
            valign='middle'
        )
        self.clock_label.bind(size=self.clock_label.setter('text_size'))
        clock_row.add_widget(self.clock_label)
        layout.add_widget(clock_row)

        # Spacer between clock and temperature
        layout.add_widget(Label(size_hint_y=0.10))

        # Temperature and Humidity Display
        sensor_layout = BoxLayout(orientation='vertical', size_hint_y=0.35, spacing=20)

        # Large temperature display - takes full row - touchable to toggle C/F
        temp_display = '0°F' if not self.ctx else f'{int(self.ctx.getHotRoomTempF())}°F'

        class TouchableLabel(ButtonBehavior, Label):
            pass

        self.temp_label = TouchableLabel(
            text=temp_display,
            font_size='200sp',
            bold=True,
            color=(1, 0.5, 0, 1),
            size_hint_y=0.50
        )
        self.temp_label.bind(on_press=self.toggle_temperature_unit)
        self.temp_unit = 'F'  # Default to Fahrenheit
        sensor_layout.add_widget(self.temp_label)

        # Humidity display with icon - centered
        humidity_outer = BoxLayout(orientation='vertical', size_hint_y=0.50)

        # Top spacer to push humidity down
        humidity_outer.add_widget(Label(size_hint_y=0.3))

        humidity_container = BoxLayout(orientation='horizontal', size_hint_y=0.7)
        humidity_container.add_widget(Label())  # Left spacer

        humidity_row = BoxLayout(orientation='horizontal', size_hint_x=None, spacing=20)
        humidity_row.bind(minimum_width=humidity_row.setter('width'))

        # Water drop icon
        humidity_icon = Image(
            source='icons/waterdrop.png',
            size_hint=(None, None),
            size=(100, 100)
        )
        humidity_row.add_widget(humidity_icon)

        # Humidity percentage
        humidity_display = '0%' if not self.ctx else f'{int(self.ctx.getHotRoomHumidity())}%'
        self.humidity_label = Label(
            text=humidity_display,
            font_size='120sp',
            color=(0.5, 0.8, 1, 1),
            size_hint_x=None,
            width=300,
            halign='center',
            valign='middle'
        )
        self.humidity_label.bind(size=self.humidity_label.setter('text_size'))
        humidity_row.add_widget(self.humidity_label)

        humidity_container.add_widget(humidity_row)
        humidity_container.add_widget(Label())  # Right spacer

        humidity_outer.add_widget(humidity_container)
        sensor_layout.add_widget(humidity_outer)
        
        layout.add_widget(sensor_layout)

        # Preset Temperature Buttons - 3 columns: [High/Medium stacked], [Target Temp], [OFF]
        preset_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=5, padding=[0, 0])

        # Use FloatLayout as button base
        class ImageButton(ButtonBehavior, FloatLayout):
            pass

        # Column 1: Vertical stack with High on top, Medium on bottom
        preset_stack_outer = BoxLayout(orientation='vertical', size_hint_x=0.15)
        preset_stack_outer.add_widget(Label())  # Top spacer

        preset_stack = BoxLayout(orientation='vertical', spacing=20, size_hint_y=None, height=180)

        # Get preset temperatures from context
        preset_high_temp = self.ctx.getTargetTempPresetHigh() if self.ctx else 200
        preset_medium_temp = self.ctx.getTargetTempPresetMedium() if self.ctx else 180

        presets = [
            ('High', preset_high_temp, 'icons/preset_high.png', 'icons/preset_high.png'),
            ('Medium', preset_medium_temp, 'icons/preset_medium.png', 'icons/preset_medium.png')
        ]

        for idx, (name, temp, passive_img, active_img) in enumerate(presets):
            full_path = os.path.abspath(passive_img)
            print(f"Loading preset '{name}': {passive_img} -> {full_path}, exists: {os.path.exists(passive_img)}")

            btn = ImageButton(size_hint_y=None, height=80)

            if os.path.exists(passive_img):
                # Preset images at 75% size
                btn.img = Image(
                    source=passive_img,
                    fit_mode="contain",
                    size_hint=(1, 1),
                    pos_hint={'center_x': 0.5, 'center_y': 0.5}
                )
                btn.add_widget(btn.img)
            else:
                print(f"Warning: Image not found: {passive_img}")
                btn.img = None

            # Store button data
            btn.preset_name = name
            btn.preset_temp = temp
            btn.passive_img = passive_img
            btn.active_img = active_img
            btn.is_active = False

            btn.bind(on_press=lambda x, i=idx: self.toggle_preset(i))
            self.preset_buttons.append(btn)
            preset_stack.add_widget(btn)

        preset_stack_outer.add_widget(preset_stack)
        preset_stack_outer.add_widget(Label())  # Bottom spacer

        preset_layout.add_widget(preset_stack_outer)

        # Column 2: Target temperature display
        target_temp_wrapper = FloatLayout(size_hint_x=0.5)

        # Create a container with rounded rectangle background
        target_temp_container = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(400, 180),
            pos_hint={'center_x': 0.55, 'center_y': 0.5}
        )

        # Temperature value
        target_temp = self.ctx.getHotRoomTargetTempF() if self.ctx else 190

        self.target_temp_label = Label(
            text=f'{target_temp}°F',
            font_size='135sp',
            bold=True,
            color=(0.85, 1, 0.4, 0.6)  # Lighter greenish-yellow
        )

        # Add rounded rectangle outline to container
        def update_background(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(0.85, 1, 0.4, 0.8)  # Greenish-yellow outline to match text
                Line(
                    rounded_rectangle=(instance.x, instance.y, instance.width, instance.height, 20),
                    width=2
                )

        target_temp_container.bind(pos=update_background, size=update_background)
        update_background(target_temp_container, None)

        target_temp_container.add_widget(self.target_temp_label)

        target_temp_wrapper.add_widget(target_temp_container)
        preset_layout.add_widget(target_temp_wrapper)

        # Column 3: Heater button
        sauna_btn = ImageButton(size_hint_x=0.35)
        self.sauna_passive_img_path = 'icons/passive.png'
        self.sauna_active_img_path = 'icons/active.png'

        sauna_btn.img = Image(
            source=self.sauna_passive_img_path,
            fit_mode="contain",
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        sauna_btn.add_widget(sauna_btn.img)

        sauna_btn.bind(on_press=self.toggle_sauna)
        self.sauna_btn = sauna_btn
        preset_layout.add_widget(sauna_btn)

        layout.add_widget(preset_layout)

        # Temperature slider at the bottom
        slider_container = BoxLayout(orientation='vertical', size_hint_y=0.1, padding=[40, 10], spacing=10)

        # Temperature slider
        initial_temp = self.ctx.getHotRoomTargetTempF() if self.ctx else 190
        max_temp = self.ctx.getHotRoomMaxTempF() if self.ctx else 250
        self.temp_slider = Slider(
            min=100,
            max=max_temp,
            value=initial_temp,
            step=1
        )
        self.temp_slider.bind(value=self.on_slider_change)
        slider_container.add_widget(self.temp_slider)

        layout.add_widget(slider_container)

        self.add_widget(layout)

        # Update sensor readings every 2 seconds
        Clock.schedule_interval(self.update_sensors, 2)
        # Update clock every second
        Clock.schedule_interval(self.update_clock, 1)
        # Initialize heater button state
        self.update_sauna_button()
        # Initialize heater icon state
        if self.ctx:
            if self.ctx.isHeaterOn():
                self.heater_icon.background_normal = 'icons/heater_on.png'
                self.heater_icon.background_down = 'icons/heater_on.png'
            else:
                self.heater_icon.background_normal = 'icons/heater_off.png'
                self.heater_icon.background_down = 'icons/heater_off.png'
    
    def toggle_temperature_unit(self, instance):
        """Toggle between Celsius and Fahrenheit"""
        self.temp_unit = 'C' if self.temp_unit == 'F' else 'F'
        self.update_temperature_display()

    def update_temperature_display(self):
        """Update temperature display based on current unit"""
        if self.ctx:
            temp_f = self.ctx.getHotRoomTempF()
            target_temp_f = self.ctx.getHotRoomTargetTempF()

            if self.temp_unit == 'F':
                self.temp_label.text = f'{int(temp_f)}°F'
                if hasattr(self, 'target_temp_label'):
                    self.target_temp_label.text = f'{int(target_temp_f)}°F'
            else:
                temp_c = (temp_f - 32) * 5 / 9
                self.temp_label.text = f'{int(temp_c)}°C'
                if hasattr(self, 'target_temp_label'):
                    target_temp_c = (target_temp_f - 32) * 5 / 9
                    self.target_temp_label.text = f'{int(target_temp_c)}°C'

    def update_sensors(self, dt):
        """Update sensor readings from SaunaContext"""
        if self.ctx:
            self.update_temperature_display()
            self.humidity_label.text = f'{int(self.ctx.getHotRoomHumidity())}%'
            target_temp = int(self.ctx.getHotRoomTargetTempF())

            # Update slider if value differs (to reflect external changes)
            if hasattr(self, 'temp_slider') and self.temp_slider.value != target_temp:
                self.temp_slider.value = target_temp

            self.update_sauna_button()

            # Update heater icon - switch between heater_on and heater_off
            if self.ctx.isHeaterOn():
                # Heater is on - show heater_on icon
                self.heater_icon.background_normal = 'icons/heater_on.png'
                self.heater_icon.background_down = 'icons/heater_on.png'
            else:
                # Heater is off - show heater_off icon
                self.heater_icon.background_normal = 'icons/heater_off.png'
                self.heater_icon.background_down = 'icons/heater_off.png'

        # Update error icon visibility - show only when there are errors
        if self.errorMgr and self.errorMgr.hasAnyError():
            # Add errors icon if not already in status bar
            if self.errors_icon not in self.status_bar.children:
                self.status_bar.add_widget(self.errors_icon)
        else:
            # Remove errors icon if it's in the status bar
            if self.errors_icon in self.status_bar.children:
                self.status_bar.remove_widget(self.errors_icon)

    def update_clock(self, dt):
        """Update clock display"""
        self.clock_label.text = datetime.now().strftime('%I:%M:%S').lstrip('0')

    def toggle_sauna(self, instance):
        """Toggle sauna heater on/off"""
        if self.ctx:
            if self.ctx.isSaunaOn():
                self.ctx.turnSaunaOff()
                print("Sauna turned OFF")
            else:
                self.ctx.turnSaunaOn()
                print("Sauna turned ON")
            self.update_sauna_button()

    def update_sauna_button(self):
        """Update heater button appearance based on sauna state"""
        if self.ctx and hasattr(self, 'sauna_btn'):
            if self.ctx.isSaunaOn():
                # Sauna is on - use active image
                self.sauna_btn.img.source = self.sauna_active_img_path
            else:
                # Sauna is off - use passive image
                self.sauna_btn.img.source = self.sauna_passive_img_path

    def on_slider_change(self, instance, value):
        """Handle temperature slider value change"""
        if self.ctx:
            self.ctx.setHotRoomTargetTempF(int(value))
            # Update the target temperature display immediately
            if hasattr(self, 'target_temp_label'):
                if self.temp_unit == 'F':
                    self.target_temp_label.text = f'{int(value)}°F'
                else:
                    temp_c = (value - 32) * 5 / 9
                    self.target_temp_label.text = f'{int(temp_c)}°C'
            print(f"Target temperature set to {int(value)}°F")

    def toggle_preset(self, preset_index):
        """Toggle preset button - activate selected, deactivate others"""
        clicked_btn = self.preset_buttons[preset_index]

        # If clicking OFF button or already active preset, turn everything off
        if clicked_btn.preset_temp == 0 or clicked_btn.is_active:
            self.deactivate_all_presets()
            print("All presets turned OFF")
        else:
            # Deactivate all presets first
            self.deactivate_all_presets()

            # Activate clicked preset
            clicked_btn.is_active = True
            if clicked_btn.img:
                clicked_btn.img.source = clicked_btn.active_img
            self.active_preset = preset_index

            # Set target temperature based on preset
            self.ctx.setHotRoomTargetTempF(clicked_btn.preset_temp)
            # Also update the slider to reflect the new temperature
            if hasattr(self, 'temp_slider'):
                self.temp_slider.value = clicked_btn.preset_temp

    # TODO
    def deactivate_all_presets(self):
        pass
        """Deactivate all preset buttons"""
        for btn in self.preset_buttons:
            btn.is_active = False
            if btn.img:
                btn.img.source = btn.passive_img
        self.active_preset = None

    def set_temperature(self, temp):
        """Set target temperature (kept for compatibility)"""
        if temp == 0:
            print("Turning sauna OFF")
        else:
            print(f"Setting temperature to {temp}°C")
    
    def open_fan_screen(self, instance):
        self.manager.current = 'fan'

    def open_wifi_screen(self, instance):
        self.manager.current = 'wifi'

    def open_settings_screen(self, instance):
        self.manager.current = 'settings'

    def open_errors_screen(self, instance):
        """Open errors screen to display error details"""
        self.manager.current = 'errors'

class FanScreen(Screen):
    """Fan control screen"""
    def __init__(self, ctx: SaunaContext=None, sd: SaunaDevices=None, **kwargs):
        super().__init__(**kwargs)
        self.ctx = ctx
        self.sd = sd
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Header
        header = BoxLayout(size_hint_y=0.15)
        header.add_widget(Label(text='Fan Configuration', font_size='30sp', bold=True))
        layout.add_widget(header)
        
        # Fan controls - top third of screen
        fan_layout = BoxLayout(orientation='vertical', spacing=60, size_hint_y=0.33, padding=[0, 40, 0, 0])

        # Left Fan
        left_fan_box = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=45)
        left_fan_box.add_widget(Label(size_hint_x=0.15))  # Left spacer - 15% from left
        self.left_fan_btn = Button(
            size_hint=(None, None),
            size=(45, 45),
            background_normal='icons/checkbox-unchecked.png',
            background_down='icons/checkbox-unchecked.png',
            border=(0, 0, 0, 0)
        )
        # Load initial state from context
        self.left_fan_btn.active = self.ctx.getLeftFanOnStatus()
        if self.left_fan_btn.active:
            self.left_fan_btn.background_normal = 'icons/checkbox-checked.png'
            self.left_fan_btn.background_down = 'icons/checkbox-checked.png'
        self.left_fan_btn.bind(on_press=self.toggle_left_fan)
        left_fan_box.add_widget(self.left_fan_btn)

        # Make label clickable
        class ClickableLabel(ButtonBehavior, Label):
            pass

        left_label = ClickableLabel(text='Left Fan', font_size='30sp', bold=True, halign='left', size_hint_x=1)
        left_label.text_size = (left_label.width, None)
        left_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
        left_label.bind(on_press=self.toggle_left_fan)
        left_fan_box.add_widget(left_label)
        fan_layout.add_widget(left_fan_box)

        # Right Fan
        right_fan_box = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=45)
        right_fan_box.add_widget(Label(size_hint_x=0.15))  # Left spacer - 15% from left
        self.right_fan_btn = Button(
            size_hint=(None, None),
            size=(45, 45),
            background_normal='icons/checkbox-unchecked.png',
            background_down='icons/checkbox-unchecked.png',
            border=(0, 0, 0, 0)
        )
        # Load initial state from context
        if self.ctx:
            self.right_fan_btn.active = self.ctx.getRightFanOnStatus()
            if self.right_fan_btn.active:
                self.right_fan_btn.background_normal = 'icons/checkbox-checked.png'
                self.right_fan_btn.background_down = 'icons/checkbox-checked.png'
        else:
            self.right_fan_btn.active = False
        self.right_fan_btn.bind(on_press=self.toggle_right_fan)
        right_fan_box.add_widget(self.right_fan_btn)
        right_label = ClickableLabel(text='Right Fan', font_size='30sp', bold=True, halign='left', size_hint_x=1)
        right_label.text_size = (right_label.width, None)
        right_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
        right_label.bind(on_press=self.toggle_right_fan)
        right_fan_box.add_widget(right_label)
        fan_layout.add_widget(right_fan_box)

        layout.add_widget(fan_layout)

        # Fan Speed Control
        speed_layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=0.20, padding=[60, 20, 60, 0])

        speed_label = Label(
            text='Fan Speed',
            font_size='30sp',
            bold=True,
            size_hint_y=0.3
        )
        speed_layout.add_widget(speed_label)

        # Fan speed slider
        initial_speed = self.ctx.getFanSpeedPct() if self.ctx else 100
        self.speed_slider = Slider(
            min=0,
            max=100,
            value=initial_speed,
            step=1,
            size_hint_y=0.4
        )
        self.speed_slider.bind(value=self.on_speed_change)
        speed_layout.add_widget(self.speed_slider)

        # Speed value display
        self.speed_value_label = Label(
            text=f'{int(initial_speed)}%',
            font_size='24sp',
            size_hint_y=0.3
        )
        speed_layout.add_widget(self.speed_value_label)

        layout.add_widget(speed_layout)

        # Spacer to push OK button up from bottom
        layout.add_widget(Label(size_hint_y=0.25))

        # OK button
        ok_btn = Button(
            text='Ok',
            size_hint=(None, None),
            size=(200, 60),
            pos_hint={'center_x': 0.5},
            font_size='20sp',
            background_color=(0.5, 0.8, 1.0, 1)
        )
        ok_btn.bind(on_press=self.go_back)
        layout.add_widget(ok_btn)

        # Small bottom spacer
        layout.add_widget(Label(size_hint_y=0.07))
        
        self.add_widget(layout)

    def toggle_left_fan(self, instance):
        """Toggle left fan button state"""
        self.left_fan_btn.active = not self.left_fan_btn.active
        if self.left_fan_btn.active:
            self.left_fan_btn.background_normal = 'icons/checkbox-checked.png'
            self.left_fan_btn.background_down = 'icons/checkbox-checked.png'
        else:
            self.left_fan_btn.background_normal = 'icons/checkbox-unchecked.png'
            self.left_fan_btn.background_down = 'icons/checkbox-unchecked.png'
        # Save to context
        if self.ctx:
            self.ctx.setLeftFanOnStatus(self.left_fan_btn.active)
            self.sd.turnLeftFanOnOff(self.left_fan_btn.active)
        print(f"Left Fan: {self.left_fan_btn.active}")

    def toggle_right_fan(self, instance):
        """Toggle right fan button state"""
        self.right_fan_btn.active = not self.right_fan_btn.active
        if self.right_fan_btn.active:
            self.right_fan_btn.background_normal = 'icons/checkbox-checked.png'
            self.right_fan_btn.background_down = 'icons/checkbox-checked.png'
        else:
            self.right_fan_btn.background_normal = 'icons/checkbox-unchecked.png'
            self.right_fan_btn.background_down = 'icons/checkbox-unchecked.png'
        # Save to context
        if self.ctx:
            self.ctx.setRightFanOnStatus(self.right_fan_btn.active)
            self.sd.turnRightFanOnOff(self.right_fan_btn.active)
        print(f"Right Fan: {self.right_fan_btn.active}")

    def on_speed_change(self, instance, value):
        """Handle fan speed slider change"""
        speed_pct = int(value)
        self.speed_value_label.text = f'{speed_pct}%'
        if self.ctx and self.sd:
            self.ctx.setFanSpeedPct(speed_pct)
            self.sd.setFanSpeed(speed_pct)
        print(f"Fan Speed: {speed_pct}%")

    def go_back(self, instance):
        # Save fan states here if needed
        print(f"Left Fan: {self.left_fan_btn.active}, Right Fan: {self.right_fan_btn.active}")
        self.manager.current = 'main'

class WiFiScreen(Screen):
    """WiFi configuration screen"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Header
        header = BoxLayout(size_hint_y=0.1)
        back_btn = Button(text='← Back', size_hint_x=0.3, font_size='20sp')
        back_btn.bind(on_press=self.go_back)
        header.add_widget(back_btn)
        header.add_widget(Label(text='WiFi Configuration', font_size='30sp', bold=True))
        layout.add_widget(header)
        
        # WiFi settings
        settings_layout = BoxLayout(orientation='vertical', spacing=20, padding=20)
        
        # SSID
        ssid_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        ssid_box.add_widget(Label(text='SSID:', font_size='20sp', size_hint_x=0.3))
        self.ssid_input = TextInput(multiline=False, font_size='20sp')
        ssid_box.add_widget(self.ssid_input)
        settings_layout.add_widget(ssid_box)
        
        # Password
        pwd_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        pwd_box.add_widget(Label(text='Password:', font_size='20sp', size_hint_x=0.3))
        self.pwd_input = TextInput(multiline=False, password=True, font_size='20sp')
        pwd_box.add_widget(self.pwd_input)
        settings_layout.add_widget(pwd_box)
        
        # Connect button
        connect_btn = Button(
            text='Connect',
            size_hint_y=None,
            height=80,
            font_size='24sp',
            background_color=(0.2, 0.7, 0.3, 1)
        )
        connect_btn.bind(on_press=self.connect_wifi)
        settings_layout.add_widget(connect_btn)
        
        # Status
        self.status_label = Label(text='', font_size='18sp', color=(1, 1, 0, 1))
        settings_layout.add_widget(self.status_label)
        
        layout.add_widget(settings_layout)
        self.add_widget(layout)
    
    def connect_wifi(self, instance):
        ssid = self.ssid_input.text
        self.status_label.text = f'Connecting to {ssid}...'
        # Implement actual WiFi connection here
        print(f"Connecting to WiFi: {ssid}")
    
    def go_back(self, instance):
        self.manager.current = 'main'

class ErrorsScreen(Screen):
    """Errors display screen"""
    def __init__(self, errorMgr=None, **kwargs):
        super().__init__(**kwargs)
        self.errorMgr = errorMgr

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Header
        header = BoxLayout(size_hint_y=0.1)
        header.add_widget(Label(text='System Errors', font_size='30sp', bold=True))
        layout.add_widget(header)

        # Errors list
        scroll_view = ScrollView(size_hint=(1, 0.8))
        self.errors_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, padding=10)
        self.errors_layout.bind(minimum_height=self.errors_layout.setter('height'))

        scroll_view.add_widget(self.errors_layout)
        layout.add_widget(scroll_view)

        # Buttons - centered
        button_container = BoxLayout(size_hint_y=0.1)
        button_container.add_widget(Label())  # Left spacer

        button_layout = BoxLayout(size_hint_x=None, spacing=20)
        button_layout.bind(minimum_width=button_layout.setter('width'))

        # Ok button
        ok_btn = Button(
            text='Ok',
            size_hint=(None, None),
            size=(200, 60),
            font_size='20sp',
            background_color=(0.5, 0.8, 1.0, 1)
        )
        ok_btn.bind(on_press=self.go_back)
        button_layout.add_widget(ok_btn)

        # Clear Errors button
        clear_btn = Button(
            text='Clear Errors',
            size_hint=(None, None),
            size=(200, 60),
            font_size='20sp',
            background_color=(1.0, 0.5, 0.5, 1)
        )
        clear_btn.bind(on_press=self.clear_errors)
        button_layout.add_widget(clear_btn)

        button_container.add_widget(button_layout)
        button_container.add_widget(Label())  # Right spacer

        layout.add_widget(button_container)

        self.add_widget(layout)

    def on_enter(self):
        """Called when screen is entered - refresh error list"""
        self.refresh_errors()

    def refresh_errors(self):
        """Update the errors display"""
        self.errors_layout.clear_widgets()

        if not self.errorMgr:
            error_label = Label(
                text='Error Manager not available',
                font_size='18sp',
                size_hint_y=None,
                height=40,
                color=(0.7, 0.7, 0.7, 1)
            )
            self.errors_layout.add_widget(error_label)
            return

        has_errors = False

        # Check for critical error
        if self.errorMgr._criticalErrorMessage:
            has_errors = True
            self.add_error_item('CRITICAL ERROR', self.errorMgr._criticalErrorMessage)

        # Check for relay module error
        if self.errorMgr._relayModuleErrorMessage:
            has_errors = True
            self.add_error_item('Relay Module', self.errorMgr._relayModuleErrorMessage)

        # Check for fan module error
        if self.errorMgr._fanModuleErrorMessage:
            has_errors = True
            self.add_error_item('Fan Module', self.errorMgr._fanModuleErrorMessage)

        # Check for sensor module error
        if self.errorMgr._sensorModuleErrorMessage:
            has_errors = True
            self.add_error_item('Sensor Module', self.errorMgr._sensorModuleErrorMessage)

        # Check for heater error
        if self.errorMgr._heaterErrorMessage:
            has_errors = True
            self.add_error_item('Heater', self.errorMgr._heaterErrorMessage)

        # Check for Modbus exception
        if self.errorMgr._modbusException:
            has_errors = True
            self.add_error_item('Modbus Communication', str(self.errorMgr._modbusException))

        # If no errors, show message
        if not has_errors:
            no_error_label = Label(
                text='No active errors',
                font_size='20sp',
                size_hint_y=None,
                height=60,
                color=(0.2, 0.8, 0.2, 1)
            )
            self.errors_layout.add_widget(no_error_label)

    def add_error_item(self, category, message):
        """Add an error item to the display"""
        error_box = BoxLayout(orientation='vertical', size_hint_y=None, height=80, padding=5)

        # Category label
        category_label = Label(
            text=f'[{category}]',
            font_size='18sp',
            bold=True,
            size_hint_y=None,
            height=30,
            color=(1, 0.3, 0.3, 1),
            halign='left',
            valign='middle'
        )
        category_label.bind(size=category_label.setter('text_size'))
        error_box.add_widget(category_label)

        # Message label
        message_label = Label(
            text=message,
            font_size='16sp',
            size_hint_y=None,
            height=50,
            color=(1, 1, 1, 1),
            halign='left',
            valign='top'
        )
        message_label.bind(size=message_label.setter('text_size'))
        error_box.add_widget(message_label)

        self.errors_layout.add_widget(error_box)

    def clear_errors(self, instance):
        """Clear all errors"""
        if self.errorMgr:
            self.errorMgr.eraseCriticalError()
            self.errorMgr.eraseRelayModuleError()
            self.errorMgr.eraseFanModuleError()
            self.errorMgr.eraseSensorModuleError()
            self.errorMgr.eraseHeaterError()
            self.errorMgr.eraseModbusError()
            print("All errors cleared")
        self.refresh_errors()

    def go_back(self, instance):
        self.manager.current = 'main'

class SaunaControlApp(App):
    """Main application class"""
    def __init__(self, ctx=None, sc=None, sd=None, errorMgr=None, **kwargs):
        super().__init__(**kwargs)
        self.ctx = ctx
        self.sc = sc
        self.sd = sd
        self.errorMgr = errorMgr

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main', ctx=self.ctx, errorMgr=self.errorMgr))
        sm.add_widget(FanScreen(name='fan', ctx=self.ctx, sd=self.sd))
        sm.add_widget(WiFiScreen(name='wifi'))
        sm.add_widget(SettingsScreen(name='settings', ctx=self.ctx, sc=self.sc))
        sm.add_widget(ErrorsScreen(name='errors', errorMgr=self.errorMgr))
        return sm