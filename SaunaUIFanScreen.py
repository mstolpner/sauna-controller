from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from SaunaContext import SaunaContext


class SaunaUIFanScreen(Screen):

    _ctx: SaunaContext = None

    def __init__(self, ctx: SaunaContext = None, **kwargs):
        super().__init__(**kwargs)
        self._ctx = ctx

        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Header
        header = BoxLayout(size_hint_y=0.10)
        header.add_widget(Label(text='Fan Configuration', font_size='30sp', bold=True))
        layout.add_widget(header)

        # Fan controls - top third of screen
        fan_layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=0.23, padding=[0, 10, 0, 0])

        # Make label clickable
        class ClickableLabel(ButtonBehavior, Label):
            pass

        # Both fans in one horizontal row
        fans_box = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=45)
        fans_box.add_widget(Label(size_hint_x=0.15))  # Left spacer - 15% from left

        # Left Fan
        self.left_fan_btn = Button(
            size_hint=(None, None),
            size=(45, 45),
            background_normal='icons/checkbox-unchecked.png',
            background_down='icons/checkbox-unchecked.png',
            border=(0, 0, 0, 0)
        )

        # Load initial state from context
        self.left_fan_btn.active = self._ctx.isLeftFanEnabled()
        if self.left_fan_btn.active:
            self.left_fan_btn.background_normal = 'icons/checkbox-checked.png'
            self.left_fan_btn.background_down = 'icons/checkbox-checked.png'
        self.left_fan_btn.bind(on_press=self.toggle_left_fan)
        fans_box.add_widget(self.left_fan_btn)

        left_label = ClickableLabel(text='Left Fan', font_size='30sp', bold=True, halign='left', size_hint_x=0.4)
        left_label.text_size = (left_label.width, None)
        left_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
        left_label.bind(on_press=self.toggle_left_fan)
        fans_box.add_widget(left_label)

        # Right Fan
        self.right_fan_btn = Button(
            size_hint=(None, None),
            size=(45, 45),
            background_normal='icons/checkbox-unchecked.png',
            background_down='icons/checkbox-unchecked.png',
            border=(0, 0, 0, 0)
        )

        # Load initial state from context
        self.right_fan_btn.active = self._ctx.isRightFanEnabled()
        if self.right_fan_btn.active:
            self.right_fan_btn.background_normal = 'icons/checkbox-checked.png'
            self.right_fan_btn.background_down = 'icons/checkbox-checked.png'
        self.right_fan_btn.bind(on_press=self.toggle_right_fan)
        fans_box.add_widget(self.right_fan_btn)

        right_label = ClickableLabel(text='Right Fan', font_size='30sp', bold=True, halign='left', size_hint_x=0.4)
        right_label.text_size = (right_label.width, None)
        right_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
        right_label.bind(on_press=self.toggle_right_fan)
        fans_box.add_widget(right_label)

        fan_layout.add_widget(fans_box)

        # RPM Display
        rpm_box = BoxLayout(orientation='horizontal', spacing=5, size_hint_y=None, height=35, padding=[0, 0, 0, 0])
        # Add spacer to match checkbox row (15% + checkbox width 45px + spacing 20px = align with checkbox text)
        left_spacer = BoxLayout(size_hint_x=0.15)
        left_spacer.add_widget(Label(size_hint_x=None, width=65))  # 45px checkbox + 20px spacing
        rpm_box.add_widget(left_spacer)

        # Left Fan RPM
        left_rpm_label = Label(text='Left Fan:', font_size='24sp', bold=True, halign='left',
                              size_hint_x=None, width=120, color=(0.5, 0.8, 1.0, 1))
        left_rpm_label.text_size = (left_rpm_label.width, None)
        left_rpm_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
        rpm_box.add_widget(left_rpm_label)

        self.left_rpm_value = Label(text='0 RPM', font_size='24sp', bold=True, halign='left',
                                    size_hint_x=None, width=120, color=(0.85, 1.0, 0.4, 1))
        self.left_rpm_value.text_size = (self.left_rpm_value.width, None)
        self.left_rpm_value.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
        rpm_box.add_widget(self.left_rpm_value)

        # Right Fan RPM
        right_rpm_label = Label(text='Right Fan:', font_size='24sp', bold=True, halign='left',
                               size_hint_x=None, width=130, color=(0.5, 0.8, 1.0, 1))
        right_rpm_label.text_size = (right_rpm_label.width, None)
        right_rpm_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
        rpm_box.add_widget(right_rpm_label)

        self.right_rpm_value = Label(text='0 RPM', font_size='24sp', bold=True, halign='left',
                                     size_hint_x=None, width=120, color=(0.85, 1.0, 0.4, 1))
        self.right_rpm_value.text_size = (self.right_rpm_value.width, None)
        self.right_rpm_value.bind(size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None)))
        rpm_box.add_widget(self.right_rpm_value)

        fan_layout.add_widget(rpm_box)
        layout.add_widget(fan_layout)

        # Fan Speed Control
        speed_layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=0.18, padding=[60, 10, 60, 0])
        speed_label = Label(
            text='Fan Speed',
            font_size='30sp',
            bold=True,
            size_hint_y=0.3
        )
        speed_layout.add_widget(speed_label)

        # Fan speed slider
        initial_speed = self._ctx.getFanSpeedPct() if self._ctx else 100
        self.speed_slider = Slider(
            min=0,
            max=100,
            value=initial_speed,
            step=5,
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

        # Fan Running Time After Sauna Off Control
        runtime_layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=0.18, padding=[60, 10, 60, 0])
        runtime_label = Label(
            text='Time to keep fan running after sauna is off, hrs',
            font_size='24sp',
            bold=True,
            size_hint_y=0.3
        )
        runtime_layout.add_widget(runtime_label)

        # Fan running time slider
        initial_runtime = self._ctx.getFanRunningTimeAfterSaunaOffHrs() if self._ctx else 0.5
        self.runtime_slider = Slider(
            min=0,
            max=12,
            value=initial_runtime,
            step=0.5,
            size_hint_y=0.4
        )
        self.runtime_slider.bind(value=self.on_runtime_change)
        runtime_layout.add_widget(self.runtime_slider)

        # Runtime value display
        self.runtime_value_label = Label(
            text=f'{initial_runtime:.2f} hrs',
            font_size='24sp',
            size_hint_y=0.3
        )
        runtime_layout.add_widget(self.runtime_value_label)
        layout.add_widget(runtime_layout)

        # Spacer to push OK button up from bottom
        layout.add_widget(Label(size_hint_y=0.20))

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

        # Schedule RPM display updates every 2 seconds
        Clock.schedule_interval(self.update_rpm_displays, 1)

    def toggle_left_fan(self, instance):
        self.left_fan_btn.active = not self.left_fan_btn.active
        if self.left_fan_btn.active:
            self.left_fan_btn.background_normal = 'icons/checkbox-checked.png'
            self.left_fan_btn.background_down = 'icons/checkbox-checked.png'
        else:
            self.left_fan_btn.background_normal = 'icons/checkbox-unchecked.png'
            self.left_fan_btn.background_down = 'icons/checkbox-unchecked.png'

    def toggle_right_fan(self, instance):
        self.right_fan_btn.active = not self.right_fan_btn.active
        if self.right_fan_btn.active:
            self.right_fan_btn.background_normal = 'icons/checkbox-checked.png'
            self.right_fan_btn.background_down = 'icons/checkbox-checked.png'
        else:
            self.right_fan_btn.background_normal = 'icons/checkbox-unchecked.png'
            self.right_fan_btn.background_down = 'icons/checkbox-unchecked.png'

    # Handle fan speed slider change. Update SaunaContext right away.
    def on_speed_change(self, instance, value):
        speed_pct = int(value)
        self._ctx.setFanSpeedPct(speed_pct)
        self.speed_value_label.text = f'{speed_pct}%'

    # Handle fan running time slider change
    def on_runtime_change(self, instance, value):
        runtime_hrs = value
        self.runtime_value_label.text = f'{runtime_hrs:.2f} hrs'

    # Update RPM displays from context
    def update_rpm_displays(self, dt):
        if self._ctx:
            left_rpm = self._ctx.getLeftFanRpm()
            right_rpm = self._ctx.getRightFanRpm()
            self.left_rpm_value.text = f'{left_rpm} RPM'
            self.right_rpm_value.text = f'{right_rpm} RPM'

    def on_ok(self, instance):
        self._ctx.setRightFanEnabled(self.right_fan_btn.active)
        self._ctx.setLeftFanEnabled(self.left_fan_btn.active)
        self._ctx.setFanSpeedPct(self.speed_slider.value)
        self._ctx.setFanRunningTimeAfterSaunaOffHrs(self.runtime_slider.value)
        self.manager.current = 'main'
