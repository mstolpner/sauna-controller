import subprocess
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput


class SaunaUIWiFiScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Header
        header = BoxLayout(size_hint_y=0.1)
        header.add_widget(Label(text='WiFi Configuration', font_size='30sp', bold=True))
        layout.add_widget(header)

        # WiFi settings
        settings_layout = BoxLayout(orientation='vertical', spacing=20, padding=20)

        # SSID
        ssid_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        ssid_box.add_widget(Label(text='SSID:', font_size='24sp', size_hint_x=0.3))
        self.ssid_input = TextInput(multiline=False, font_size='32sp')
        ssid_box.add_widget(self.ssid_input)
        settings_layout.add_widget(ssid_box)

        # Password
        pwd_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        pwd_box.add_widget(Label(text='Password:', font_size='24sp', size_hint_x=0.3))
        self.pwd_input = TextInput(multiline=False, password=True, font_size='32sp')
        pwd_box.add_widget(self.pwd_input)
        settings_layout.add_widget(pwd_box)

        # Status
        self.status_label = Label(text='', font_size='32sp', color=(0, 1, 0, 1), size_hint_y=None, height=80)
        settings_layout.add_widget(self.status_label)

        # Spacer to push buttons down
        settings_layout.add_widget(Label())

        # Buttons row
        buttons_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=15)

        # Left spacer to center buttons
        buttons_row.add_widget(Label())

        # Connect button
        connect_btn = Button(
            text='Connect',
            font_size='24sp',
            background_color=(0.2, 0.7, 0.3, 1),
            size_hint_x=None,
            width=150
        )
        connect_btn.bind(on_press=self.connect_wifi)
        buttons_row.add_widget(connect_btn)

        # Ok button
        ok_btn = Button(
            text='OK',
            font_size='24sp',
            background_color=(0.3, 0.5, 0.8, 1),
            size_hint_x=None,
            width=150
        )
        ok_btn.bind(on_press=self.go_back)
        buttons_row.add_widget(ok_btn)

        # Right spacer to center buttons
        buttons_row.add_widget(Label())
        settings_layout.add_widget(buttons_row)

        # Small spacer at bottom
        settings_layout.add_widget(Label(size_hint_y=None, height=20))
        layout.add_widget(settings_layout)

        self.add_widget(layout)

    def connect_wifi(self, instance):
        ssid = self.ssid_input.text
        password = self.pwd_input
        self.status_label.text = f'Connecting to {ssid}...'
        # Set WiFi using NetworkManager
        try:
            # Check if connection already exists
            check_cmd = f"nmcli connection show '{ssid}'"
            result = subprocess.run(check_cmd, shell=True, capture_output=True)
            if result.returncode == 0:
                # Connection exists, modify it
                cmd = f"nmcli connection modify '{ssid}' wifi-sec.key-mgmt wpa-psk wifi-sec.psk '{password}'"
                subprocess.run(cmd, shell=True, check=True)
            else:
                # Create new connection
                cmd = f"nmcli device wifi connect '{ssid}' password '{password}'"
                subprocess.run(cmd, shell=True, check=True)

            # Activate the connection
            activate_cmd = f"nmcli connection up '{ssid}'"
            subprocess.run(activate_cmd, shell=True, check=True)
            self.status_label.color((0, 1, 0, 1))
            self.status_label.text = f'Connected to {ssid}...'

        except subprocess.CalledProcessError as e:
            self.status_label.color((1, 0, 0, 1))
            self.status_label.text = f'Could not connect to {ssid}...'

    def go_back(self, instance):
        self.manager.current = 'main'
