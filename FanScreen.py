from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.behaviors import ButtonBehavior
from SaunaContext import SaunaContext


class FanScreen(Screen):
    """Fan control screen"""

    def __init__(self, ctx: SaunaContext = None, **kwargs):
        super().__init__(**kwargs)
        self.ctx = ctx

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
        self.right_fan_btn.active = self.ctx.getRightFanOnStatus()
        if self.right_fan_btn.active:
            self.right_fan_btn.background_normal = 'icons/checkbox-checked.png'
            self.right_fan_btn.background_down = 'icons/checkbox-checked.png'
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
        ok_btn.bind(on_press=self.on_ok)
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

    def toggle_right_fan(self, instance):
        """Toggle right fan button state"""
        self.right_fan_btn.active = not self.right_fan_btn.active
        if self.right_fan_btn.active:
            self.right_fan_btn.background_normal = 'icons/checkbox-checked.png'
            self.right_fan_btn.background_down = 'icons/checkbox-checked.png'
        else:
            self.right_fan_btn.background_normal = 'icons/checkbox-unchecked.png'
            self.right_fan_btn.background_down = 'icons/checkbox-unchecked.png'

    def on_speed_change(self, instance, value):
        """Handle fan speed slider change"""
        speed_pct = int(value)
        self.speed_value_label.text = f'{speed_pct}%'
        self.ctx.setFanSpeedPct(speed_pct)

    def on_ok(self, instance):
        self.ctx.setRightFanOnStatus(self.right_fan_btn.active)
        self.ctx.setLeftFanOnStatus(self.left_fan_btn.active)
        self.manager.current = 'main'
