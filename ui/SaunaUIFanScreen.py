from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from core.SaunaContext import SaunaContext

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

        # Fan controls - top section of screen
        fan_layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=0.25, padding=[0, 0, 0, 0])

        # Make label clickable
        class ClickableLabel(ButtonBehavior, Label):
            pass

        # Both fans in one horizontal row
        fans_box = BoxLayout(orientation='horizontal', spacing=120, size_hint_y=None, height=120)
        fans_box.add_widget(Label(size_hint_x=0.25))  # Left spacer

        self.left_fan_icon = Button(
            size_hint=(None, None),
            size=(120, 120),
            background_normal=self._get_fan_icon(self._ctx.isLeftFanEnabled(), self._ctx.isLeftFanHealthy()),
            background_down=self._get_fan_icon(self._ctx.isLeftFanEnabled(), self._ctx.isLeftFanHealthy()),
            border=(0, 0, 0, 0)
        )
        self.left_fan_icon.bind(on_press=self.toggle_left_fan)
        fans_box.add_widget(self.left_fan_icon)

        self.right_fan_icon = Button(
            size_hint=(None, None),
            size=(120, 120),
            background_normal=self._get_fan_icon(self._ctx.isRightFanEnabled(), self._ctx.isRightFanHealthy()),
            background_down=self._get_fan_icon(self._ctx.isRightFanEnabled(), self._ctx.isRightFanHealthy()),
            border=(0, 0, 0, 0)
        )
        self.right_fan_icon.bind(on_press=self.toggle_right_fan)
        fans_box.add_widget(self.right_fan_icon)

        fans_box.add_widget(Label(size_hint_x=0.25))  # Right spacer

        fan_layout.add_widget(fans_box)

        # RPM Display - centered under fan icons
        rpm_box = BoxLayout(orientation='horizontal', spacing=120, size_hint_y=None, height=35)
        rpm_box.add_widget(Label(size_hint_x=0.25))  # Left spacer

        # Left Fan RPM
        self.left_rpm_value = Label(text='0 RPM', font_size='24sp', bold=True, halign='center',
                                    size_hint_x=None, width=120, color=(0.85, 1.0, 0.4, 1))
        rpm_box.add_widget(self.left_rpm_value)

        # Right Fan RPM
        self.right_rpm_value = Label(text='0 RPM', font_size='24sp', bold=True, halign='center',
                                     size_hint_x=None, width=120, color=(0.85, 1.0, 0.4, 1))
        rpm_box.add_widget(self.right_rpm_value)

        rpm_box.add_widget(Label(size_hint_x=0.25))  # Right spacer

        fan_layout.add_widget(rpm_box)
        layout.add_widget(fan_layout)

        # Add spacer between fans and sliders
        layout.add_widget(Label(size_hint_y=0.10))

        # Fan Speed Control
        speed_layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=0.18, padding=[60, 0, 60, 0])
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
        runtime_layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=0.18, padding=[60, 0, 60, 0])
        runtime_label = Label(
            text='Keep fan running after sauna is off, hrs',
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
        layout.add_widget(Label(size_hint_y=0.08))

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

    def _get_fan_icon(self, enabled, healthy):
        if not healthy:
            return 'icons/fan_red.png'
        elif enabled:
            return 'icons/fan_green.png'
        else:
            return 'icons/fan_grey.png'

    def toggle_left_fan(self, instance):
        new_state = not self._ctx.isLeftFanEnabled()
        self._ctx.setLeftFanEnabled(new_state)
        icon = self._get_fan_icon(new_state, self._ctx.isLeftFanHealthy())
        self.left_fan_icon.background_normal = icon
        self.left_fan_icon.background_down = icon

    def toggle_right_fan(self, instance):
        new_state = not self._ctx.isRightFanEnabled()
        self._ctx.setRightFanEnabled(new_state)
        icon = self._get_fan_icon(new_state, self._ctx.isRightFanHealthy())
        self.right_fan_icon.background_normal = icon
        self.right_fan_icon.background_down = icon

    # Handle fan speed slider change. Update SaunaContext right away.
    def on_speed_change(self, instance, value):
        speed_pct = int(value)
        self._ctx.setFanSpeedPct(speed_pct)
        self.speed_value_label.text = f'{speed_pct}%'

    # Handle fan running time slider change
    def on_runtime_change(self, instance, value):
        runtime_hrs = value
        self.runtime_value_label.text = f'{runtime_hrs:.2f} hrs'

    # Update RPM displays and fan icons from context
    def update_rpm_displays(self, dt):
        if self._ctx:
            left_rpm = self._ctx.getLeftFanRpm()
            right_rpm = self._ctx.getRightFanRpm()
            self.left_rpm_value.text = f'{left_rpm} RPM'
            self.right_rpm_value.text = f'{right_rpm} RPM'

            left_icon = self._get_fan_icon(self._ctx.isLeftFanEnabled(), self._ctx.isLeftFanHealthy())
            self.left_fan_icon.background_normal = left_icon
            self.left_fan_icon.background_down = left_icon

            right_icon = self._get_fan_icon(self._ctx.isRightFanEnabled(), self._ctx.isRightFanHealthy())
            self.right_fan_icon.background_normal = right_icon
            self.right_fan_icon.background_down = right_icon

    def on_ok(self, instance):
        self._ctx.setFanSpeedPct(int(self.speed_slider.value))
        self._ctx.setFanRunningTimeAfterSaunaOffHrs(int(self.runtime_slider.value))
        self._ctx.persist()
        self.manager.current = 'main'
