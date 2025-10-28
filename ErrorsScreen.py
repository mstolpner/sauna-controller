from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

# TODO on critical error raise dialog
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

        # Check for Fan errors
        if self.errorMgr._fanErrorMessage:
            has_errors = True
            self.add_error_item('Fan', str(self.errorMgr._fanErrorMessage))

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
            self.errorMgr.eraseFanError()
            print("All errors cleared")
        self.refresh_errors()

    def go_back(self, instance):
        self.manager.current = 'main'
