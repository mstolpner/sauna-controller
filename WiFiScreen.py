from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput


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
