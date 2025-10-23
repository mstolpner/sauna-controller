import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
import random
import os

# Set window size for Raspberry Pi touchscreen (portrait)
Window.size = (800, 1280)
Window.rotation = 90

class StatusIcon(Button):
    """Custom status icon button with image"""
    def __init__(self, icon_image, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (80, 80)
        
        # Check if image exists, otherwise show text fallback
        full_path = os.path.abspath(icon_image)
        print(f"Loading icon: {icon_image} -> {full_path}, exists: {os.path.exists(icon_image)}")
        
        if os.path.exists(icon_image):
            self.background_normal = icon_image
            self.background_down = icon_image
            self.border = (0, 0, 0, 0)
        else:
            print(f"Warning: Image not found: {icon_image}")
            self.background_normal = ''
            self.background_color = (0.2, 0.2, 0.2, 1)
            # Fallback to text
            self.text = os.path.basename(icon_image).replace('.png', '')
            self.font_size = '14sp'

class MainScreen(Screen):
    """Main sauna control screen"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.temp = 20.0
        self.humidity = 45.0
        self.active_preset = None
        self.preset_buttons = []
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Top status bar
        status_bar = BoxLayout(size_hint_y=0.15, spacing=5)
        
        self.fan_icon = StatusIcon('icons/fan.png')
        self.fan_icon.bind(on_press=self.open_fan_screen)
        status_bar.add_widget(self.fan_icon)
        
        self.wifi_icon = StatusIcon('icons/wifi.png')
        self.wifi_icon.bind(on_press=self.open_wifi_screen)
        status_bar.add_widget(self.wifi_icon)
        
        self.heater_icon = StatusIcon('icons/heater.png')
        self.heater_icon.bind(on_press=self.toggle_heater)
        status_bar.add_widget(self.heater_icon)
        
        self.settings_icon = StatusIcon('icons/settings.png')
        self.settings_icon.bind(on_press=self.open_settings_screen)
        status_bar.add_widget(self.settings_icon)
        
        status_bar.add_widget(Label())  # Spacer
        
        layout.add_widget(status_bar)
        
        # Temperature and Humidity Display
        sensor_layout = BoxLayout(orientation='vertical', size_hint_y=0.35, spacing=5)
        
        # Large temperature display - takes full row
        self.temp_label = Label(
            text=f'{int(self.temp)}°F',
            font_size='120sp',
            bold=True,
            color=(1, 0.5, 0, 1),
            size_hint_y=0.75
        )
        sensor_layout.add_widget(self.temp_label)
        
        # Smaller humidity display
        self.humidity_label = Label(
            text=f'Humidity: {int(self.humidity)}%',
            font_size='40sp',
            color=(0.5, 0.8, 1, 1),
            size_hint_y=0.25
        )
        sensor_layout.add_widget(self.humidity_label)
        
        layout.add_widget(sensor_layout)
        
        # Preset Temperature Buttons - 4 buttons in one row
        preset_layout = GridLayout(cols=4, rows=1, size_hint_y=0.5, spacing=10)
        
        presets = [
            ('Low', 140, 'presets/passive.png', 'presets/active.png'),
            ('Medium', 160, 'presets/passive.png', 'presets/active.png'),
            ('High', 180, 'presets/passive.png', 'presets/active.png'),
            ('OFF', 0, 'presets/off_passive.png', 'presets/off_active.png')
        ]
        
        for idx, (name, temp, passive_img, active_img) in enumerate(presets):
            # Create button container
            full_path = os.path.abspath(passive_img)
            print(f"Loading preset '{name}': {passive_img} -> {full_path}, exists: {os.path.exists(passive_img)}")
            
            # Use FloatLayout as button base
            from kivy.uix.floatlayout import FloatLayout
            from kivy.uix.behaviors import ButtonBehavior
            
            class ImageButton(ButtonBehavior, FloatLayout):
                pass
            
            btn = ImageButton()
            
            if os.path.exists(passive_img):
                # Add image that maintains aspect ratio
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
            
            # Add temperature label overlay (only for temp presets, not OFF)
            if temp > 0:
                temp_label = Label(
                    text=f'{temp}°C',
                    font_size='32sp',
                    bold=True,
                    color=(1, 1, 1, 1),
                    size_hint=(None, None),
                    pos_hint={'center_x': 0.5, 'center_y': 0.5}
                )
                btn.add_widget(temp_label)
            
            btn.bind(on_press=lambda x, i=idx: self.toggle_preset(i))
            self.preset_buttons.append(btn)
            preset_layout.add_widget(btn)
        
        layout.add_widget(preset_layout)
        
        self.add_widget(layout)
        
        # Update sensor readings every 2 seconds
        Clock.schedule_interval(self.update_sensors, 2)
    
    def update_sensors(self, dt):
        """Simulate sensor readings"""
        # In real implementation, read from actual sensors
        self.temp += random.uniform(-0.5, 0.5)
        self.humidity += random.uniform(-1, 1)
        self.temp = max(15, min(100, self.temp))
        self.humidity = max(20, min(80, self.humidity))
        
        self.temp_label.text = f'{int(self.temp)}°F'
        self.humidity_label.text = f'Humidity: {int(self.humidity)}%'
    
    def toggle_preset(self, preset_index):
        """Toggle preset button - activate selected, deactivate others"""
        clicked_btn = self.preset_buttons[preset_index]
        
        # If clicking OFF button or already active preset, turn everything off
        if clicked_btn.preset_temp == 0 or clicked_btn.is_active:
            self.deactivate_all_presets()
            self.heater_icon.background_color = (0.2, 0.2, 0.2, 1)
            print("All presets turned OFF")
        else:
            # Deactivate all presets first
            self.deactivate_all_presets()
            
            # Activate clicked preset
            clicked_btn.is_active = True
            if clicked_btn.img:
                clicked_btn.img.source = clicked_btn.active_img
            self.active_preset = preset_index
            self.heater_icon.background_color = (1, 0.3, 0, 1)
            print(f"Setting temperature to {clicked_btn.preset_temp}°C ({clicked_btn.preset_name})")
    
    def deactivate_all_presets(self):
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
            self.heater_icon.background_color = (0.2, 0.2, 0.2, 1)
        else:
            print(f"Setting temperature to {temp}°C")
            self.heater_icon.background_color = (1, 0.3, 0, 1)
    
    def toggle_heater(self, instance):
        """Toggle heater status"""
        print("Heater status toggled")
    
    def open_fan_screen(self, instance):
        self.manager.current = 'fan'
    
    def open_wifi_screen(self, instance):
        self.manager.current = 'wifi'
    
    def open_settings_screen(self, instance):
        self.manager.current = 'settings'

class FanScreen(Screen):
    """Fan control screen"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Header
        header = BoxLayout(size_hint_y=0.15)
        header.add_widget(Label(text='Fan Control', font_size='30sp', bold=True))
        layout.add_widget(header)
        
        # Fan controls - centered in middle
        fan_layout = BoxLayout(orientation='vertical', spacing=30, size_hint_y=0.7)
        
        # Left Fan
        left_fan_box = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=100)
        left_fan_box.add_widget(Label(text='Left Fan', font_size='28sp', bold=True, halign='right'))
        self.left_fan_checkbox = CheckBox(size_hint=(None, None), size=(80, 80), active=False)
        left_fan_box.add_widget(self.left_fan_checkbox)
        left_fan_box.add_widget(Label())  # Spacer
        fan_layout.add_widget(left_fan_box)
        
        # Right Fan
        right_fan_box = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=100)
        right_fan_box.add_widget(Label(text='Right Fan', font_size='28sp', bold=True, halign='right'))
        self.right_fan_checkbox = CheckBox(size_hint=(None, None), size=(80, 80), active=False)
        right_fan_box.add_widget(self.right_fan_checkbox)
        right_fan_box.add_widget(Label())  # Spacer
        fan_layout.add_widget(right_fan_box)
        
        layout.add_widget(fan_layout)
        
        # OK button at bottom
        ok_btn = Button(
            text='OK',
            size_hint_y=0.15,
            font_size='28sp',
            bold=True,
            background_color=(0.2, 0.7, 0.3, 1)
        )
        ok_btn.bind(on_press=self.go_back)
        layout.add_widget(ok_btn)
        
        self.add_widget(layout)
    
    def go_back(self, instance):
        # Save fan states here if needed
        print(f"Left Fan: {self.left_fan_checkbox.active}, Right Fan: {self.right_fan_checkbox.active}")
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

class SettingsScreen(Screen):
    """Settings configuration screen"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Header
        header = BoxLayout(size_hint_y=0.1)
        back_btn = Button(text='← Back', size_hint_x=0.3, font_size='20sp')
        back_btn.bind(on_press=self.go_back)
        header.add_widget(back_btn)
        header.add_widget(Label(text='Settings', font_size='30sp', bold=True))
        layout.add_widget(header)
        
        # Settings list
        settings_layout = GridLayout(cols=1, spacing=10, size_hint_y=0.9)
        
        settings = [
            'Max Temperature Limit',
            'Auto Shutdown Timer',
            'Temperature Units (°C/°F)',
            'Screen Brightness',
            'Sound Alerts',
            'Safety Timeout',
            'Humidity Alert Level',
            'Night Mode',
            'Language',
            'Factory Reset'
        ]
        
        for setting in settings:
            btn = Button(
                text=setting,
                size_hint_y=None,
                height=60,
                font_size='18sp',
                background_color=(0.3, 0.3, 0.4, 1)
            )
            btn.bind(on_press=lambda x, s=setting: self.open_setting(s))
            settings_layout.add_widget(btn)
        
        layout.add_widget(settings_layout)
        self.add_widget(layout)
    
    def open_setting(self, setting_name):
        print(f"Opening setting: {setting_name}")
        # Implement individual setting screens as needed
    
    def go_back(self, instance):
        self.manager.current = 'main'

class SaunaControlApp(App):
    """Main application class"""
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(FanScreen(name='fan'))
        sm.add_widget(WiFiScreen(name='wifi'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm

if __name__ == '__main__':
    SaunaControlApp().run()