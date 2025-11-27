import os
import socket
from datetime import datetime
from kivy.config import Config
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from ui.SaunaUISettingsScreen import SaunaUISettingsScreen
from ui.SaunaUIFanScreen import SaunaUIFanScreen
from ui.SaunaUIWiFiScreen import SaunaUIWiFiScreen
from ui.SaunaUIErrorsScreen import SaunaUIErrorsScreen
from core.SaunaContext import SaunaContext
from core.SaunaErrorMgr import SaunaErrorMgr

# Set window size for Raspberry Pi touchscreen (portrait)


# Custom status icon button with image
class StatusIcon(Button):

    def __init__(self, icon_image, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (50, 50)  # Smaller size
        self.background_normal = icon_image
        self.background_down = icon_image
        self.border = (0, 0, 0, 0)


class SaunaUIMainScreen(Screen):

    def __init__(self, ctx: SaunaContext=None, errorMgr: SaunaErrorMgr=None, **kwargs):
        super().__init__(**kwargs)

        Window.size = (ctx.getScreenWidth(), ctx.getScreenHeight())
        Window.rotation = ctx.getScreenRotation()

        # Set deep dark grey background
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # Deep dark grey
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Set kivy log level
        Config.set('kivy', 'log_level', 'warning')
        Config.write()

        # Dependencies
        self.ctx = ctx
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

        self.light_icon = StatusIcon('icons/light_off.png')
        self.light_icon.bind(on_press=self.toggle_light_always_on)
        self.status_bar.add_widget(self.light_icon)

        self.heater_icon = StatusIcon('icons/heater_off.png')
        self.status_bar.add_widget(self.heater_icon)

        self.errors_icon = StatusIcon('icons/errors.png')
        self.errors_icon.bind(on_press=self.open_errors_screen)

        layout.add_widget(self.status_bar)

        # Spacer to push content down
        layout.add_widget(Label(size_hint_y=0.05))

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
        sensor_layout = BoxLayout(orientation='vertical', size_hint_y=0.35, spacing=5)

        # Large temperature display - takes full row - touchable to toggle C/F
        temp_display = '0°F' if not self.ctx else f'{int(self.ctx.getHotRoomTempF())}°F'

        class TouchableLabel(ButtonBehavior, Label):
            pass

        self.temp_label = TouchableLabel(
            text=temp_display,
            font_size='240sp',
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
        humidity_outer.add_widget(Label(size_hint_y=0.0))

        humidity_container = BoxLayout(orientation='horizontal', size_hint_y=1.0)
        humidity_container.add_widget(Label())  # Left spacer

        humidity_row = BoxLayout(orientation='horizontal', size_hint_x=None, spacing=0)
        humidity_row.bind(minimum_width=humidity_row.setter('width'))

        # Water drop icon
        humidity_icon = Image(
            source='icons/waterdrop.png',
            size_hint=(None, None),
            size=(70, 70),
            pos_hint={'center_y': 0.5}
        )
        humidity_row.add_widget(humidity_icon)

        # Humidity percentage
        humidity_display = '0%' if not self.ctx else f'{int(self.ctx.getHotRoomHumidity())}%'
        self.humidity_label = Label(
            text=humidity_display,
            font_size='90sp',
            color=(0.5, 0.8, 1, 1),
            size_hint_x=None,
            width=250,
            halign='center',
            valign='center'
        )
        self.humidity_label.bind(size=self.humidity_label.setter('text_size'))
        humidity_row.add_widget(self.humidity_label)

        humidity_container.add_widget(humidity_row)
        humidity_container.add_widget(Label())  # Right spacer

        humidity_outer.add_widget(humidity_container)
        sensor_layout.add_widget(humidity_outer)
        
        layout.add_widget(sensor_layout)

        # Preset Temperature Buttons - 3 columns: [High/Medium stacked], [Target Temp], [Sauna On/Off]
        preset_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=5, padding=[0, 0])

        # Use FloatLayout as button base
        class ImageButton(ButtonBehavior, FloatLayout):
            pass

        # Column 1: Vertical stack with High on top, Medium on bottom
        preset_stack_outer = BoxLayout(orientation='vertical', size_hint_x=0.15)
        preset_stack_outer.add_widget(Label())  # Top spacer

        preset_stack = BoxLayout(orientation='vertical', spacing=20, size_hint_y=None, height=180)

        # Get preset temperatures from context
        preset_high_temp = self.ctx.getTargetTempPresetHigh()
        preset_medium_temp = self.ctx.getTargetTempPresetMedium()

        presets = [
            ('High', preset_high_temp, 'icons/preset_high.png', 'icons/preset_high.png'),
            ('Medium', preset_medium_temp, 'icons/preset_medium.png', 'icons/preset_medium.png')
        ]

        for idx, (name, temp, passive_img, active_img) in enumerate(presets):
            full_path = os.path.abspath(passive_img)

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
            pos_hint={'center_x': 0.50, 'center_y': 0.5}
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

        # Column 3: Sauna button
        sauna_btn = ImageButton(size_hint_x=0.23)
        self.sauna_passive_img_path = 'icons/sauna_off.png'
        self.sauna_active_img_path = 'icons/sauna_on.png'

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
        Clock.schedule_interval(self.update_sensors, 1)
        # Update clock every second
        Clock.schedule_interval(self.update_clock, 1)
        # Initialize heater button state
        self.update_sauna_button()
        # Initialize light icon state
        if self.ctx.isHotRoomLightOn():
            self.light_icon.background_normal = 'icons/light_on.png'
            self.light_icon.background_down = 'icons/light_on.png'
        else:
            self.light_icon.background_normal = 'icons/light_off.png'
            self.light_icon.background_down = 'icons/light_off.png'
        # Initialize heater icon state
        if self.errorMgr and self.errorMgr._heaterErrorMessage:
            self.heater_icon.background_normal = 'icons/heater_error.png'
            self.heater_icon.background_down = 'icons/heater_error.png'
        elif self.ctx.isHeaterOn():
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

    def is_wifi_connected(self):
        """Check if WiFi/network is connected"""
        try:
            # Try to create a socket connection to Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            return True
        except OSError:
            return False

    def update_sensors(self, dt):
        self.update_temperature_display()
        self.humidity_label.text = f'{int(self.ctx.getHotRoomHumidity())}%'
        target_temp = int(self.ctx.getHotRoomTargetTempF())

        # Update slider if value differs (to reflect external changes)
        if hasattr(self, 'temp_slider') and self.temp_slider.value != target_temp:
            self.temp_slider.value = target_temp

        self.update_sauna_button()

        # Update light icon - switch between light_on and light_off
        if self.ctx.isHotRoomLightOn():
            self.light_icon.background_normal = 'icons/light_on.png'
            self.light_icon.background_down = 'icons/light_on.png'
        else:
            self.light_icon.background_normal = 'icons/light_off.png'
            self.light_icon.background_down = 'icons/light_off.png'

        # Update heater icon - check for errors first, then switch between heater_on and heater_off
        if self.errorMgr and self.errorMgr._heaterErrorMessage:
            # Heater has an error - show heater_error icon
            self.heater_icon.background_normal = 'icons/heater_error.png'
            self.heater_icon.background_down = 'icons/heater_error.png'
        elif self.ctx.isHeaterOn():
            # Heater is on - show heater_on icon
            self.heater_icon.background_normal = 'icons/heater_on.png'
            self.heater_icon.background_down = 'icons/heater_on.png'
        else:
            # Heater is off - show heater_off icon
            self.heater_icon.background_normal = 'icons/heater_off.png'
            self.heater_icon.background_down = 'icons/heater_off.png'

        # Update WiFi icon based on connection status
        if self.is_wifi_connected():
            self.wifi_icon.background_normal = 'icons/wifi.png'
            self.wifi_icon.background_down = 'icons/wifi.png'
        else:
            self.wifi_icon.background_normal = 'icons/wifi_nc.png'
            self.wifi_icon.background_down = 'icons/wifi_nc.png'

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
        self.ctx.turnSaunaOnOff(self.ctx.isSaunaOff())
        self.update_sauna_button()

    def update_sauna_button(self):
        """Update heater button appearance based on sauna state"""
        if self.ctx.isSaunaOn():
            self.sauna_btn.img.source = self.sauna_active_img_path
        else:
            self.sauna_btn.img.source = self.sauna_passive_img_path

    def on_slider_change(self, instance, value):
        """Handle temperature slider value change"""
        self.ctx.setHotRoomTargetTempF(int(value))
        self.update_temperature_display()

    def toggle_preset(self, preset_index):
        """Toggle preset button - activate selected, deactivate others"""
        clicked_btn = self.preset_buttons[preset_index]

        # Activate clicked preset
        clicked_btn.is_active = True
        if clicked_btn.img:
            clicked_btn.img.source = clicked_btn.active_img
        self.active_preset = preset_index

        # Set target temperature based on preset
        self.ctx.setHotRoomTargetTempF(clicked_btn.preset_temp)
        # Also update the slider to reflect the new temperature
        self.temp_slider.value = clicked_btn.preset_temp

    def set_temperature(self, temp):
        """Set target temperature (kept for compatibility)"""
        if temp == 0:
            print("Turning sauna OFF")
        else:
            print(f"Setting temperature to {temp}°C")

    def toggle_light_always_on(self, instance):
        self.ctx.setHotRoomLightAlwaysOn(not self.ctx.getHotRoomLightAlwaysOn())

    def open_fan_screen(self, instance):
        self.manager.current = 'fan'

    def open_wifi_screen(self, instance):
        self.manager.current = 'wifi'

    def open_settings_screen(self, instance):
        self.manager.current = 'settings'

    def open_errors_screen(self, instance):
        self.manager.current = 'errors'

    def _update_bg(self, instance, value):
        """Update background rectangle size and position"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class SaunaControlApp(App):

    def __init__(self, ctx=None, errorMgr=None, **kwargs):
        super().__init__(**kwargs)
        self.ctx = ctx
        self.errorMgr = errorMgr

    def build(self):
        sm = ScreenManager()
        sm.add_widget(SaunaUIMainScreen(name='main', ctx=self.ctx, errorMgr=self.errorMgr))
        sm.add_widget(SaunaUIFanScreen(name='fan', ctx=self.ctx))
        sm.add_widget(SaunaUIWiFiScreen(name='wifi'))
        sm.add_widget(SaunaUISettingsScreen(name='settings', ctx=self.ctx))
        sm.add_widget(SaunaUIErrorsScreen(name='errors', errorMgr=self.errorMgr))
        return sm