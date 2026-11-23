# -*- coding: utf-8 -*-
import os
import sys
import random
import json
import math
import time

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Scale, Rotate, Mesh, RoundedRectangle, Ellipse, Line
from kivy.animation import Animation
from kivy.config import Config

Config.set('graphics', 'resizable', '1')
Window.clearcolor = (0.12, 0.12, 0.12, 1)

try:
    from jnius import autoclass, PythonJavaClass, java_method
    from android.runnable import run_on_ui_thread
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')
    View = autoclass('android.view.View')
    Intent = autoclass('android.content.Intent')

    @run_on_ui_thread
    def force_fullscreen():
        window = activity.getWindow()
        decor = window.getDecorView()
        decor.setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        )
        decor.setFocusable(True)
        decor.setFocusableInTouchMode(True)
        decor.requestFocus()

    class AndroidKeyListener(PythonJavaClass):
        __javainterfaces__ = ['android/view/View$OnKeyListener']
        __javacontext__ = 'app'

        def __init__(self, app_ref):
            super().__init__()
            self.app = app_ref

        @java_method('(Landroid/view/View;ILandroid/view/KeyEvent;)Z')
        def onKey(self, view, keyCode, event):
            action = event.getAction()
            Clock.schedule_once(lambda dt: self.app._handle_android_native_key(keyCode, action))
            if keyCode not in (24, 25, 164):
                return True
            return False

    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False


class ParticleEmitter:
    """Yok olan duvarların, süper mod efektlerinin ve yıldız parçacıklarının yöneticisi."""
    def __init__(self, canvas):
        self.canvas = canvas
        self.particles = []

    def spawn_shattered_wall(self, rect, color, creature_size=120):
        x, y, w, h = rect
        effect_type = random.choice([0, 1, 2])
        num_particles = random.randint(30, 50)
        size_factor = max(1.0, creature_size / 120.0)

        for _ in range(num_particles):
            p_x = random.uniform(x, x + w)
            p_y = random.uniform(y, y + h)
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 250) * size_factor
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            life = 1.5
            decay = random.uniform(1.0, 2.0)
            size = random.uniform(8, 20) * (1.0 + (size_factor - 1.0) * 0.4)

            r = min(1.0, max(0.0, color[0] + random.uniform(-0.15, 0.15)))
            g = min(1.0, max(0.0, color[1] + random.uniform(-0.15, 0.15)))
            b = min(1.0, max(0.0, color[2] + random.uniform(-0.15, 0.15)))
            p_color = [r, g, b, 1.0]

            p_data = {
                "type": effect_type,
                "x": p_x, "y": p_y,
                "vx": vx, "vy": vy,
                "size": size,
                "color": p_color,
                "life": life,
                "decay": decay,
                "rot": random.uniform(0, 360),
                "rot_speed": random.uniform(-180, 180)
            }
            self.particles.append(p_data)

    def spawn_super_trail(self, x, y, size, color, glow_size=150.0):
        num_particles = random.randint(4, 7)
        cx = x + size / 2
        cy = y + size / 2
        for _ in range(num_particles):
            p_x = cx + random.uniform(-glow_size / 2, glow_size / 2)
            p_y = cy + random.uniform(-glow_size / 2, glow_size / 2)

            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(25, 60)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            life = 0.95
            decay = random.uniform(1.2, 2.0)
            p_size = random.uniform(14, 26) * (size / 120.0)

            r_neon = random.uniform(0.3, 1.0)
            g_neon = random.uniform(0.3, 1.0)
            b_neon = random.uniform(0.3, 1.0)

            max_channel = max(r_neon, g_neon, b_neon)
            if max_channel > 0:
                r_neon /= max_channel
                g_neon /= max_channel
                b_neon /= max_channel

            p_data = {
                "type": 2,
                "sub_type": random.choice(["orb", "star"]),
                "x": p_x, "y": p_y,
                "vx": vx, "vy": vy,
                "size": p_size,
                "glow_size": glow_size,
                "life": life,
                "decay": decay,
                "neon_color": [r_neon, g_neon, b_neon],
                "rot": random.uniform(0, 360),
                "rot_speed": random.uniform(-150, 150)
            }
            self.particles.append(p_data)

    def update_particles(self, dt):
        self.canvas.clear()

        valid_particles = []
        for p in self.particles:
            if p and isinstance(p, dict) and "life" in p and "type" in p:
                p["life"] -= dt * p.get("decay", 1.0)
                if p["life"] > 0:
                    valid_particles.append(p)
        self.particles = valid_particles

        with self.canvas:
            for p in self.particles:
                alpha = min(1.0, max(0.0, p["life"]))

                if p["type"] == 2:
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["vx"] *= 0.92
                    p["vy"] *= 0.92
                    p["size"] += dt * 9.0
                    p["rot"] += p["rot_speed"] * dt

                    nc = p.get("neon_color", [1.0, 0.9, 0.0])

                    if p.get("sub_type", "orb") == "orb":
                        Color(nc[0], nc[1], nc[2], alpha * 0.35)
                        Ellipse(pos=(p["x"] - p["size"]/2, p["y"] - p["size"]/2), size=(p["size"], p["size"]))
                        Color(1.0, 1.0, 1.0, alpha * 0.85)
                        Ellipse(pos=(p["x"] - p["size"]/4, p["y"] - p["size"]/4), size=(p["size"]/2, p["size"]/2))
                    else:
                        PushMatrix()
                        Rotate(angle=p["rot"], origin=(p["x"], p["y"]), axis=(0, 0, 1))
                        Color(nc[0], nc[1], nc[2], alpha * 0.4)
                        Ellipse(pos=(p["x"] - p["size"]/2, p["y"] - p["size"]/6), size=(p["size"], p["size"]/3))
                        Ellipse(pos=(p["x"] - p["size"]/6, p["y"] - p["size"]/2), size=(p["size"]/3, p["size"]))
                        Color(1.0, 1.0, 1.0, alpha * 0.85)
                        Ellipse(pos=(p["x"] - p["size"]/2.5, p["y"] - p["size"]/12), size=(p["size"]/1.25, p["size"]/6))
                        Ellipse(pos=(p["x"] - p["size"]/12, p["y"] - p["size"]/2.5), size=(p["size"]/6, p["size"]/1.25))
                        PopMatrix()
                elif p["type"] == 0:
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["rot"] += p["rot_speed"] * dt

                    if "color" in p and len(p["color"]) >= 4:
                        Color(p["color"][0], p["color"][1], p["color"][2], alpha)
                    else:
                        Color(1, 1, 1, alpha)

                    PushMatrix()
                    Rotate(angle=p["rot"], origin=(p["x"], p["y"]), axis=(0, 0, 1))
                    Rectangle(pos=(p["x"] - p["size"]/2, p["y"] - p["size"]/2), size=(p["size"], p["size"]))
                    PopMatrix()

                elif p["type"] == 1:
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["rot"] += p["rot_speed"] * dt

                    if "color" in p and len(p["color"]) >= 4:
                        Color(p["color"][0], p["color"][1], p["color"][2], alpha)
                    else:
                        Color(1, 1, 1, alpha)

                    PushMatrix()
                    Rotate(angle=p["rot"], origin=(p["x"], p["y"]), axis=(0, 0, 1))
                    s = p["size"] / 2
                    vertices1 = [
                        p["x"], p["y"] + s, 0, 0,
                        p["x"] - s, p["y"] - s/2, 0, 0,
                        p["x"] + s, p["y"] - s/2, 0, 0
                    ]
                    vertices2 = [
                        p["x"], p["y"] - s, 0, 0,
                        p["x"] - s, p["y"] + s/2, 0, 0,
                        p["x"] + s, p["y"] + s/2, 0, 0
                    ]
                    indices = [0, 1, 2]
                    Mesh(vertices=vertices1, indices=indices, mode='triangles')
                    Mesh(vertices=vertices2, indices=indices, mode='triangles')
                    PopMatrix()

class CreatureOverlayApp(App):
    def build(self):
        from kivy.config import Config
        Config.set('graphics', 'max_fps', '60')
        Config.set('graphics', 'vsync', '1')

        self.title = "Spider Android - Kivy Saf OpenGL Overlay"

        self.about_sparkles = []
        self.sparkle_spawn_timer = 0.0
        self.sparkle_layer = None

        self.SCREEN_WIDTH = Window.width if Window.width > 100 else 1080
        self.SCREEN_HEIGHT = Window.height if Window.height > 100 else 1920

        self.layout = FloatLayout()
        self.bg_layer = Widget()
        self.wall_layer = FloatLayout()
        self.gold_orb_layer = Widget()
        self.particle_layer = Widget()
        self.creature_layer = FloatLayout()
        self.ui_layer = FloatLayout()
        self.toggle_layer = FloatLayout()
        self.focus_layer = Widget()
        self.cursor_layer = Widget()

        self.layout.add_widget(self.bg_layer)
        self.layout.add_widget(self.gold_orb_layer)
        self.layout.add_widget(self.wall_layer)
        self.layout.add_widget(self.particle_layer)
        self.layout.add_widget(self.creature_layer)
        self.layout.add_widget(self.ui_layer)
        self.layout.add_widget(self.toggle_layer)
        self.layout.add_widget(self.focus_layer)
        self.layout.add_widget(self.cursor_layer)
        self.wall_layer.bind(on_touch_down=self.on_wall_touch)

        self.particle_emitter = ParticleEmitter(self.particle_layer.canvas)

        if ANDROID_AVAILABLE:
            ext_dir = activity.getExternalFilesDir(None)
            if ext_dir:
                self.CONFIG_FILE = os.path.join(ext_dir.getAbsolutePath(), "settings_android.json")
            else:
                self.CONFIG_FILE = os.path.join(self.user_data_dir, "settings_android.json")
        else:
            self.CONFIG_FILE = "settings_android.json"

        self.settings = {
            "animation_folder_idx": 0, "animation_folder_idx2": 0, "start_program": 0, 
            "creature_size": 120, "anim_speed": 80, "move_speed": 4, "max_creatures": 6,
            "max_creatures2": 1, "type2_enabled": 1, "image_facing": 0, "visual_offset": 15, 
            "screen_awake": 0, "folder_settings": {}, "super_speed_mult": 3.0,
            "current_hab_idx1": 0,  
            "current_hab_idx2": 0,
            "demo_duration": 20
        }
        self.load_settings()

        self.habitats_list = ["KARA", "HAVA", "DENIZ", "UZAY", "DIGER"]
        self.spider_list = []
        self.walls = []
        self.spider_active = True if self.settings["start_program"] == 1 else False
        self.current_view = "main"
        self.active_settings_tab = "visual"
        self.ui_visible = True

        self.focus_items = []
        self.focus_index = 0
        self.cursor_x = self.SCREEN_WIDTH / 2
        self.cursor_y = self.SCREEN_HEIGHT / 2
        self.cursor_vx = 0
        self.cursor_vy = 0

        self.demo_active = False
        self.demo_timer = 0.0
        self.demo_hab_idx = 0

        self.gold_orb = None
        self.gold_orb_timer = 0.0
        self.gold_orb_spawn_time = 20.0

        self.animation_folders = self.get_available_animation_folders()

        hab_idx = self.settings.get("current_hab_idx1", 0)
        target_hab = self.habitats_list[hab_idx % len(self.habitats_list)]
        initial_filtered = [f for f in self.animation_folders if self.get_folder_habitat(f) == target_hab]

        if len(initial_filtered) <= 1:
            self.settings["type2_enabled"] = 0
            current_folder = initial_filtered[self.settings["animation_folder_idx"] % len(initial_filtered)] if initial_filtered else "default"
            if current_folder in self.settings["folder_settings"]:
                self.settings["folder_settings"][current_folder]["type2_enabled"] = 0

        self.sync_active_folder_settings()

        self.rebuild_toggle_button()
        self.rebuild_ui()
        self.update_background_image()
        self.apply_screen_awake_status()

        Clock.schedule_interval(self.update, 1.0 / 60.0)
        self.next_wall_time = random.uniform(6.0, 12.0)
        self.big_wall_active = False
        self.big_wall_pending_destroy = False
        self.big_wall_destroy_timer = 0.0
        self.wall_timer = 0
        self.big_wall_timer = 0
        self.big_wall_interval = 120.0

        Window.bind(on_resize=self.on_window_resize)
        Window.bind(
            on_key_down=self.on_key_down,
            on_key_up=self.on_key_up,
            on_joy_button_down=self.on_joy_button_down,
            on_joy_button_up=self.on_joy_button_up,
            on_joy_hat=self.on_joy_hat,
            on_joy_axis=self.on_joy_axis
        )

        if ANDROID_AVAILABLE:
            try:
                force_fullscreen()
                self._native_key_listener = AndroidKeyListener(self)

                @run_on_ui_thread
                def _attach_key_listener():
                    decor = activity.getWindow().getDecorView()
                    decor.setFocusable(True)
                    decor.setFocusableInTouchMode(True)
                    decor.requestFocus()
                    decor.setOnKeyListener(self._native_key_listener)
                _attach_key_listener()
            except Exception as e:
                print(f"Native Key Hata: {e}")

        return self.layout
    def update_focus_visual(self):
        self.focus_layer.canvas.clear()
        if not self.ui_visible or not self.focus_items:
            return
        self.focus_index = self.focus_index % len(self.focus_items)
        item = self.focus_items[self.focus_index]
        target = item["widget"] if isinstance(item, dict) else item
        if not target or not target.parent:
            return
        with self.focus_layer.canvas:
            Color(1.0, 0.85, 0.1, 0.9)
            Line(rounded_rectangle=(target.x - 4, target.y - 4, target.width + 8, target.height + 8, 12), width=2.5)

    def _handle_android_native_key(self, keyCode, action):
        if hasattr(self, 'key_debug_label'):
            self.key_debug_label.text = f"ANDROID NATIVE -> keyCode:{keyCode} act:{action}"

        if action == 0:
            self.on_key_down(Window, keyCode, 0, '', [])
        elif action == 1:
            self.on_key_up(Window, keyCode, 0)

    def _on_kb_down(self, keyboard, keycode, text, modifiers):
        if hasattr(self, 'key_debug_label'):
            self.key_debug_label.text = f"KB -> {keycode}"
        self.on_key_down(Window, keycode[0], 0, text, modifiers)
        return True

    def on_joy_button_down(self, window, stickid, buttonid):
        if hasattr(self, 'key_debug_label'):
            self.key_debug_label.text = f"JOY BTN -> stick:{stickid} btn:{buttonid}"

        # Yön Tuşları (11: Yukarı, 12: Aşağı, 13: Sol, 14: Sağ)
        if buttonid == 11:
            self.on_key_down(Window, 273, 0, '', [])   # Yukarı
        elif buttonid == 12:
            self.on_key_down(Window, 274, 0, '', [])   # Aşağı
        elif buttonid == 13:
            self.on_key_down(Window, 276, 0, '', [])   # Sol
        elif buttonid == 14:
            self.on_key_down(Window, 275, 0, '', [])   # Sağ
        # Onay / OK Tuşları
        elif buttonid in (0, 1, 2, 96):
            self.on_key_down(Window, 13, 0, '', [])
        # Geri / Menü Tuşları
        elif buttonid in (3, 4, 97, 111):
            self.on_key_down(Window, 27, 0, '', [])

    def on_joy_button_up(self, window, stickid, buttonid):
        # Yön tuşu bırakıldığında imlecin hareketini durdur
        if buttonid in (11, 12):
            self.cursor_vy = 0
        elif buttonid in (13, 14):
            self.cursor_vx = 0
        # Onay tuşu bırakıldığında kilidi aç (EKLENECEK KISIM)
        elif buttonid in (0, 1, 2, 96):
            self.on_key_up(Window, 13, 0)

    def on_joy_hat(self, window, stickid, hatid, value):
        if hasattr(self, 'key_debug_label'):
            self.key_debug_label.text = f"JOY HAT -> {value}"
        x, y = value
        if y == 1:
            self.on_key_down(Window, 273, 0, '', [])
        elif y == -1:
            self.on_key_down(Window, 274, 0, '', [])
        elif x == -1:
            self.on_key_down(Window, 276, 0, '', [])
        elif x == 1:
            self.on_key_down(Window, 275, 0, '', [])
        elif x == 0 and y == 0:
            self.cursor_vx = 0
            self.cursor_vy = 0

    def on_joy_axis(self, window, stickid, axisid, value):
        if abs(value) > 15000:
            if hasattr(self, 'key_debug_label'):
                self.key_debug_label.text = f"JOY AXIS -> ax:{axisid} val:{value}"
            if axisid == 1:
                self.on_key_down(Window, 273 if value < 0 else 274, 0, '', [])
            elif axisid == 0:
                self.on_key_down(Window, 276 if value < 0 else 275, 0, '', [])
        else:
            self.cursor_vx = 0
            self.cursor_vy = 0

    def on_mouse_move(self, window, pos):
        if any(getattr(t, 'is_touch', False) for t in Window.touches):
            return

        mx, my = pos
        if hasattr(self, 'key_debug_label'):
            self.key_debug_label.text = f"MOUSE -> x:{int(mx)} y:{int(my)}"

        if not self.ui_visible:
            self.cursor_x = mx
            self.cursor_y = my
            return

        for idx, item in enumerate(self.focus_items):
            target = item["widget"] if isinstance(item, dict) else item
            if target and target.collide_point(mx, my):
                if self.focus_index != idx:
                    self.focus_index = idx
                    self.update_focus_visual()
                break

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        if hasattr(self, 'key_debug_label'):
            self.key_debug_label.text = f"Basılan Tuş -> key: {key} | scancode: {scancode}"

        KEY_UP = (273, 19, 1073741906)
        KEY_DOWN = (274, 20, 1073741905)
        KEY_LEFT = (276, 21, 1073741904)
        KEY_RIGHT = (275, 22, 1073741903)
        KEY_OK = (13, 32, 23, 66, 160, 1073741912)
        KEY_BACK = (27, 4, 1073742094)

        if key in KEY_BACK:
            if self.ui_visible and self.current_view != "main":
                self.switch_view("main")
            else:
                self.toggle_ui_visibility(None)
            return True

        if self.ui_visible and self.focus_items:
            self.focus_index = self.focus_index % len(self.focus_items)

            if key in KEY_UP:
                item = self.focus_items[self.focus_index]
                if isinstance(item, dict) and "tab_name" in item:
                    self.focus_index = len(self.focus_items) - 1
                elif isinstance(item, dict) and item.get("io_row") and self.focus_index > 0 and isinstance(self.focus_items[self.focus_index - 1], dict) and self.focus_items[self.focus_index - 1].get("io_row"):
                    self.focus_index = (self.focus_index - 2) % len(self.focus_items)
                else:
                    self.focus_index = (self.focus_index - 1) % len(self.focus_items)
                self.update_focus_visual()
                return True
            elif key in KEY_DOWN:
                item = self.focus_items[self.focus_index]
                if isinstance(item, dict) and "tab_name" in item:
                    sekme_sayisi = sum(1 for x in self.focus_items if isinstance(x, dict) and "tab_name" in x)
                    self.focus_index = sekme_sayisi % len(self.focus_items)
                elif isinstance(item, dict) and item.get("io_row") and (self.focus_index + 1) < len(self.focus_items) and isinstance(self.focus_items[self.focus_index + 1], dict) and self.focus_items[self.focus_index + 1].get("io_row"):
                    self.focus_index = (self.focus_index + 2) % len(self.focus_items)
                else:
                    self.focus_index = (self.focus_index + 1) % len(self.focus_items)
                self.update_focus_visual()
                return True
            elif key in KEY_LEFT:
                item = self.focus_items[self.focus_index]
                if isinstance(item, dict) and item.get("io_row"):
                    if self.focus_index > 0 and isinstance(self.focus_items[self.focus_index - 1], dict) and self.focus_items[self.focus_index - 1].get("io_row"):
                        self.focus_index -= 1
                        self.update_focus_visual()
                elif isinstance(item, dict) and "left" in item and not item["left"].disabled:
                    item["left"].trigger_action(duration=0.05)
                elif isinstance(item, dict) and "tab_name" in item:
                    sekmeler = ["visual", "type1"] + (["type2"] if self.settings.get("type2_enabled", 1) == 1 else [])
                    yeni_idx = (sekmeler.index(item["tab_name"]) - 1) % len(sekmeler)
                    self.focus_index = yeni_idx
                    self._switch_tab_safe(sekmeler[yeni_idx])
                return True
            elif key in KEY_RIGHT:
                item = self.focus_items[self.focus_index]
                if isinstance(item, dict) and item.get("io_row"):
                    if (self.focus_index + 1) < len(self.focus_items) and isinstance(self.focus_items[self.focus_index + 1], dict) and self.focus_items[self.focus_index + 1].get("io_row"):
                        self.focus_index += 1
                        self.update_focus_visual()
                elif isinstance(item, dict) and "right" in item and not item["right"].disabled:
                    item["right"].trigger_action(duration=0.05)
                elif isinstance(item, dict) and "tab_name" in item:
                    sekmeler = ["visual", "type1"] + (["type2"] if self.settings.get("type2_enabled", 1) == 1 else [])
                    yeni_idx = (sekmeler.index(item["tab_name"]) + 1) % len(sekmeler)
                    self.focus_index = yeni_idx
                    self._switch_tab_safe(sekmeler[yeni_idx])
                return True
            elif key in KEY_OK:
                item = self.focus_items[self.focus_index]
                target = item.get("ok") if isinstance(item, dict) else item
                if target and not getattr(target, "disabled", False):
                    target.trigger_action(duration=0.05)
                return True

        # Menü gizliyken (sanal el imleci aktifken) yön tuşları ve orta tuş kontrolü
        if not self.ui_visible:
            cursor_speed = 450
            if key in KEY_UP:
                self.cursor_vy = cursor_speed
                return True
            elif key in KEY_DOWN:
                self.cursor_vy = -cursor_speed
                return True
            elif key in KEY_LEFT:
                self.cursor_vx = -cursor_speed
                return True
            elif key in KEY_RIGHT:
                self.cursor_vx = cursor_speed
                return True
            elif key in KEY_OK:
                if not getattr(self, "remote_ok_held", False):
                    self.remote_ok_held = True
                    self.trigger_cursor_press()
                return True

        return False

    def on_key_up(self, window, key, scancode):
        KEY_UP = (273, 19, 1073741906)
        KEY_DOWN = (274, 20, 1073741905)
        KEY_LEFT = (276, 21, 1073741904)
        KEY_RIGHT = (275, 22, 1073741903)
        KEY_OK = (13, 32, 23, 66, 160, 1073741912)

        if key in KEY_UP or key in KEY_DOWN:
            self.cursor_vy = 0
        elif key in KEY_LEFT or key in KEY_RIGHT:
            self.cursor_vx = 0
        elif key in KEY_OK:
            self.remote_ok_held = False
            self.trigger_cursor_release()
        return False

    def trigger_cursor_press(self):
        # Önce duvar kontrolü yap
        for i, wall in enumerate(list(self.walls)):
            r = wall["rect"]
            if r[0] <= self.cursor_x <= r[0] + r[2] and r[1] <= self.cursor_y <= r[1] + r[3]:
                if wall.get("is_big", False):
                    self.big_wall_active = False
                    self.big_wall_pending_destroy = False
                    self.big_wall_timer = 0.0
                    for s in self.spider_list:
                        if s.is_orbiting:
                            s.is_orbiting = False
                            s.angle = random.uniform(0, 2 * math.pi)
                self.particle_emitter.spawn_shattered_wall(r, wall["color"])
                self.walls.pop(i)
                self.redraw_walls()
                return

        # Duvar yoksa imlecin altındaki yaratığı yakala (Basılı tutma başlangıcı)
        for s in list(self.spider_list):
            if s.x <= self.cursor_x <= s.x + s.size and s.y <= self.cursor_y <= s.y + s.size:
                s.is_grabbed = True
                s.grab_timer = 0.0
                s.grab_start_pos = (self.cursor_x, self.cursor_y)
                s.is_orbiting = False
                s.vx = 0
                s.vy = 0
                self.grabbed_by_remote = s
                return

    def trigger_cursor_release(self):
        s = getattr(self, 'grabbed_by_remote', None)
        if s and s in self.spider_list:
            s.is_grabbed = False
            s.grab_timer = 0.0
            if hasattr(s, 'body_color'):
                s.body_color.rgba = (1.0, 1.0, 1.0, 1.0)
            s.finalize_transforms(None)
            
            # Bırakıldığında rastgele bir yöne fırlat
            s.angle = random.uniform(0, 2 * math.pi)
            s.vx = math.cos(s.angle) * 1200.0
            s.vy = math.sin(s.angle) * 1200.0
            s.is_flung = True
        self.grabbed_by_remote = None

    def sync_active_folder_settings(self):
        filtered1 = self.get_filtered_folders_by_slot(1)
        filtered2 = self.get_filtered_folders_by_slot(2)
        current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
        current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]

        is_single_folder = len(filtered1) <= 1
        default_type2_status = 0 if is_single_folder else 1

        if is_single_folder:
            self.settings["type2_enabled"] = 0

        for folder in [current_folder, current_folder2]:
            if folder not in self.settings["folder_settings"]:
                self.settings["folder_settings"][folder] = {
                    "move_speed": self.settings.get("move_speed", 4),
                    "anim_speed": self.settings.get("anim_speed", 80),
                    "max_creatures": self.settings.get("max_creatures", 6),
                    "max_creatures2": self.settings.get("max_creatures2", 1),
                    "type2_enabled": default_type2_status,
                    "image_facing": self.settings.get("image_facing", 0),
                    "visual_offset": self.settings.get("visual_offset", 15),
                    "creature_size": self.settings.get("creature_size", 120),
                    "bg_image_idx": self.settings.get("bg_image_idx", 0),
                    "super_speed_mult": self.settings.get("super_speed_mult", 3.0)
                }
            elif is_single_folder:
                self.settings["folder_settings"][folder]["type2_enabled"] = 0

        local = self.settings["folder_settings"][current_folder]
        for key in ["move_speed", "anim_speed", "max_creatures", "max_creatures2", "type2_enabled", "image_facing", "visual_offset", "creature_size", "bg_image_idx", "super_speed_mult"]:
            if key in local:
                self.settings[key] = local[key]

    def get_folder_habitat(self, folder_name):
        if folder_name == "default":
            return "DIGER"

        if "/" in folder_name:
            prefix = folder_name.split("/")[0].upper()
            if prefix in ["KARA", "HAVA", "DENIZ", "UZAY", "DIGER"]:
                return prefix

        fn = folder_name.lower()
        if fn.startswith("diger") or "diger" in fn:
            return "DIGER"
        elif fn.startswith("kara") or "orumcek" in fn or "bocek" in fn:
            return "KARA"
        elif fn.startswith("hava") or "kus" in fn or "ucak" in fn:
            return "HAVA"
        elif fn.startswith("deniz") or "balik" in fn or "gemisi" in fn:
            return "DENIZ"
        elif fn.startswith("uzay") or "ufo" in fn or "roket" in fn:
            return "UZAY"
        return "DIGER"

    def get_filtered_folders_by_slot(self, slot_type=1):
        hab_idx = self.settings.get("current_hab_idx1" if slot_type == 1 else "current_hab_idx2", 0)
        target_hab = self.habitats_list[hab_idx % len(self.habitats_list)]
        filtered = [f for f in self.animation_folders if self.get_folder_habitat(f) == target_hab]

        if not filtered:
            return ["default"]

        if slot_type == 2:
            filtered1 = [f for f in self.animation_folders if self.get_folder_habitat(f) == target_hab]
            if filtered1:
                current_folder1 = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
                if len(filtered) > 1 and current_folder1 in filtered:
                    filtered.remove(current_folder1)
                elif len(filtered) == 1 and current_folder1 in filtered:
                    return ["default"]

        return filtered

    def get_filtered_folders_by_current_habitat(self):
        return self.get_filtered_folders_by_slot(1)

    def clear_all_creatures_on_habitat_change(self):
        for spider in list(self.spider_list):
            try:
                spider.canvas_widget.canvas.clear()
                self.creature_layer.remove_widget(spider.canvas_widget)
            except:
                pass
        self.spider_list.clear()

    def apply_screen_awake_status(self):
        if not ANDROID_AVAILABLE:
            return

        @run_on_ui_thread
        def _set_flag():
            if self.settings.get("screen_awake", 0) == 1:
                activity.getWindow().addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
            else:
                activity.getWindow().clearFlags(WindowManager.FLAG_KEEP_SCREEN_ON)

        try:
            _set_flag()
        except:
            pass

    def toggle_screen_awake(self, instance):
        current = self.settings.get("screen_awake", 0)
        self.settings["screen_awake"] = 1 if current == 0 else 0
        self.save_settings()
        self.apply_screen_awake_status()
        self.rebuild_ui()

    def load_settings(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.settings.update(json.load(f))
            except:
                pass

    def save_settings(self):
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f)
        except Exception as e:
            print(f"Ayarlar kaydedilirken hata oluştu: {e}")

    def _set_btn_status(self, btn, text, is_ok, orig_text, orig_color):
        if not btn:
            return
        btn.text = text
        if hasattr(btn, "bg_color_inst"):
            btn.bg_color_inst.rgba = (0.13, 0.77, 0.36, 1) if is_ok else (0.93, 0.26, 0.26, 1)

        def _restore(dt):
            try:
                btn.text = orig_text
                if hasattr(btn, "bg_color_inst"):
                    btn.bg_color_inst.rgba = orig_color
            except Exception:
                pass

        Clock.schedule_once(_restore, 2.0)

    def _find_backup_path(self):
        if ANDROID_AVAILABLE:
            return "/storage/emulated/0/Download/spider_ayarlar.json"
        for folder in ["/storage/emulated/0/Download", "/storage/emulated/0/Documents"]:
            try:
                if os.path.isdir(folder) and os.access(folder, os.W_OK):
                    return os.path.join(folder, "spider_ayarlar.json")
            except Exception:
                pass
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "spider_ayarlar.json")

    def _request_all_files_access(self):
        """Android 11+ cihazlarda Download klasörüne tam erişim izni ekranını açar."""
        if not ANDROID_AVAILABLE:
            return
        try:
            Build = autoclass('android.os.Build$VERSION')
            if Build.SDK_INT >= 30:
                Environment = autoclass('android.os.Environment')
                if not Environment.isExternalStorageManager():
                    Uri = autoclass('android.net.Uri')
                    Settings = autoclass('android.provider.Settings')
                    intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                    pkg_uri = Uri.parse(f"package:{activity.getPackageName()}")
                    intent.setData(pkg_uri)
                    activity.startActivity(intent)
        except Exception as e:
            print(f"İzin yönlendirme hatası: {e}")

    def _apply_imported_data(self, data, instance, orig_color):
        if isinstance(data, dict):
            self.settings.update(data)
            self.animation_folders = self.get_available_animation_folders()

            if "folder_settings" in self.settings and isinstance(self.settings["folder_settings"], dict):
                valid_folders = set(self.animation_folders)
                self.settings["folder_settings"] = {
                    k: v for k, v in self.settings["folder_settings"].items()
                    if k in valid_folders
                }

            hab_len = len(self.habitats_list)
            self.settings["current_hab_idx1"] = self.settings.get("current_hab_idx1", 0) % hab_len
            self.settings["current_hab_idx2"] = self.settings.get("current_hab_idx2", 0) % hab_len

            f1_len = len(self.get_filtered_folders_by_slot(1))
            f2_len = len(self.get_filtered_folders_by_slot(2))
            self.settings["animation_folder_idx"] = self.settings.get("animation_folder_idx", 0) % max(1, f1_len)
            self.settings["animation_folder_idx2"] = self.settings.get("animation_folder_idx2", 0) % max(1, f2_len)

            self.save_settings()
            self.sync_active_folder_settings()
            self.clear_all_creatures_on_habitat_change()
            self.update_background_image()
            self.apply_screen_awake_status()
            self.rebuild_ui()

            for child in self.ui_layer.children:
                if isinstance(child, Button) and child.text == "Yükle":
                    self._set_btn_status(child, "Yüklendi!", True, "Yükle", orig_color)
                    break

    def export_settings_saf(self, instance):
        orig_color = (0.2, 0.5, 0.7, 1)
        target_path = self._find_backup_path()
        try:
            dir_name = os.path.dirname(target_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)

            self._set_btn_status(instance, "Kaydedildi!", True, "Dışa Aktar", orig_color)
            if hasattr(self, "path_label") and self.path_label:
                self.path_label.text = f"[color=aaaaaa][b]Kayıt Yeri :[/b][/color]\n[color=ffd700][b]{target_path}[/b][/color]"
        except PermissionError:
            self._set_btn_status(instance, "İzin Gerekli!", False, "Dışa Aktar", orig_color)
            if hasattr(self, "path_label") and self.path_label:
                self.path_label.text = "[color=ff4444][b]Açılan ekrandan Tüm Dosyalara Erişim izni verin![/b][/color]"
            self._request_all_files_access()
        except Exception as e:
            self._set_btn_status(instance, "Hata!", False, "Dışa Aktar", orig_color)
            if hasattr(self, "path_label") and self.path_label:
                self.path_label.text = f"[color=ff4444][b]Hata: {e}[/b][/color]"

    def import_settings_saf(self, instance):
        orig_color = (0.6, 0.4, 0.2, 1)
        target_path = self._find_backup_path()
        try:
            if not os.path.exists(target_path):
                self._set_btn_status(instance, "Dosya Yok!", False, "Yükle", orig_color)
                if hasattr(self, "path_label") and self.path_label:
                    self.path_label.text = f"[color=ff4444][b]Bulunamadı: {target_path}[/b][/color]"
                return

            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._apply_imported_data(data, instance, orig_color)
            if hasattr(self, "path_label") and self.path_label:
                self.path_label.text = f"[color=45b870][b]Yüklendi: {target_path}[/b][/color]"
        except PermissionError:
            self._set_btn_status(instance, "İzin Gerekli!", False, "Yükle", orig_color)
            if hasattr(self, "path_label") and self.path_label:
                self.path_label.text = "[color=ff4444][b]Açılan ekrandan Tüm Dosyalara Erişim izni verin![/b][/color]"
            self._request_all_files_access()
        except Exception as e:
            self._set_btn_status(instance, "Hata!", False, "Yükle", orig_color)
            if hasattr(self, "path_label") and self.path_label:
                self.path_label.text = f"[color=ff4444][b]Hata: {e}[/b][/color]"

    def get_available_animation_folders(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if app := App.get_running_app():
            if hasattr(app, 'directory') and app.directory:
                base_dir = app.directory

        folders = ["default"]
        anims_path = os.path.join(base_dir, "anims")

        if os.path.exists(anims_path):
            for root, dirs, files in os.walk(anims_path):
                if any(f.rsplit('.', 1)[0].isdigit() for f in files if '.' in f):
                    rel_path = os.path.relpath(root, anims_path)
                    if rel_path != ".":
                        normalized_path = rel_path.replace("\\", "/")
                        if normalized_path not in folders:
                            folders.append(normalized_path)
        return folders
    def update_background_image(self):
        try:
            self.bg_layer.canvas.clear()
            base_dir = os.path.dirname(os.path.abspath(__file__))
            app = App.get_running_app()
            if app and hasattr(app, 'directory') and app.directory:
                base_dir = app.directory

            filtered1 = self.get_filtered_folders_by_slot(1)
            chosen_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]

            anims_root = os.path.join(base_dir, "anims")
            theme_dir = anims_root
            target_hab, target_sf = None, None

            if chosen_folder != "default" and "/" in chosen_folder and os.path.exists(anims_root):
                hab, sf = chosen_folder.split("/")
                real_hab = next((d for d in os.listdir(anims_root) if d.lower() == hab.lower() and os.path.isdir(os.path.join(anims_root, d))), hab)
                hab_path = os.path.join(anims_root, real_hab)
                if os.path.exists(hab_path):
                    real_sf = next((d for d in os.listdir(hab_path) if d.lower() == sf.lower() and os.path.isdir(os.path.join(hab_path, d))), sf)
                    theme_dir = os.path.join(hab_path, real_sf)
                    target_hab, target_sf = real_hab, real_sf

            is_shared_bg = target_hab and target_hab.lower() in ["uzay", "deniz", "hava"]
            if is_shared_bg:
                theme_dir = os.path.join(anims_root, target_hab)
                target_sf = None

            is_portrait = Window.height >= Window.width
            bg_indices = set()

            if os.path.exists(theme_dir):
                for f_name in os.listdir(theme_dir):
                    fn_low = f_name.lower()
                    if fn_low.startswith("bg") and fn_low.endswith((".png", ".jpg", ".jpeg")):
                        clean = fn_low.rsplit(".", 1)[0][2:]
                        num_part = clean.split("_")[0]
                        if num_part == "":
                            bg_indices.add(0)
                        elif num_part.isdigit():
                            bg_indices.add(int(num_part))

            json_path = os.path.join(base_dir, "anims_index.json")
            if not bg_indices and target_hab and os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        structure = json.load(f)
                    j_hab = next((k for k in structure.keys() if k.lower() == target_hab.lower()), None)
                    if j_hab:
                        if is_shared_bg:
                            all_files = structure[j_hab].get("ORTAK_BG", [])
                        else:
                            j_sf = next((sk for sk in structure[j_hab].keys() if sk.lower() == target_sf.lower()), None) if target_sf else None
                            all_files = structure[j_hab][j_sf] if j_sf else []

                        for bf in all_files:
                            fn_low = bf.lower()
                            if fn_low.startswith("bg") and "." in fn_low:
                                clean = fn_low.rsplit(".", 1)[0][2:]
                                num_part = clean.split("_")[0]
                                if num_part == "":
                                    bg_indices.add(0)
                                elif num_part.isdigit():
                                    bg_indices.add(int(num_part))
                except Exception as e:
                    print(f"Arka plan JSON tarama hatası: {e}")

            sorted_indices = sorted(bg_indices) if bg_indices else [0]
            local = self.settings["folder_settings"].get(chosen_folder, self.settings)
            raw_idx = local.get("bg_image_idx", 0)
            chosen_num = sorted_indices[raw_idx % len(sorted_indices)]
            suffix = "" if chosen_num == 0 else str(chosen_num)

            candidates = [
                os.path.join(theme_dir, f"bg{suffix}_v.png" if is_portrait else f"bg{suffix}_h.png"),
                os.path.join(theme_dir, f"bg{suffix}.png"),
                os.path.join(theme_dir, "bg.png"),
                os.path.join(base_dir, "anims", "bg.png")
            ]
            bg_path = next((p for p in candidates if os.path.exists(p)), None)

            if bg_path:
                bg_texture = CoreImage(bg_path).texture
                bg_texture.wrap = 'repeat'
                with self.bg_layer.canvas:
                    Color(1, 1, 1, 1)
                    Rectangle(pos=(0, 0), size=(Window.width, Window.height), texture=bg_texture)
        except Exception as e:
            print(f"Arka plan güncellenirken hata oluştu: {e}")

    def on_window_resize(self, window, width, height):
        self.SCREEN_WIDTH = width if width > 100 else 1080
        self.SCREEN_HEIGHT = height if height > 100 else 1920
        self.update_background_image()
        if hasattr(self, 'ui_layer'):
            self.rebuild_ui()
        if hasattr(self, 'toggle_layer'):
            self.rebuild_toggle_button()

    def rebuild_toggle_button(self):
        self.toggle_layer.clear_widgets()
        self.toggle_btn = Button(
            text="", size_hint=(0.15, 0.08), pos_hint={'x': 0.8, 'y': 0.90},
            background_color=(0.2, 0.25, 0.33, 1), on_press=self.toggle_ui_visibility
        )
        icon_size = 120
        with self.toggle_btn.canvas.after:
            Color(1, 1, 1, 1)
            icon_path = "eye.png" if self.ui_visible else "close.png"
            if os.path.exists(icon_path):
                self.toggle_btn.icon_rect = Rectangle(texture=CoreImage(icon_path).texture, size=(icon_size, icon_size), pos=(0, 0))

        def _update_toggle_icon(instance, value):
            if hasattr(instance, 'icon_rect'):
                instance.icon_rect.pos = (instance.x + (instance.width - icon_size) / 2, instance.y + (instance.height - icon_size) / 2)
        self.toggle_btn.bind(pos=_update_toggle_icon, size=_update_toggle_icon)
        self.toggle_layer.add_widget(self.toggle_btn)

        if getattr(self, 'demo_active', False) and not self.ui_visible:
            hab_colors = {
                "KARA": "45b870",
                "HAVA": "4dc3ff",
                "DENIZ": "00e5ff",
                "UZAY": "d580ff",
                "DIGER": "ff9933"
            }
            current_demo_hab = self.habitats_list[self.demo_hab_idx % len(self.habitats_list)]
            hab_hex = hab_colors.get(current_demo_hab, "ffffff")
            demo_dur = self.settings.get("demo_duration", 20)
            kalan_sure = max(1, int(demo_dur - self.demo_timer) + 1)

            self.mini_demo_label = Label(
                text=f"DEMO : [color={hab_hex}][b]{current_demo_hab}[/b][/color] ({kalan_sure} sn)",
                size_hint=(0.65, 0.06),
                pos_hint={'x': 0.04, 'y': 0.91},
                font_size='16sp',
                color=(0.95, 0.75, 0.15, 1),
                bold=True,
                markup=True
            )
            with self.mini_demo_label.canvas.before:
                Color(0.05, 0.05, 0.05, 0.65)
                self.mini_demo_label.bg_rect = RoundedRectangle(
                    pos=self.mini_demo_label.pos,
                    size=self.mini_demo_label.size,
                    radius=[12]
                )

            def _update_mini_bg(instance, value):
                instance.bg_rect.pos = instance.pos
                instance.bg_rect.size = instance.size

            self.mini_demo_label.bind(pos=_update_mini_bg, size=_update_mini_bg)
            self.toggle_layer.add_widget(self.mini_demo_label)
        else:
            self.mini_demo_label = None

    def rebuild_ui(self):
        self.ui_layer.clear_widgets()
        self.focus_items = []
        if not self.ui_visible:
            Clock.schedule_once(lambda dt: self.update_focus_visual(), 0.05)
            return
        btn_h = 0.052

        def create_visual_button(text, bg_color, y_pos, on_press_callback):
            btn = Button(text=text, size_hint=(0.6, btn_h), pos_hint={'x': 0.2, 'y': y_pos}, font_size='15sp', background_color=(0, 0, 0, 0), markup=True)
            with btn.canvas.before:
                Color(*bg_color)
                btn.bg_rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[12])

            def _update_rect(instance, value):
                instance.bg_rect.pos = instance.pos
                instance.bg_rect.size = instance.size
            btn.bind(pos=_update_rect, size=_update_rect)

            def _animate_press(instance):
                anim = Animation(size_hint_y=btn_h * 0.88, duration=0.06, t='out_quad')

                def _on_anim_complete(*args):
                    anim_back = Animation(size_hint_y=btn_h, duration=0.06, t='in_quad')
                    anim_back.bind(on_complete=lambda *x: on_press_callback(instance))
                    anim_back.start(instance)
                anim.bind(on_complete=_on_anim_complete)
                anim.start(instance)
            btn.bind(on_press=_animate_press)
            return btn
        if self.current_view == "main":
            hab_colors = {
                "KARA": "45b870",
                "HAVA": "4dc3ff",
                "DENIZ": "00e5ff",
                "UZAY": "d580ff",
                "DIGER": "ff9933"
            }

            if self.demo_active:
                current_demo_hab = self.habitats_list[self.demo_hab_idx % len(self.habitats_list)]
                hab_hex = hab_colors.get(current_demo_hab, "ffffff")
                demo_dur = self.settings.get("demo_duration", 20)
                kalan_sure = max(1, int(demo_dur - self.demo_timer) + 1)

                title_text = f"DEMO : [color={hab_hex}][b]{current_demo_hab}[/b][/color] ({kalan_sure} sn)"
                title_color = (0.95, 0.75, 0.15, 1)

                status_text = "Hareketi başlat (Demo Açık)"
                status_color = (0.45, 0.45, 0.45, 1)
            else:
                title_text = "Yaratık yürüyor" if self.spider_active else "Yaratık duruyor"
                title_color = (0.13, 0.77, 0.36, 1) if self.spider_active else (1, 1, 1, 1)

                status_text = "Hareketi durdur" if self.spider_active else "Hareketi başlat"
                status_color = (0.93, 0.26, 0.26, 1) if self.spider_active else (0.13, 0.77, 0.36, 1)

            self.title_label = Label(
                text=title_text,
                size_hint=(0.8, 0.06),
                pos_hint={'x': 0.1, 'y': 0.8},
                font_size='20sp',
                color=title_color,
                bold=True,
                markup=True
            )

            with self.title_label.canvas.before:
                Color(0.05, 0.05, 0.05, 0.5)
                self.title_bg = Rectangle(pos=self.title_label.pos, size=self.title_label.size)

            def _update_title_bg(instance, value):
                self.title_bg.pos = instance.pos
                self.title_bg.size = instance.size
            self.title_label.bind(pos=_update_title_bg, size=_update_title_bg)

            self.ui_layer.add_widget(self.title_label)

            self.status_btn = create_visual_button(status_text, status_color, 0.64, self.toggle_spider)
            self.status_btn.disabled = self.demo_active
            self.status_btn.disabled_color = (0.75, 0.75, 0.75, 1)
            self.ui_layer.add_widget(self.status_btn)

            if self.spider_active:
                demo_text = "Demo Modu (Hareket Açık)"
                demo_color = (0.45, 0.45, 0.45, 1)
            else:
                demo_text = "Demoyu Durdur" if self.demo_active else "Demo Modu"
                demo_color = (0.9, 0.5, 0.1, 1) if self.demo_active else (0.45, 0.35, 0.85, 1)

            self.demo_btn = create_visual_button(demo_text, demo_color, 0.55, self.toggle_demo_mode)
            self.demo_btn.disabled = self.spider_active
            self.demo_btn.disabled_color = (0.75, 0.75, 0.75, 1)
            self.ui_layer.add_widget(self.demo_btn)

            btn_ayarlar = create_visual_button("Ayarlar", (0.2, 0.25, 0.33, 1), 0.46, lambda x: self.switch_view("settings"))
            btn_hakkinda = create_visual_button("Hakkında", (0.2, 0.5, 0.6, 1), 0.37, lambda x: self.switch_view("about"))
            btn_cikis = create_visual_button("Çıkış", (0.93, 0.26, 0.26, 1), 0.28, lambda x: sys.exit())

            self.ui_layer.add_widget(btn_ayarlar)
            self.ui_layer.add_widget(btn_hakkinda)
            self.ui_layer.add_widget(btn_cikis)

            self.focus_items = [self.status_btn, self.demo_btn, btn_ayarlar, btn_hakkinda, btn_cikis]

        elif self.current_view == "settings":
            filtered1 = self.get_filtered_folders_by_slot(1)
            filtered2 = self.get_filtered_folders_by_slot(2)
            current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
            current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]

            if self.active_settings_tab == "type2":
                target_folder = current_folder2
            else:
                target_folder = current_folder

            local1 = self.settings["folder_settings"].setdefault(target_folder, {
                "move_speed": 4, "anim_speed": 80, "max_creatures": 6, "max_creatures2": 1, "type2_enabled": 1,
                "image_facing": 0, "visual_offset": 15, "creature_size": 120, "bg_image_idx": 0, "super_speed_mult": 3.0
            })
            is_type2_on = self.settings.get("type2_enabled", 1) == 1

            tab_y = 0.82

            btn_tab1 = Button(text="Genel/Çevre", size_hint=(0.26, 0.05), pos_hint={'x': 0.08, 'y': tab_y}, font_size='16sp', bold=True, background_color=(0, 0, 0, 0))
            with btn_tab1.canvas.before:
                Color(*(0.13, 0.77, 0.36, 1) if self.active_settings_tab == "visual" else (0.2, 0.25, 0.33, 1))
                btn_tab1.bg_rect = RoundedRectangle(pos=btn_tab1.pos, size=btn_tab1.size, radius=[10])

            btn_tab2 = Button(text="1. Tür Ayar", size_hint=(0.26, 0.05), pos_hint={'x': 0.37, 'y': tab_y}, font_size='16sp', bold=True, background_color=(0, 0, 0, 0))
            with btn_tab2.canvas.before:
                Color(*(0.13, 0.77, 0.36, 1) if self.active_settings_tab == "type1" else (0.2, 0.25, 0.33, 1))
                btn_tab2.bg_rect = RoundedRectangle(pos=btn_tab2.pos, size=btn_tab2.size, radius=[10])

            btn_tab3 = Button(text="2. Tür Ayar", size_hint=(0.26, 0.05), pos_hint={'x': 0.66, 'y': tab_y}, font_size='16sp', bold=True, background_color=(0, 0, 0, 0))
            btn_tab3.disabled = not is_type2_on

            with btn_tab3.canvas.before:
                if not is_type2_on:
                    Color(0.15, 0.15, 0.15, 0.6)
                else:
                    Color(*(0.13, 0.77, 0.36, 1) if self.active_settings_tab == "type2" else (0.2, 0.25, 0.33, 1))
                btn_tab3.bg_rect = RoundedRectangle(pos=btn_tab3.pos, size=btn_tab3.size, radius=[10])

            def _update_tab_rect(inst, val):
                inst.bg_rect.pos = inst.pos
                inst.bg_rect.size = inst.size
            btn_tab1.bind(pos=_update_tab_rect, size=_update_tab_rect)
            btn_tab2.bind(pos=_update_tab_rect, size=_update_tab_rect)
            btn_tab3.bind(pos=_update_tab_rect, size=_update_tab_rect)

            btn_tab1.bind(on_press=lambda x: Clock.schedule_once(lambda dt: self._switch_tab_safe("visual")))
            btn_tab2.bind(on_press=lambda x: Clock.schedule_once(lambda dt: self._switch_tab_safe("type1")))
            btn_tab3.bind(on_press=lambda x: Clock.schedule_once(lambda dt: self._switch_tab_safe("type2")))

            self.ui_layer.add_widget(btn_tab1)
            self.ui_layer.add_widget(btn_tab2)
            self.ui_layer.add_widget(btn_tab3)

            self.focus_items.append({"widget": btn_tab1, "ok": btn_tab1, "tab_name": "visual"})
            self.focus_items.append({"widget": btn_tab2, "ok": btn_tab2, "tab_name": "type1"})
            if is_type2_on:
                self.focus_items.append({"widget": btn_tab3, "ok": btn_tab3, "tab_name": "type2"})

            def _setup_setting_row(label, btn_m, btn_p, y_pos, bg_m_color=(0.2, 0.25, 0.33, 1), bg_p_color=(0.2, 0.25, 0.33, 1)):
                btn_m.size_hint = (0.12, btn_h)
                btn_m.pos_hint = {'x': 0.67, 'y': y_pos}
                btn_m.font_size = '18sp'
                btn_m.background_color = (0, 0, 0, 0)

                btn_p.size_hint = (0.12, btn_h)
                btn_p.pos_hint = {'x': 0.81, 'y': y_pos}
                btn_p.font_size = '18sp'
                btn_p.background_color = (0, 0, 0, 0)

                label.size_hint = (0.58, btn_h)
                label.pos_hint = {'x': 0.07, 'y': y_pos}
                label.font_size = '14sp'
                label.halign = 'center'
                label.valign = 'middle'
                label.bind(size=lambda s, w: setattr(s, 'text_size', s.size))

                with label.canvas.before:
                    Color(0.05, 0.05, 0.05, 0.75)
                    label.bg_rect = RoundedRectangle(pos=label.pos, size=label.size, radius=[10])
                with btn_m.canvas.before:
                    Color(*bg_m_color)
                    btn_m.bg_rect = RoundedRectangle(pos=btn_m.pos, size=btn_m.size, radius=[12])
                with btn_p.canvas.before:
                    Color(*bg_p_color)
                    btn_p.bg_rect = RoundedRectangle(pos=btn_p.pos, size=btn_p.size, radius=[12])

                def _update_bg(inst, val):
                    inst.bg_rect.pos = inst.pos
                    inst.bg_rect.size = inst.size

                label.bind(pos=_update_bg, size=_update_bg)
                btn_m.bind(pos=_update_bg, size=_update_bg)
                btn_p.bind(pos=_update_bg, size=_update_bg)
                self.focus_items.append({"widget": label, "left": btn_m, "right": btn_p})
            if self.active_settings_tab == "visual":
                hab_idx1 = self.settings.get("current_hab_idx1", 0) % len(self.habitats_list)
                current_hab1 = self.habitats_list[hab_idx1]
                self.hab1_label = Label(text=f"Seçili Sınıf: [color=45b870][b]{current_hab1}[/b][/color]", markup=True)
                self.h1_m, self.h1_p = Button(text="<"), Button(text=">")
                _setup_setting_row(self.hab1_label, self.h1_m, self.h1_p, 0.75)
                self.h1_m.bind(on_press=lambda x: self.change_habitat_class_step(-1, 1))
                self.h1_p.bind(on_press=lambda x: self.change_habitat_class_step(1, 1))
                self.ui_layer.add_widget(self.hab1_label)
                self.ui_layer.add_widget(self.h1_m)
                self.ui_layer.add_widget(self.h1_p)

                self.type_label = Label(text=f"1. Alt Tür: [b]{current_folder.upper()}[/b]", markup=True)
                self.t_minus, self.t_plus = Button(text="<"), Button(text=">")
                _setup_setting_row(self.type_label, self.t_minus, self.t_plus, 0.67)
                self.t_minus.bind(on_press=lambda x: self.change_creature_type_step(-1, 1))
                self.t_plus.bind(on_press=lambda x: self.change_creature_type_step(1, 1))
                self.ui_layer.add_widget(self.type_label)
                self.ui_layer.add_widget(self.t_minus)
                self.ui_layer.add_widget(self.t_plus)

                is_single_folder = len(filtered1) <= 1

                if is_single_folder:
                    t2_status_text = "[color=ed4242][b]YOK\n(TEK TÜR)[/b][/color]"
                    self.t2_toggle_label = Label(text=f"2. Tür Durumu: {t2_status_text}", markup=True, halign='center')
                    self.t2_left_btn, self.t2_right_btn = Button(text="X"), Button(text="X")
                    self.t2_left_btn.disabled = True
                    self.t2_right_btn.disabled = True
                else:
                    t2_status_text = "[color=13c444][b]AKTİF[/b][/color]" if is_type2_on else "[color=ed4242][b]PASİF[/b][/color]"
                    self.t2_toggle_label = Label(text=f"2. Tür Durumu: {t2_status_text}", markup=True)
                    self.t2_left_btn, self.t2_right_btn = Button(text="<"), Button(text=">")

                _setup_setting_row(self.t2_toggle_label, self.t2_left_btn, self.t2_right_btn, 0.59)

                def _toggle_type2_switch():
                    filtered_check = self.get_filtered_folders_by_slot(1)
                    if len(filtered_check) <= 1:
                        self.settings["type2_enabled"] = 0
                        self.save_settings()
                        return

                    current_status = 1 if self.settings.get("type2_enabled", 1) == 1 else 0
                    new_status = 0 if current_status == 1 else 1
                    local1["type2_enabled"] = new_status
                    self.settings["type2_enabled"] = new_status
                    self.save_settings()

                    if new_status == 0:
                        for spider in list(self.spider_list):
                            if spider.assigned_folder == current_folder2:
                                try:
                                    spider.canvas_widget.canvas.clear()
                                    self.creature_layer.remove_widget(spider.canvas_widget)
                                    self.spider_list.remove(spider)
                                except:
                                    pass
                    self.rebuild_ui()

                if not is_single_folder:
                    self.t2_left_btn.bind(on_press=lambda x: _toggle_type2_switch())
                    self.t2_right_btn.bind(on_press=lambda x: _toggle_type2_switch())

                self.ui_layer.add_widget(self.t2_toggle_label)
                self.ui_layer.add_widget(self.t2_left_btn)
                self.ui_layer.add_widget(self.t2_right_btn)

                if is_type2_on and not is_single_folder:
                    filtered2 = self.get_filtered_folders_by_slot(2)
                    current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]
                    self.type2_label = Label(text=f"2. Alt Tür: [b]{current_folder2.upper()}[/b]", markup=True)
                    self.t2_m, self.t2_p = Button(text="<"), Button(text=">")
                    _setup_setting_row(self.type2_label, self.t2_m, self.t2_p, 0.51)
                    self.t2_m.bind(on_press=lambda x: self.change_creature_type_step(-1, 2))
                    self.t2_p.bind(on_press=lambda x: self.change_creature_type_step(1, 2))
                    self.ui_layer.add_widget(self.type2_label)
                    self.ui_layer.add_widget(self.t2_m)
                    self.ui_layer.add_widget(self.t2_p)
                    y_pos_bg = 0.43
                elif is_single_folder:
                    self.type2_label = Label(text="2. Alt Tür: [color=ed4242][b]KİLİTLİ[/b][/color]", markup=True)
                    self.t2_m, self.t2_p = Button(text="X"), Button(text="X")
                    self.t2_m.disabled = True
                    self.t2_p.disabled = True
                    _setup_setting_row(self.type2_label, self.t2_m, self.t2_p, 0.51)
                    self.ui_layer.add_widget(self.type2_label)
                    self.ui_layer.add_widget(self.t2_m)
                    self.ui_layer.add_widget(self.t2_p)
                    y_pos_bg = 0.43
                else:
                    y_pos_bg = 0.51

                bg_display_text = "Varsayılan (bg)" if self.settings.get("bg_image_idx", 0) == 0 else f"Tema {self.settings.get('bg_image_idx', 0)}"
                self.bg_img_label = Label(text=f"Arka Plan: [color=e0a040][b]{bg_display_text}[/b][/color]", markup=True)
                self.bg_minus, self.bg_plus = Button(text="<"), Button(text=">")
                _setup_setting_row(self.bg_img_label, self.bg_minus, self.bg_plus, y_pos_bg, (0.7, 0.5, 0.2, 1), (0.7, 0.5, 0.2, 1))
                self.bg_minus.bind(on_press=lambda x: self.change_bg_image_step(-1))
                self.bg_plus.bind(on_press=lambda x: self.change_bg_image_step(1))
                self.ui_layer.add_widget(self.bg_img_label)
                self.ui_layer.add_widget(self.bg_minus)
                self.ui_layer.add_widget(self.bg_plus)

                # --- 6. Satır: Ayarları Yükle / Dışa Aktar (Kumanda D-Pad Uyumlu) ---
                y_pos_io = y_pos_bg - 0.08
                btn_export = Button(text="Dışa Aktar", size_hint=(0.41, btn_h), pos_hint={'x': 0.07, 'y': y_pos_io}, font_size='14sp', bold=True, background_color=(0, 0, 0, 0))
                btn_import = Button(text="Yükle", size_hint=(0.41, btn_h), pos_hint={'x': 0.52, 'y': y_pos_io}, font_size='14sp', bold=True, background_color=(0, 0, 0, 0))

                with btn_export.canvas.before:
                    btn_export.bg_color_inst = Color(0.2, 0.5, 0.7, 1)
                    btn_export.bg_rect = RoundedRectangle(pos=btn_export.pos, size=btn_export.size, radius=(12,))
                with btn_import.canvas.before:
                    btn_import.bg_color_inst = Color(0.6, 0.4, 0.2, 1)
                    btn_import.bg_rect = RoundedRectangle(pos=btn_import.pos, size=btn_import.size, radius=(12,))

                def _upd_io(inst, val):
                    inst.bg_rect.pos = inst.pos
                    inst.bg_rect.size = inst.size

                btn_export.bind(pos=_upd_io, size=_upd_io, on_press=self.export_settings_saf)
                btn_import.bind(pos=_upd_io, size=_upd_io, on_press=self.import_settings_saf)
                self.ui_layer.add_widget(btn_export)
                self.ui_layer.add_widget(btn_import)

                self.focus_items.append({"widget": btn_export, "ok": btn_export, "io_row": True})
                self.focus_items.append({"widget": btn_import, "ok": btn_import, "io_row": True})

                # --- 7. Satır: Ayar Dosyası Kayıt Yolu Bilgisi ---
                y_pos_path = y_pos_io - 0.08
                backup_path = self._find_backup_path()
                self.path_label = Label(
                    text=f"[color=aaaaaa][b]Kayıt Yeri :[/b][/color]\n[color=ffd700][b]{backup_path}[/b][/color]",
                    size_hint=(0.86, btn_h * 1.15),
                    pos_hint={'x': 0.07, 'y': y_pos_path},
                    font_size='12sp',
                    halign='center',
                    valign='middle',
                    markup=True
                )
                self.path_label.bind(size=lambda s, w: setattr(s, 'text_size', (s.width - 20, s.height)))

                with self.path_label.canvas.before:
                    Color(0.05, 0.05, 0.05, 0.80)
                    self.path_label.bg_rect = RoundedRectangle(pos=self.path_label.pos, size=self.path_label.size, radius=[10])

                def _upd_path_bg(inst, val):
                    inst.bg_rect.pos = inst.pos
                    inst.bg_rect.size = inst.size

                self.path_label.bind(pos=_upd_path_bg, size=_upd_path_bg)
                self.ui_layer.add_widget(self.path_label)

                # --- 8. Satır: Demo Süresi Seçim Satırı ---
                y_pos_demo = y_pos_path - 0.068
                demo_dur = self.settings.get("demo_duration", 20)
                self.demo_dur_label = Label(text=f"Demo Süresi: [color=4dc3ff][b]{demo_dur} sn[/b][/color]", markup=True)
                self.dd_minus, self.dd_plus = Button(text="<"), Button(text=">")
                _setup_setting_row(self.demo_dur_label, self.dd_minus, self.dd_plus, y_pos_demo, (0.28, 0.22, 0.55, 1), (0.28, 0.22, 0.55, 1))
                self.dd_minus.bind(on_press=lambda x: self.change_demo_duration_step(-1))
                self.dd_plus.bind(on_press=lambda x: self.change_demo_duration_step(1))
                self.ui_layer.add_widget(self.demo_dur_label)
                self.ui_layer.add_widget(self.dd_minus)
                self.ui_layer.add_widget(self.dd_plus)

            elif self.active_settings_tab == "type1":
                self.size_label = Label(text=f"1. Tür Boyut: {local1.get('creature_size', 120)} px")
                self.sz_minus, self.sz_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.size_label, self.sz_minus, self.sz_plus, 0.72)
                self._check_button_edge_colors_v2("creature_size", 40, 400, self.sz_minus, self.sz_plus, local1)
                self.sz_minus.bind(on_press=lambda x: self.update_stat_live("creature_size", -10, 40, 400, self.size_label, "1. Tür Boyut: ", " px", self.sz_minus, self.sz_plus, target_type=1))
                self.sz_plus.bind(on_press=lambda x: self.update_stat_live("creature_size", 10, 40, 400, self.size_label, "1. Tür Boyut: ", " px", self.sz_minus, self.sz_plus, target_type=1))
                self.ui_layer.add_widget(self.size_label)
                self.ui_layer.add_widget(self.sz_minus)
                self.ui_layer.add_widget(self.sz_plus)

                self.speed_label = Label(text=f"1. Tür Hız: {local1.get('move_speed', 4)}")
                self.s_minus, self.s_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.speed_label, self.s_minus, self.s_plus, 0.64)
                self._check_button_edge_colors_v2("move_speed", 1, 15, self.s_minus, self.s_plus, local1)
                self.s_minus.bind(on_press=lambda x: self.update_stat_live("move_speed", -1, 1, 15, self.speed_label, "1. Tür Hız: ", "", self.s_minus, self.s_plus, target_type=1))
                self.s_plus.bind(on_press=lambda x: self.update_stat_live("move_speed", 1, 1, 15, self.speed_label, "1. Tür Hız: ", "", self.s_minus, self.s_plus, target_type=1))
                self.ui_layer.add_widget(self.speed_label)
                self.ui_layer.add_widget(self.s_minus)
                self.ui_layer.add_widget(self.s_plus)

                self.anim_label = Label(text=f"1. Tür Anim Hızı: {local1.get('anim_speed', 80)} ms")
                self.a_minus, self.a_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.anim_label, self.a_minus, self.a_plus, 0.56)
                self._check_button_edge_colors_v2("anim_speed", 20, 300, self.a_minus, self.a_plus, local1)
                self.a_minus.bind(on_press=lambda x: self.update_stat_live("anim_speed", -10, 20, 300, self.anim_label, "1. Tür Anim: ", " ms", self.a_minus, self.a_plus, target_type=1))
                self.a_plus.bind(on_press=lambda x: self.update_stat_live("anim_speed", 10, 20, 300, self.anim_label, "1. Tür Anim: ", " ms", self.a_minus, self.a_plus, target_type=1))
                self.ui_layer.add_widget(self.anim_label)
                self.ui_layer.add_widget(self.a_minus)
                self.ui_layer.add_widget(self.a_plus)

                self.count_label = Label(text=f"1. Tür Toplam Sayı: {local1.get('max_creatures', 6)}")
                self.c_minus, self.c_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.count_label, self.c_minus, self.c_plus, 0.48)
                self._check_button_edge_colors_v2("max_creatures", 1, 30, self.c_minus, self.c_plus, local1)
                self.c_minus.bind(on_press=lambda x: self.update_stat_live("max_creatures", -1, 1, 30, self.count_label, "1. Tür Toplam Sayı: ", "", self.c_minus, self.c_plus, target_type=1))
                self.c_plus.bind(on_press=lambda x: self.update_stat_live("max_creatures", 1, 1, 30, self.count_label, "1. Tür Toplam Sayı: ", "", self.c_minus, self.c_plus, target_type=1))

                self.ui_layer.add_widget(self.count_label)
                self.ui_layer.add_widget(self.c_minus)
                self.ui_layer.add_widget(self.c_plus)
                self.offset1_label = Label(text=f"1. Tür Ofset: {local1.get('visual_offset', 15)} px")
                self.o1_minus, self.o1_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.offset1_label, self.o1_minus, self.o1_plus, 0.40)
                self._check_button_edge_colors_v2("visual_offset", 0, 50, self.o1_minus, self.o1_plus, local1)
                self.o1_minus.bind(on_press=lambda x: self.update_stat_live("visual_offset", -5, 0, 50, self.offset1_label, "1. Tür Ofset: ", " px", self.o1_minus, self.o1_plus, target_type=1))
                self.o1_plus.bind(on_press=lambda x: self.update_stat_live("visual_offset", 5, 0, 50, self.offset1_label, "1. Tür Ofset: ", " px", self.o1_minus, self.o1_plus, target_type=1))
                self.ui_layer.add_widget(self.offset1_label)
                self.ui_layer.add_widget(self.o1_minus)
                self.ui_layer.add_widget(self.o1_plus)

                face1_deg = local1.get("image_facing", 0) * 90
                self.face1_label = Label(text=f"1. Tür Görsel Açısı: {face1_deg}°")
                self.f1_minus, self.f1_plus = Button(text="<"), Button(text=">")
                _setup_setting_row(self.face1_label, self.f1_minus, self.f1_plus, 0.32)
                self.f1_minus.bind(on_press=lambda x: [self.change_setting_face_step(-1), self.rebuild_ui()])
                self.f1_plus.bind(on_press=lambda x: [self.change_setting_face_step(1), self.rebuild_ui()])
                self.ui_layer.add_widget(self.face1_label)
                self.ui_layer.add_widget(self.f1_minus)
                self.ui_layer.add_widget(self.f1_plus)

                self.super1_label = Label(text=f"1. Tür Süper Hız: {local1.get('super_speed_mult', 3.0):.1f}x")
                self.sp1_minus, self.sp1_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.super1_label, self.sp1_minus, self.sp1_plus, 0.24)
                self._check_button_edge_colors_v2("super_speed_mult", 1.5, 6.0, self.sp1_minus, self.sp1_plus, local1)
                self.sp1_minus.bind(on_press=lambda x: self.update_stat_live("super_speed_mult", -0.5, 1.5, 6.0, self.super1_label, "1. Tür Süper Hız: ", "x", self.sp1_minus, self.sp1_plus, target_type=1))
                self.sp1_plus.bind(on_press=lambda x: self.update_stat_live("super_speed_mult", 0.5, 1.5, 6.0, self.super1_label, "1. Tür Süper Hız: ", "x", self.sp1_minus, self.sp1_plus, target_type=1))
                self.ui_layer.add_widget(self.super1_label)
                self.ui_layer.add_widget(self.sp1_minus)
                self.ui_layer.add_widget(self.sp1_plus)

            elif self.active_settings_tab == "type2":
                self.size2_label = Label(text=f"2. Tür Boyut: {local1.get('creature_size', 120)} px")
                self.sz2_minus, self.sz2_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.size2_label, self.sz2_minus, self.sz2_plus, 0.72)
                self._check_button_edge_colors_v2("creature_size", 40, 400, self.sz2_minus, self.sz2_plus, local1)
                self.sz2_minus.bind(on_press=lambda x: self.update_stat_live("creature_size", -10, 40, 400, self.size2_label, "2. Tür Boyut: ", " px", self.sz2_minus, self.sz2_plus, target_type=2))
                self.sz2_plus.bind(on_press=lambda x: self.update_stat_live("creature_size", 10, 40, 400, self.size2_label, "2. Tür Boyut: ", " px", self.sz2_minus, self.sz2_plus, target_type=2))
                self.ui_layer.add_widget(self.size2_label)
                self.ui_layer.add_widget(self.sz2_minus)
                self.ui_layer.add_widget(self.sz2_plus)

                self.speed2_label = Label(text=f"2. Tür Hız: {local1.get('move_speed', 4)}")
                self.s2_minus, self.s2_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.speed2_label, self.s2_minus, self.s2_plus, 0.64)
                self._check_button_edge_colors_v2("move_speed", 1, 15, self.s2_minus, self.s2_plus, local1)
                self.s2_minus.bind(on_press=lambda x: self.update_stat_live("move_speed", -1, 1, 15, self.speed2_label, "2. Tür Hız: ", "", self.s2_minus, self.s2_plus, target_type=2))
                self.s2_plus.bind(on_press=lambda x: self.update_stat_live("move_speed", 1, 1, 15, self.speed2_label, "2. Tür Hız: ", "", self.s2_minus, self.s2_plus, target_type=2))
                self.ui_layer.add_widget(self.speed2_label)
                self.ui_layer.add_widget(self.s2_minus)
                self.ui_layer.add_widget(self.s2_plus)

                self.anim2_label = Label(text=f"2. Tür Anim Hızı: {local1.get('anim_speed', 80)} ms")
                self.a2_minus, self.a2_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.anim2_label, self.a2_minus, self.a2_plus, 0.56)
                self._check_button_edge_colors_v2("anim_speed", 20, 300, self.a2_minus, self.a2_plus, local1)
                self.a2_minus.bind(on_press=lambda x: self.update_stat_live("anim_speed", -10, 20, 300, self.anim2_label, "2. Tür Anim: ", " ms", self.a2_minus, self.a2_plus, target_type=2))
                self.a2_plus.bind(on_press=lambda x: self.update_stat_live("anim_speed", 10, 20, 300, self.anim2_label, "2. Tür Anim: ", " ms", self.a2_minus, self.a2_plus, target_type=2))
                self.ui_layer.add_widget(self.anim2_label)
                self.ui_layer.add_widget(self.a2_minus)
                self.ui_layer.add_widget(self.a2_plus)

                self.count2_label = Label(text=f"2. Tür Toplam Sayı: {local1.get('max_creatures2', 1)}")
                self.c2_minus, self.c2_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.count2_label, self.c2_minus, self.c2_plus, 0.48)
                self._check_button_edge_colors_v2("max_creatures2", 1, 30, self.c2_minus, self.c2_plus, local1)
                self.c2_minus.bind(on_press=lambda x: self.update_stat_live("max_creatures2", -1, 1, 30, self.count2_label, "2. Tür Toplam Sayı: ", "", self.c2_minus, self.c2_plus, target_type=2))
                self.c2_plus.bind(on_press=lambda x: self.update_stat_live("max_creatures2", 1, 1, 30, self.count2_label, "2. Tür Toplam Sayı: ", "", self.c2_minus, self.c2_plus, target_type=2))
                self.ui_layer.add_widget(self.count2_label)
                self.ui_layer.add_widget(self.c2_minus)
                self.ui_layer.add_widget(self.c2_plus)

                self.offset2_label = Label(text=f"2. Tür Ofset: {local1.get('visual_offset', 15)} px")
                self.o2_minus, self.o2_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.offset2_label, self.o2_minus, self.o2_plus, 0.40)
                self._check_button_edge_colors_v2("visual_offset", 0, 50, self.o2_minus, self.o2_plus, local1)
                self.o2_minus.bind(on_press=lambda x: self.update_stat_live("visual_offset", -5, 0, 50, self.offset2_label, "2. Tür Ofset: ", " px", self.o2_minus, self.o2_plus, target_type=2))
                self.o2_plus.bind(on_press=lambda x: self.update_stat_live("visual_offset", 5, 0, 50, self.offset2_label, "2. Tür Ofset: ", " px", self.o2_minus, self.o2_plus, target_type=2))
                self.ui_layer.add_widget(self.offset2_label)
                self.ui_layer.add_widget(self.o2_minus)
                self.ui_layer.add_widget(self.o2_plus)

                face2_deg = local1.get("image_facing", 0) * 90
                self.face2_label = Label(text=f"2. Tür Görsel Açısı: {face2_deg}°")
                self.f2_minus, self.f2_plus = Button(text="<"), Button(text=">")
                _setup_setting_row(self.face2_label, self.f2_minus, self.f2_plus, 0.32)
                self.super2_label = Label(text=f"2. Tür Süper Hız: {local1.get('super_speed_mult', 3.0):.1f}x")
                self.sp2_minus, self.sp2_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.super2_label, self.sp2_minus, self.sp2_plus, 0.24)
                self._check_button_edge_colors_v2("super_speed_mult", 1.5, 6.0, self.sp2_minus, self.sp2_plus, local1)
                self.sp2_minus.bind(on_press=lambda x: self.update_stat_live("super_speed_mult", -0.5, 1.5, 6.0, self.super2_label, "2. Tür Süper Hız: ", "x", self.sp2_minus, self.sp2_plus, target_type=2))
                self.sp2_plus.bind(on_press=lambda x: self.update_stat_live("super_speed_mult", 0.5, 1.5, 6.0, self.super2_label, "2. Tür Süper Hız: ", "x", self.sp2_minus, self.sp2_plus, target_type=2))
                self.ui_layer.add_widget(self.super2_label)
                self.ui_layer.add_widget(self.sp2_minus)
                self.ui_layer.add_widget(self.sp2_plus)

                def _change_face2(direction):
                    current_face = local1.get("image_facing", 0)
                    local1["image_facing"] = (current_face + direction + 4) % 4
                    self.save_settings()
                    self.rebuild_ui()

                self.f2_minus.bind(on_press=lambda x: _change_face2(-1))
                self.f2_plus.bind(on_press=lambda x: _change_face2(1))
                self.ui_layer.add_widget(self.face2_label)
                self.ui_layer.add_widget(self.f2_minus)
                self.ui_layer.add_widget(self.f2_plus)

            is_awake = self.settings.get("screen_awake", 0) == 1
            self.awake_btn = create_visual_button("", (0.18, 0.68, 0.38, 1) if is_awake else (0.7, 0.4, 0.2, 1), 0.12, self.toggle_screen_awake)

            metin_str = "Uyanık Tut" if is_awake else "Normal Uyku"
            from kivy.uix.label import Label as CoreLabel
            lbl_obj = CoreLabel(text=metin_str, font_size='15sp', markup=True, bold=True)
            lbl_obj.texture_update()

            def _align_custom_elements(instance, value):
                icon_x = instance.x + instance.width - 150
                if hasattr(instance, 'icon_rect'):
                    instance.icon_rect.pos = (icon_x, instance.y + (instance.height - 120) / 2)

                sol_bosluk_genislik = icon_x - instance.x
                yazi_w, yazi_h = lbl_obj.texture.size
                yazi_x = instance.x + (sol_bosluk_genislik - yazi_w) / 2
                yazi_y = instance.y + (instance.height - yazi_h) / 2

                if hasattr(instance, 'text_rect'):
                    instance.text_rect.pos = (yazi_x, yazi_y)
                    instance.text_rect.size = (yazi_w, yazi_h)

            with self.awake_btn.canvas.after:
                Color(1, 1, 1, 1)
                self.awake_btn.text_rect = Rectangle(texture=lbl_obj.texture, pos=(0, 0), size=(1, 1))

                icon_path = "awake.png" if is_awake else "sleep.png"
                if os.path.exists(icon_path):
                    self.awake_btn.icon_rect = Rectangle(texture=CoreImage(icon_path).texture, size=(120, 120), pos=(0, 0))

            self.awake_btn.bind(pos=_align_custom_elements, size=_align_custom_elements)
            self.ui_layer.add_widget(self.awake_btn)
            btn_ana_menu = create_visual_button("Ana Menü", (0.13, 0.77, 0.36, 1), 0.04, lambda x: self.switch_view("main"))
            self.ui_layer.add_widget(btn_ana_menu)

            self.focus_items.append({"widget": self.awake_btn, "ok": self.awake_btn})
            self.focus_items.append({"widget": btn_ana_menu, "ok": btn_ana_menu})
        elif self.current_view == "about":
            self.about_sparkles.clear()
            self.sparkle_spawn_timer = 0.0

            scroll_container = ScrollView(
                size_hint=(0.86, 0.65),
                pos_hint={'x': 0.07, 'y': 0.20},
                do_scroll_x=False,
                do_scroll_y=True
            )

            with scroll_container.canvas.before:
                Color(0.05, 0.05, 0.05, 0.85)
                scroll_container.bg_rect = RoundedRectangle(pos=scroll_container.pos, size=scroll_container.size, radius=[15])

            def _update_scroll_bg(inst, val):
                inst.bg_rect.pos = inst.pos
                inst.bg_rect.size = inst.size
            scroll_container.bind(pos=_update_scroll_bg, size=_update_scroll_bg)

            self.about_label = Label(
                text="[color=45b870][b]SPIDER ANDROID[/b][/color]\n\n"
                     "[b]Sürüm:[/b] v1.4.0\n"
                     "[b]Geliştiren:[/b] Sabri Erkin\n"
                     "[b]Altyapı:[/b] Kivy Saf OpenGL\n\n"
                     "Orijinali [b]Desperado[/b]'nun [b]Spider v0.9.5[/b] adlı symbian uygulamasıdır. Ben biraz geliştirmeye çalıştım ve androidde çalışacak hale getirdim.\n\n"
                     "Bu uygulama, ekran üzerinde rastgele gezinen yaratıklar, parçalanabilir dinamik duvarlar ve özel güçler içeren interaktif bir simülasyondur.\n\n"
                     "[b]Özellikler:[/b]\n"
                     "• Altın küreleri toplayarak süper hıza ulaşın.\n"
                     "• Süper modda engelleri ve rakip yaratıkları yok edin.\n"
                     "• Ayarlar menüsünden tüm fiziksel sınırları canlı olarak yönetin.",
                markup=True, font_size='15sp', halign='center', valign='top',
                padding=(40, 40),
                size_hint_y=None
            )

            def _update_label_height(inst, val):
                inst.text_size = (inst.width, None)

            def _set_texture_height(inst, val):
                inst.height = max(scroll_container.height, inst.texture_size[1] + 80)

            self.about_label.bind(width=_update_label_height)
            self.about_label.bind(texture_size=_set_texture_height)

            scroll_container.add_widget(self.about_label)
            self.ui_layer.add_widget(scroll_container)

            if getattr(self, 'sparkle_layer', None) is not None and self.sparkle_layer in self.ui_layer.children:
                self.ui_layer.remove_widget(self.sparkle_layer)

            self.sparkle_layer = Widget(size_hint=(0.86, 0.65), pos_hint={'x': 0.07, 'y': 0.20})
            self.ui_layer.add_widget(self.sparkle_layer)

            btn_about_back = create_visual_button("Ana Menü", (0.13, 0.77, 0.36, 1), 0.06, lambda x: self.switch_view("main"))
            self.ui_layer.add_widget(btn_about_back)
            self.focus_items.append({"widget": btn_about_back, "ok": btn_about_back})

        Clock.schedule_once(lambda dt: self.update_focus_visual(), 0.05)

    def switch_view(self, view_name):
        self.about_sparkles.clear()
        self.sparkle_spawn_timer = 0.0
        if getattr(self, 'sparkle_layer', None) is not None:
            self.sparkle_layer.canvas.clear()
        self.current_view = view_name
        self.focus_index = 0
        self.rebuild_ui()

    def _switch_tab_safe(self, tab_name):
        self.active_settings_tab = tab_name
        self.rebuild_ui()

    def update_stat_live(self, key, amount, min_v, max_v, label_obj, prefix, suffix="", btn_m=None, btn_p=None, target_type=1):
        filtered1 = self.get_filtered_folders_by_slot(1)
        filtered2 = self.get_filtered_folders_by_slot(2)

        current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
        current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]

        chosen_folder = current_folder if target_type == 1 else current_folder2
        local = self.settings["folder_settings"].setdefault(chosen_folder, {})

        local[key] = round(max(min_v, min(local.get(key, min_v) + amount, max_v)),1)
        self.save_settings()

        label_obj.text = f"{prefix}{local[key]}{suffix}"
        if btn_m and btn_p:
            self._check_button_edge_colors_v2(key, min_v, max_v, btn_m, btn_p, local)

        if key == "max_creatures":
            type1_spiders = [s for s in self.spider_list if s.assigned_folder == current_folder]
            while len(type1_spiders) > local[key]:
                rem = type1_spiders.pop()
                if rem in self.spider_list:
                    self.spider_list.remove(rem)
                try:
                    rem.canvas_widget.canvas.clear()
                    self.creature_layer.remove_widget(rem.canvas_widget)
                except:
                    pass
        elif key == "max_creatures2":
            if self.settings.get("type2_enabled", 1) == 0:
                return
            type2_spiders = [s for s in self.spider_list if s.assigned_folder == current_folder2]
            while len(type2_spiders) > local[key]:
                rem = type2_spiders.pop()
                if rem in self.spider_list:
                    self.spider_list.remove(rem)
                try:
                    rem.canvas_widget.canvas.clear()
                    self.creature_layer.remove_widget(rem.canvas_widget)
                except:
                    pass
        elif key == "visual_offset":
            for spider in self.spider_list:
                if (target_type == 1 and spider.assigned_folder == current_folder) or (target_type == 2 and spider.assigned_folder == current_folder2):
                    spider.visual_offset = local[key]
        elif key == "creature_size":
            for spider in self.spider_list:
                if (target_type == 1 and spider.assigned_folder == current_folder) or (target_type == 2 and spider.assigned_folder == current_folder2):
                    spider.update_size(local[key])
        self.rebuild_ui()

    def _check_button_edge_colors_v2(self, key, min_v, max_v, btn_m, btn_p, local_dict):
        current_value = local_dict.get(key, min_v)
        if btn_m.canvas.before and btn_m.canvas.before.children:
            try:
                if current_value <= min_v:
                    btn_m.canvas.before.children[0].rgba = (0.93, 0.26, 0.26, 1)
                else:
                    btn_m.canvas.before.children[0].rgba = (0.2, 0.25, 0.33, 1)
            except Exception:
                pass

        if btn_p.canvas.before and btn_p.canvas.before.children:
            try:
                if current_value >= max_v:
                    btn_p.canvas.before.children[0].rgba = (0.13, 0.77, 0.36, 1)
                else:
                    btn_p.canvas.before.children[0].rgba = (0.2, 0.25, 0.33, 1)
            except Exception:
                pass
    def toggle_ui_visibility(self, instance):
        self.ui_visible = not self.ui_visible
        self.rebuild_toggle_button()
        self.rebuild_ui()

    def toggle_spider(self, instance):
        if self.demo_active:
            return
        self.spider_active = not self.spider_active

        self.clear_all_creatures_on_habitat_change()
        self.walls.clear()
        self.gold_orb = None
        try:
            self.wall_layer.canvas.clear()
            self.gold_orb_layer.canvas.clear()
        except:
            pass

        if self.spider_active:
            self.update_background_image()

        self.rebuild_ui()

    def toggle_demo_mode(self, instance):
        if self.spider_active:
            return
        self.demo_active = not self.demo_active
        if self.demo_active:
            self._saved_hab_idx1 = self.settings.get("current_hab_idx1", 0)
            self._saved_hab_idx2 = self.settings.get("current_hab_idx2", 0)
            self._saved_folder_idx1 = self.settings.get("animation_folder_idx", 0)
            self._saved_folder_idx2 = self.settings.get("animation_folder_idx2", 0)
            self._saved_bg_idx = self.settings.get("bg_image_idx", 0)

            self.spider_active = False
            self.demo_hab_idx = 0
            self.demo_timer = 0.0
            self._apply_demo_habitat(self.demo_hab_idx)
        else:
            self.demo_active = False
            self.spider_active = False
            self.demo_timer = 0.0

            if hasattr(self, '_saved_hab_idx1'):
                self.settings["current_hab_idx1"] = self._saved_hab_idx1
                self.settings["current_hab_idx2"] = self._saved_hab_idx2
                self.settings["animation_folder_idx"] = self._saved_folder_idx1
                self.settings["animation_folder_idx2"] = self._saved_folder_idx2
                self.settings["bg_image_idx"] = getattr(self, '_saved_bg_idx', 0)
                self.sync_active_folder_settings()

            # Ekrandaki tüm yaratıkları ve katman çizimlerini kesin olarak temizle
            self.clear_all_creatures_on_habitat_change()
            self.creature_layer.clear_widgets()
            self.creature_layer.canvas.clear()

            # Duvarları, altın küreyi ve büyük duvar durumlarını sıfırla
            self.walls.clear()
            self.gold_orb = None
            self.big_wall_active = False
            self.big_wall_pending_destroy = False
            self.big_wall_timer = 0.0
            self.wall_timer = 0.0
            try:
                self.wall_layer.canvas.clear()
                self.gold_orb_layer.canvas.clear()
                self.particle_layer.canvas.clear()
            except Exception:
                pass

            self.update_background_image()

        self.rebuild_toggle_button()
        self.rebuild_ui()

    def _apply_demo_habitat(self, hab_idx):
        self.clear_all_creatures_on_habitat_change()
        target_hab = self.habitats_list[hab_idx % len(self.habitats_list)]
        self.settings["current_hab_idx1"] = hab_idx % len(self.habitats_list)

        hab_folders = [f for f in self.animation_folders if self.get_folder_habitat(f) == target_hab]
        if not hab_folders:
            hab_folders = ["default"]
        random.shuffle(hab_folders)
        self.current_demo_folders = hab_folders

        filtered1 = self.get_filtered_folders_by_slot(1)
        chosen_folder = hab_folders[0]
        if chosen_folder in filtered1:
            self.settings["animation_folder_idx"] = filtered1.index(chosen_folder)
        else:
            self.settings["animation_folder_idx"] = 0

        base_dir = os.path.dirname(os.path.abspath(__file__))
        app = App.get_running_app()
        if app and hasattr(app, 'directory') and app.directory:
            base_dir = app.directory

        anims_root = os.path.join(base_dir, "anims")
        theme_dir = anims_root
        is_shared = target_hab.lower() in ["uzay", "deniz", "hava"]

        if is_shared and os.path.exists(anims_root):
            real_hab = next((d for d in os.listdir(anims_root) if d.lower() == target_hab.lower() and os.path.isdir(os.path.join(anims_root, d))), target_hab)
            theme_dir = os.path.join(anims_root, real_hab)
        elif "/" in chosen_folder and os.path.exists(anims_root):
            hab, sf = chosen_folder.split("/")
            real_hab = next((d for d in os.listdir(anims_root) if d.lower() == hab.lower() and os.path.isdir(os.path.join(anims_root, d))), hab)
            hab_path = os.path.join(anims_root, real_hab)
            if os.path.exists(hab_path):
                real_sf = next((d for d in os.listdir(hab_path) if d.lower() == sf.lower() and os.path.isdir(os.path.join(hab_path, d))), sf)
                theme_dir = os.path.join(hab_path, real_sf)

        bg_count = 1
        if os.path.exists(theme_dir):
            bg_indices = set()
            for f_name in os.listdir(theme_dir):
                fn_low = f_name.lower()
                if fn_low.startswith("bg") and fn_low.endswith((".png", ".jpg", ".jpeg")):
                    clean = fn_low.rsplit(".", 1)[0][2:]
                    num_part = clean.split("_")[0]
                    if num_part == "":
                        bg_indices.add(0)
                    elif num_part.isdigit():
                        bg_indices.add(int(num_part))
            if bg_indices:
                bg_count = len(bg_indices)

        random_bg_idx = random.randint(0, bg_count - 1)
        self.settings["bg_image_idx"] = random_bg_idx
        self.settings["folder_settings"].setdefault(chosen_folder, {})["bg_image_idx"] = random_bg_idx

        self.update_background_image()
        if self.current_view == "main" and self.ui_visible:
            self.rebuild_ui()

    def change_habitat_class_step(self, direction, slot_type=1):
        idx = self.settings.get("current_hab_idx1", 0)
        new_idx = (idx + direction + len(self.habitats_list)) % len(self.habitats_list)

        self.settings["current_hab_idx1"] = new_idx
        self.settings["current_hab_idx2"] = new_idx
        self.settings["animation_folder_idx"] = 0
        self.settings["animation_folder_idx2"] = 0
        self.clear_all_creatures_on_habitat_change()

        target_hab = self.habitats_list[new_idx]
        all_filtered = [f for f in self.animation_folders if self.get_folder_habitat(f) == target_hab]

        if len(all_filtered) <= 1:
            self.settings["type2_enabled"] = 0
            if self.active_settings_tab == "type2":
                self.active_settings_tab = "visual"
            for folder in all_filtered:
                if folder not in self.settings["folder_settings"]:
                    self.settings["folder_settings"][folder] = {}
                self.settings["folder_settings"][folder]["type2_enabled"] = 0

        self.sync_active_folder_settings()
        self.save_settings()
        self.update_background_image()
        self.rebuild_ui()

        sekme_sayisi = sum(1 for x in self.focus_items if isinstance(x, dict) and "tab_name" in x)
        if self.focus_items:
            self.focus_index = min(sekme_sayisi, len(self.focus_items) - 1)
            self.update_focus_visual()

    def change_creature_type_step(self, direction, type_slot=1):
        filtered1 = self.get_filtered_folders_by_slot(1)
        filtered2 = self.get_filtered_folders_by_slot(2)

        if type_slot == 1:
            idx = self.settings.get("animation_folder_idx", 0)
            self.settings["animation_folder_idx"] = (idx + direction + len(filtered1)) % len(filtered1)
            self.clear_all_creatures_on_habitat_change()

            if len(filtered1) <= 1:
                self.settings["type2_enabled"] = 0
        else:
            idx2 = self.settings.get("animation_folder_idx2", 0)
            self.settings["animation_folder_idx2"] = (idx2 + direction + len(filtered2)) % len(filtered2)

        self.sync_active_folder_settings()
        self.save_settings()
        self.update_background_image()
        self.rebuild_ui()

        current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
        current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]

        for i, spider in enumerate(list(self.spider_list)):
            try:
                if spider.id % 2 == 1 and self.settings.get("type2_enabled", 1) == 1:
                    spider.assigned_folder = current_folder2
                else:
                    spider.assigned_folder = current_folder

                local = self.settings["folder_settings"].get(spider.assigned_folder, self.settings)
                spider.size = local.get("creature_size", 120)
                spider.canvas_widget.size = (spider.size, spider.size)

                spider.reload_textures(self.settings, self.animation_folders)
                spider.setup_canvas()
                spider.finalize_transforms(self.settings)
            except Exception as e:
                print(f"Doku yenileme hatası: {e}")

    def change_setting_face_step(self, direction):
        filtered1 = self.get_filtered_folders_by_slot(1)
        current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
        if current_folder not in self.settings["folder_settings"]:
            self.sync_active_folder_settings()
        current_face = self.settings["folder_settings"][current_folder].get("image_facing", 0)
        new_face = (current_face + direction + 4) % 4
        self.settings["folder_settings"][current_folder]["image_facing"] = new_face
        self.settings["image_facing"] = new_face
        self.save_settings()
        self.rebuild_ui()
    def change_bg_image_step(self, direction):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        app = App.get_running_app()
        if app and hasattr(app, 'directory') and app.directory:
            base_dir = app.directory

        filtered1 = self.get_filtered_folders_by_slot(1)
        current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]

        json_path = os.path.join(base_dir, "anims_index.json")
        valid_bg_count = 1

        if "/" in current_folder and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    structure = json.load(f)
                hab, sf = current_folder.split("/")

                target_hab = next((k for k in structure.keys() if k.lower() == hab.lower()), None)
                is_shared_bg = target_hab and target_hab.lower() in ["uzay", "hava", "deniz"]

                if target_hab:
                    if is_shared_bg:
                        all_files = structure[target_hab].get("ORTAK_BG", [])
                    else:
                        target_sf = next((sk for sk in structure[target_hab].keys() if sk.lower() == sf.lower()), None)
                        all_files = structure[target_hab][target_sf] if target_sf else []

                    bg_files = [f for f in all_files if f.lower().startswith("bg") and ("_v" in f.lower() or "_h" in f.lower())]
                    bg_indices = set()
                    for bf in bg_files:
                        clean_name = bf.lower().replace("bg", "")
                        if "_" in clean_name:
                            num_part = clean_name.split("_")[0]
                            if num_part.isdigit():
                                bg_indices.add(int(num_part))
                    if bg_indices:
                        valid_bg_count = max(bg_indices) + 1
            except Exception as e:
                print(f"Arka plan değişim JSON hatası: {e}")

        current_idx = self.settings.get("bg_image_idx", 0)
        new_idx = (current_idx + direction + valid_bg_count) % valid_bg_count

        self.settings["bg_image_idx"] = new_idx
        if current_folder not in self.settings["folder_settings"]:
            self.sync_active_folder_settings()

        if current_folder in self.settings["folder_settings"]:
            self.settings["folder_settings"][current_folder]["bg_image_idx"] = new_idx

        self.save_settings()
        self.update_background_image()
        self.rebuild_ui()

    def change_demo_duration_step(self, direction):
        durations = [20, 30, 45, 60]
        current_val = self.settings.get("demo_duration", 20)
        if current_val not in durations:
            current_val = 20
        idx = durations.index(current_val)
        new_idx = (idx + direction + len(durations)) % len(durations)
        self.settings["demo_duration"] = durations[new_idx]
        self.save_settings()
        self.rebuild_ui()

    def on_start(self):
        self.SCREEN_WIDTH = Window.width if (Window.width and Window.width > 100) else 1080
        self.SCREEN_HEIGHT = Window.height if (Window.height and Window.height > 100) else 1920
        if ANDROID_AVAILABLE:
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            except Exception as e:
                print(f"İzin hatası: {e}")

    def on_wall_touch(self, widget, touch):
        if self.ui_visible and touch.y < self.SCREEN_HEIGHT * 0.90:
            if touch.x > self.SCREEN_WIDTH * 0.1 and touch.x < self.SCREEN_WIDTH * 0.9:
                if self.current_view == "main" and touch.y > self.SCREEN_HEIGHT * 0.30:
                    return
                if self.current_view == "settings" and touch.y > self.SCREEN_HEIGHT * 0.02:
                    return
                if self.current_view == "about" and touch.y > self.SCREEN_HEIGHT * 0.15:
                    return

        for i, wall in enumerate(list(self.walls)):
            if not wall or "rect" not in wall or len(wall["rect"]) < 4:
                continue
            wx, wy, ww, wh = wall["rect"]
            if wx <= touch.x <= wx + ww and wy <= touch.y <= wy + wh:
                if wall.get("is_big", False):
                    for s in self.spider_list:
                        if s.is_orbiting:
                            s.is_orbiting = False
                            s.angle = random.uniform(0, 2 * math.pi)

                    self.big_wall_active = False
                    self.big_wall_pending_destroy = False
                    self.big_wall_timer = 0.0

                self.particle_emitter.spawn_shattered_wall(wall["rect"], wall["color"])
                self.walls.pop(i)
                self.redraw_walls()
                return True
        return False

    def spawn_random_wall(self):
        if len(self.walls) >= 2:
            return
        is_hz = random.choice([True, False])
        w = random.randint(200, 450) if is_hz else random.randint(40, 90)
        h = random.randint(40, 90) if is_hz else random.randint(200, 450)
        x = random.randint(50, max(51, self.SCREEN_WIDTH - w - 50))
        y = random.randint(120, max(121, self.SCREEN_HEIGHT - h - 120))

        for wall in list(self.walls):
            if not wall or "rect" not in wall:
                continue
            wx, wy, ww, wh = wall["rect"]
            if (x - 120 < wx + ww and x + w + 120 > wx and y - 120 < wy + wh and y + h + 120 > wy):
                return
        self.walls.append({"rect": [x, y, w, h], "color": (random.random(), random.random(), random.random(), 1.0), "life": 0.0, "is_big": False})
        self.redraw_walls()

    def spawn_gold_orb(self):
        w_size = 70
        x = random.randint(80, max(81, self.SCREEN_WIDTH - w_size - 80))
        y = random.randint(150, max(151, self.SCREEN_HEIGHT - w_size - 150))
        self.gold_orb = {"x": x, "y": y, "size": w_size, "pulse": 0.0}
        self.redraw_gold_orb()

    def redraw_gold_orb(self):
        self.gold_orb_layer.canvas.clear()
        if not self.gold_orb:
            return
        with self.gold_orb_layer.canvas:
            Color(1, 0.84, 0, 1)
            p_size = self.gold_orb["size"] + math.sin(self.gold_orb["pulse"]) * 8
            offset = (p_size - self.gold_orb["size"]) / 2
            Ellipse(pos=(self.gold_orb["x"] - offset, self.gold_orb["y"] - offset), size=(p_size, p_size))

    def redraw_walls(self):
        self.wall_layer.canvas.clear()
        with self.wall_layer.canvas:
            for wall in self.walls:
                wx, wy, ww, wh = wall["rect"]
                Color(*wall["color"])
                Rectangle(pos=(wx, wy), size=(ww, wh))

    def update(self, dt):
        if self.spider_active or self.demo_active:
            if self.demo_active:
                prev_sec = int(self.demo_timer)
                self.demo_timer += dt

                demo_dur = self.settings.get("demo_duration", 20)

                # Menü açıkken ana etiketi, gizliyken sol üstteki mini etiketi canlı güncelle
                if int(self.demo_timer) != prev_sec:
                    hab_colors = {
                        "KARA": "45b870",
                        "HAVA": "4dc3ff",
                        "DENIZ": "00e5ff",
                        "UZAY": "d580ff",
                        "DIGER": "ff9933"
                    }
                    current_demo_hab = self.habitats_list[self.demo_hab_idx % len(self.habitats_list)]
                    hab_hex = hab_colors.get(current_demo_hab, "ffffff")
                    kalan_sure = max(1, int(demo_dur - self.demo_timer) + 1)
                    yeni_metin = f"DEMO : [color={hab_hex}][b]{current_demo_hab}[/b][/color] ({kalan_sure} sn)"

                    if self.current_view == "main" and self.ui_visible and hasattr(self, 'title_label'):
                        self.title_label.text = yeni_metin
                    elif not self.ui_visible and getattr(self, 'mini_demo_label', None) is not None:
                        self.mini_demo_label.text = yeni_metin

                # Seçilen süre dolduğunda bir sonraki sınıfa geç
                if self.demo_timer >= float(demo_dur):
                    self.demo_timer = 0.0
                    self.demo_hab_idx = (self.demo_hab_idx + 1) % len(self.habitats_list)
                    self._apply_demo_habitat(self.demo_hab_idx)

                # Sadece aktif demo sınıfındaki klasörlerden en fazla 6 yaratık üret
                if len(self.spider_list) < 6:
                    # Yaratık eklemeden hemen önce demonun hâlâ açık olduğunu doğrula
                    if not self.demo_active:
                        return

                    hab_folders = getattr(self, 'current_demo_folders', None)
                    if not hab_folders:
                        target_hab = self.habitats_list[self.demo_hab_idx % len(self.habitats_list)]
                        hab_folders = [f for f in self.animation_folders if self.get_folder_habitat(f) == target_hab] or ["default"]
                        random.shuffle(hab_folders)
                        self.current_demo_folders = hab_folders

                    chosen_f = hab_folders[len(self.spider_list) % len(hab_folders)]
                    new_spider = KivySpiderEntity(self.settings, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.animation_folders, zorunlu_klasor=chosen_f)
                    self.spider_list.append(new_spider)
                    self.creature_layer.add_widget(new_spider.canvas_widget)

            else:
                filtered1 = self.get_filtered_folders_by_slot(1)
                filtered2 = self.get_filtered_folders_by_slot(2)

                current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]

                is_type2_on = self.settings.get("type2_enabled", 1) == 1 and len(filtered1) > 1
                if is_type2_on:
                    current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]
                else:
                    current_folder2 = current_folder

                local1 = self.settings["folder_settings"].get(current_folder, self.settings)
                local2 = self.settings["folder_settings"].get(current_folder2, self.settings)

                limit_type1 = local1.get("max_creatures", 6)
                limit_type2 = local2.get("max_creatures2", 1) if is_type2_on else 0

                allowed_folders = [current_folder]
                if is_type2_on:
                    allowed_folders.append(current_folder2)

                for spider in list(self.spider_list):
                    if spider.assigned_folder not in allowed_folders:
                        try:
                            spider.canvas_widget.canvas.clear()
                            self.creature_layer.remove_widget(spider.canvas_widget)
                            self.spider_list.remove(spider)
                        except:
                            pass

                current_type1_count = sum(1 for s in self.spider_list if s.assigned_folder == current_folder)
                current_type2_count = sum(1 for s in self.spider_list if s.assigned_folder == current_folder2) if is_type2_on else 0

                chosen_f = None
                if is_type2_on:
                    if current_type1_count < limit_type1 and current_type2_count < limit_type2:
                        chosen_f = current_folder if current_type1_count <= current_type2_count else current_folder2
                    elif current_type1_count < limit_type1:
                        chosen_f = current_folder
                    elif current_type2_count < limit_type2:
                        chosen_f = current_folder2
                else:
                    if current_type1_count < limit_type1:
                        chosen_f = current_folder

                if chosen_f:
                    new_spider = KivySpiderEntity(self.settings, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.animation_folders, zorunlu_klasor=chosen_f)
                    self.spider_list.append(new_spider)
                    self.creature_layer.add_widget(new_spider.canvas_widget)
                    return

            self.wall_timer += dt
            if self.wall_timer >= self.next_wall_time:
                self.wall_timer = 0
                self.next_wall_time = random.uniform(8.0, 15.0)
                self.spawn_random_wall()

            current_creature_count = len(self.spider_list)
            any_super_creature = any(s.is_super for s in self.spider_list)
            if current_creature_count >= 6 and not any_super_creature:
                if not self.gold_orb:
                    self.gold_orb_timer += dt
                    if self.gold_orb_timer >= self.gold_orb_spawn_time:
                        self.gold_orb_timer = 0.0
                        self.spawn_gold_orb()
                else:
                    self.gold_orb_timer = 0.0
                    self.gold_orb["pulse"] += dt * 4.0
                    self.redraw_gold_orb()
            else:
                self.gold_orb_timer = 0.0
                if self.gold_orb:
                    self.gold_orb = None
                    self.gold_orb_layer.canvas.clear()

            if not self.big_wall_active:
                self.big_wall_timer += dt
                if self.big_wall_timer >= self.big_wall_interval:
                    if len(self.walls) == 0:
                        boyut = random.randint(300, 400)
                        w, h = boyut, boyut
                        x = (self.SCREEN_WIDTH - w) / 2
                        y = (self.SCREEN_HEIGHT - h) / 2

                        hab_rgba = {
                            "KARA": (0.27, 0.72, 0.44, 1.0),
                            "HAVA": (0.30, 0.76, 1.00, 1.0),
                            "DENIZ": (0.00, 0.90, 1.00, 1.0),
                            "UZAY": (0.84, 0.50, 1.00, 1.0),
                            "DIGER": (1.00, 0.60, 0.20, 1.0)
                        }
                        if self.demo_active:
                            active_hab = self.habitats_list[self.demo_hab_idx % len(self.habitats_list)]
                        else:
                            active_hab = self.habitats_list[self.settings.get("current_hab_idx1", 0) % len(self.habitats_list)]

                        wall_color = hab_rgba.get(active_hab, (0.8, 0.2, 0.2, 1.0))

                        self.walls.append({
                            "rect": [x, y, w, h],
                            "color": wall_color,
                            "life": 0.0,
                            "is_big": True
                        })
                        self.big_wall_active = True
                        self.big_wall_timer = 0.0
                        self.redraw_walls()
                        for s in self.spider_list:
                            s.start_orbiting(x, y, w, h)

            if self.big_wall_active and not self.big_wall_pending_destroy:
                any_orbiting = any(s.is_orbiting for s in self.spider_list)
                if not any_orbiting:
                    for wall in self.walls:
                        if wall.get("is_big", False):
                            wx, wy, ww, wh = wall["rect"]
                            for s in self.spider_list:
                                if not s.is_grabbed and not s.is_flung and not s.is_orbiting:
                                    s.start_orbiting(wx, wy, ww, wh)
                                    break

            if self.big_wall_pending_destroy:
                self.big_wall_destroy_timer -= dt
                if self.big_wall_destroy_timer <= 0:
                    self.big_wall_pending_destroy = False
                    self.big_wall_active = False

                    if hasattr(self, 'particle_emitter'):
                        for wall in self.walls:
                            if wall.get("is_big", False):
                                r = wall["rect"]
                                self.particle_emitter.spawn_shattered_wall(r, wall["color"], creature_size=r[2])

                    self.walls = [w for w in self.walls if not w.get("is_big", False)]
                    self.redraw_walls()

            for spider in list(self.spider_list):
                spider.update_entity(dt, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.settings, self.walls, self.spider_list)
        if hasattr(self, 'particle_emitter'):
            self.particle_emitter.update_particles(dt)

        if self.current_view == "about" and getattr(self, 'sparkle_layer', None) is not None:
            self.sparkle_spawn_timer += dt
            if self.sparkle_spawn_timer >= 0.15 and len(self.about_sparkles) < 35:
                self.sparkle_spawn_timer = 0.0
                sx = random.uniform(self.sparkle_layer.x + 15, self.sparkle_layer.right - 15)
                sy = random.uniform(self.sparkle_layer.y + 15, self.sparkle_layer.top - 15)
                self.about_sparkles.append({
                    "x": sx,
                    "y": sy,
                    "size": random.uniform(14, 32),
                    "alpha": 0.0,
                    "state": "fade_in",
                    "speed": random.uniform(1.2, 2.5),
                    "form": random.choice(["plus", "star"]),
                    "base_color": random.choice([
                        (1.0, 0.9, 0.3),
                        (0.3, 0.9, 0.6),
                        (0.4, 0.8, 1.0),
                        (1.0, 1.0, 1.0)
                    ])
                })

            self.sparkle_layer.canvas.clear()
            with self.sparkle_layer.canvas:
                for sp in list(self.about_sparkles):
                    if sp["state"] == "fade_in":
                        sp["alpha"] += dt * sp["speed"]
                        if sp["alpha"] >= 1.0:
                            sp["alpha"] = 1.0
                            sp["state"] = "fade_out"
                    elif sp["state"] == "fade_out":
                        sp["alpha"] -= dt * sp["speed"]
                        if sp["alpha"] <= 0.0:
                            self.about_sparkles.remove(sp)
                            continue

                    Color(*sp["base_color"], sp["alpha"])
                    sz = sp["size"]
                    thick = sz / 10.0

                    if sp["form"] == "plus":
                        PushMatrix()
                        Rotate(angle=45, origin=(sp["x"], sp["y"]), axis=(0, 0, 1))
                        Rectangle(pos=(sp["x"] - sz/2, sp["y"] - thick/2), size=(sz, thick))
                        Rectangle(pos=(sp["x"] - thick/2, sp["y"] - sz/2), size=(thick, sz))
                        PopMatrix()
                    elif sp["form"] == "star":
                        Rectangle(pos=(sp["x"] - sz/2, sp["y"] - thick/2), size=(sz, thick))
                        Rectangle(pos=(sp["x"] - thick/2, sp["y"] - sz/2), size=(thick, sz))
                        PushMatrix()
                        Rotate(angle=45, origin=(sp["x"], sp["y"]), axis=(0, 0, 1))
                        Rectangle(pos=(sp["x"] - sz/2, sp["y"] - thick/2), size=(sz, thick))
                        Rectangle(pos=(sp["x"] - thick/2, sp["y"] - sz/2), size=(thick, sz))
                        PopMatrix()

        # --- SANAL KUMANDA İMLECİ GÜNCELLEME (İŞARET PARMAĞI 1 BİRİM SOLA GENİŞLETİLDİ) ---
        self.cursor_layer.canvas.clear()
        if not self.ui_visible:
            # 1080p ekranda 1.8x, küçük ekranlarda en az 1.4x ölçek çarpanı
            s = max(1.4, min(self.SCREEN_WIDTH, self.SCREEN_HEIGHT) / 600.0)
            
            # İmleç hızını ekran boyutuna göre dengeli tut
            spd_mult = max(0.8, min(self.SCREEN_WIDTH, self.SCREEN_HEIGHT) / 1080.0)
            self.cursor_x = max(15 * s, min(self.SCREEN_WIDTH - 15 * s, self.cursor_x + self.cursor_vx * spd_mult * dt))
            self.cursor_y = max(48 * s, min(self.SCREEN_HEIGHT - 15 * s, self.cursor_y + self.cursor_vy * spd_mult * dt))

            grabbed_s = getattr(self, 'grabbed_by_remote', None)
            is_holding = grabbed_s and grabbed_s in self.spider_list and grabbed_s.is_grabbed

            if is_holding:
                if abs(self.cursor_vx) > 0 or abs(self.cursor_vy) > 0:
                    grabbed_s.grab_timer = 0.0
                    if hasattr(grabbed_s, 'body_color'):
                        grabbed_s.body_color.rgba = (1.0, 1.0, 1.0, 1.0)
                grabbed_s.x = self.cursor_x - grabbed_s.size / 2
                grabbed_s.y = self.cursor_y - grabbed_s.size / 2
                grabbed_s.finalize_transforms(None)

            cx, cy = self.cursor_x, self.cursor_y
            with self.cursor_layer.canvas:
                # 1. Siyah Dış Kontur
                Color(0.05, 0.05, 0.05, 0.95)
                RoundedRectangle(pos=(cx - 11 * s, cy - 44 * s), size=(21 * s, 11 * s), radius=[4 * s])     # Bilek kontur
                RoundedRectangle(pos=(cx - 15.5 * s, cy - 37 * s), size=(29.5 * s, 29 * s), radius=[7 * s]) # Avuç içi kontur
                RoundedRectangle(pos=(cx - 19 * s, cy - 31 * s), size=(11 * s, 22 * s), radius=[5 * s])     # Başparmak kontur
                if not is_holding:
                    RoundedRectangle(pos=(cx - 12 * s, cy - 16 * s), size=(10 * s, 24 * s), radius=[5 * s]) # İşaret parmağı kontur (1 birim sola genişletildi)
                else:
                    RoundedRectangle(pos=(cx - 12 * s, cy - 16 * s), size=(10 * s, 13 * s), radius=[5 * s]) # İşaret parmağı kontur (kıvrık)
                RoundedRectangle(pos=(cx - 4 * s, cy - 16 * s), size=(8 * s, 13 * s), radius=[4 * s])       # Orta parmak kontur (eski hali)
                RoundedRectangle(pos=(cx + 2 * s, cy - 17 * s), size=(8 * s, 12 * s), radius=[4 * s])       # Yüzük parmağı
                RoundedRectangle(pos=(cx + 8 * s, cy - 19 * s), size=(7 * s, 11 * s), radius=[3.5 * s])     # Serçe parmak

                # 2. Beyaz İç Dolgu
                Color(1.0, 1.0, 1.0, 1.0)
                RoundedRectangle(pos=(cx - 9 * s, cy - 42 * s), size=(17 * s, 9 * s), radius=[3 * s])       # Bilek dolgu
                RoundedRectangle(pos=(cx - 13.5 * s, cy - 35 * s), size=(25.5 * s, 25 * s), radius=[6 * s]) # Avuç içi dolgu
                RoundedRectangle(pos=(cx - 17 * s, cy - 29 * s), size=(8 * s, 18 * s), radius=[4 * s])      # Başparmak dolgu
                if not is_holding:
                    RoundedRectangle(pos=(cx - 10 * s, cy - 14 * s), size=(6 * s, 20 * s), radius=[3 * s])  # İşaret parmağı dolgu (1 birim sola genişletildi)
                else:
                    RoundedRectangle(pos=(cx - 10 * s, cy - 14 * s), size=(6 * s, 9 * s), radius=[3 * s])   # İşaret parmağı dolgu (kıvrık)
                RoundedRectangle(pos=(cx - 2.5 * s, cy - 14 * s), size=(5 * s, 9 * s), radius=[2.5 * s])   # Orta parmak dolgu (eski hali)
                RoundedRectangle(pos=(cx + 3.5 * s, cy - 15 * s), size=(5 * s, 8 * s), radius=[2.5 * s])   # Yüzük parmağı
                RoundedRectangle(pos=(cx + 9.5 * s, cy - 17 * s), size=(4 * s, 7 * s), radius=[2 * s])     # Serçe parmak

class KivySpiderEntity:
    _id_counter = 0

    def __init__(self, settings, sw, sh, animation_folders, zorunlu_klasor=None):
        KivySpiderEntity._id_counter += 1
        self.id = KivySpiderEntity._id_counter
        app = App.get_running_app()

        if zorunlu_klasor:
            self.assigned_folder = zorunlu_klasor
        else:
            filtered1 = app.get_filtered_folders_by_slot(1) if app else ["default"]
            filtered2 = app.get_filtered_folders_by_slot(2) if app else ["default"]
            is_type2_on = settings.get("type2_enabled", 1) == 1 and len(filtered1) > 1

            if is_type2_on and self.id % 2 == 1:
                self.assigned_folder = filtered2[settings.get("animation_folder_idx2", 0) % len(filtered2)]
            else:
                self.assigned_folder = filtered1[settings.get("animation_folder_idx", 0) % len(filtered1)]

        local = settings.get("folder_settings", {}).get(self.assigned_folder, settings)
        self.size = local.get("creature_size", 120)
        self.canvas_widget = Widget(size_hint=(None, None), size=(self.size, self.size))

        spawn_edge = random.randint(0, 3)
        if spawn_edge == 0:
            self.x = -self.size - 20
            self.y = random.randint(0, max(1, sh - self.size))
            self.angle = random.uniform(-math.pi/4, math.pi/4) % (2 * math.pi)
        elif spawn_edge == 1:
            self.x = sw + 20
            self.y = random.randint(0, max(1, sh - self.size))
            self.angle = random.uniform(3 * math.pi / 4, 5 * math.pi / 4) % (2 * math.pi)
        elif spawn_edge == 2:
            self.x = random.randint(0, max(1, sw - self.size))
            self.y = -self.size - 20
            self.angle = random.uniform(math.pi / 4, 3 * math.pi / 4) % (2 * math.pi)
        elif spawn_edge == 3:
            self.x = random.randint(0, max(1, sw - self.size))
            self.y = sh + 20
            self.angle = random.uniform(5 * math.pi / 4, 7 * math.pi / 4) % (2 * math.pi)

        self.canvas_widget.pos = (self.x, self.y)
        self.vx = self.vy = 0.0
        self.is_grabbed = False
        self.grab_timer = 0.0
        self.grab_start_pos = (0.0, 0.0)

        self.last_touch_x = self.last_touch_y = 0.0
        self.current_frame = self.anim_time = 0
        self.is_orbiting = False
        self.visual_offset = local.get("visual_offset", 15)
        self.is_super = False
        self.super_timer = 0.0
        self.textures = {}
        self.reload_textures(settings, animation_folders)
        self.is_flung = False
        self.touch_history = []
        self.roll_angle = 0.0
        self.roll_speed = 0.0
        self.setup_canvas()

    def start_orbiting(self, wx, wy, ww, wh):
        if self.is_grabbed or self.is_orbiting:
            return

        app = App.get_running_app()
        if app and hasattr(app, 'spider_list'):
            if any(s.is_orbiting for s in app.spider_list if s.id != self.id):
                return

        self.is_orbiting = True
        self.orbit_wx, self.orbit_wy, self.orbit_ww, self.orbit_wh = wx, wy, ww, wh
        self.orbit_direction = random.choice([1, -1])

        self.orbit_phase = random.randint(0, 3)
        self.orbit_start_phase = self.orbit_phase
        self.orbit_counter = 0

        x_m, x_mx = self.orbit_wx - self.size + 15 + self.visual_offset, self.orbit_wx + self.orbit_ww - 15 - self.visual_offset
        y_m, y_mx = self.orbit_wy - self.size + 15 + self.visual_offset, self.orbit_wy + self.orbit_wh - 15 - self.visual_offset

        if self.orbit_phase == 0:
            self.x, self.y = x_mx, y_m
        elif self.orbit_phase == 1:
            self.x, self.y = x_m, y_m
        elif self.orbit_phase == 2:
            self.x, self.y = x_m, y_mx
        elif self.orbit_phase == 3:
            self.x, self.y = x_mx, y_mx
    def reload_textures(self, settings, animation_folders):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        app = App.get_running_app()
        if app and hasattr(app, 'directory') and app.directory:
            base_dir = app.directory

        self.total_frames = 0
        self.textures = {}
        local = settings.get("folder_settings", {}).get(self.assigned_folder, settings)

        target_dir = os.path.join(base_dir, "anims")
        if "/" in self.assigned_folder:
            hab, sf = self.assigned_folder.split("/")
            target_dir = os.path.join(target_dir, hab, sf)
        elif self.assigned_folder != "default":
            target_dir = os.path.join(target_dir, self.assigned_folder)

        if os.path.exists(target_dir):
            bg_v = f"bg{local.get('bg_image_idx', 0)}_v.png"
            bg_h = f"bg{local.get('bg_image_idx', 0)}_h.png"
            valid_files = []

            try:
                for f_name in os.listdir(target_dir):
                    full_file_path = os.path.join(target_dir, f_name)
                    if os.path.isfile(full_file_path) and '.' in f_name:
                        name_part = f_name.rsplit('.', 1)[0]
                        if name_part.isdigit() and f_name.lower() not in [bg_v.lower(), bg_h.lower(), 'bg.png']:
                            valid_files.append((int(name_part), full_file_path))
            except Exception as walk_e:
                print(f"Klasör listeleme hatası: {walk_e}")

            valid_files.sort(key=lambda item: item[0])
            for num, p in valid_files:
                try:
                    core_img = CoreImage(p)
                    if core_img and core_img.texture:
                        self.textures[self.total_frames] = core_img.texture
                        self.total_frames += 1
                except Exception as img_e:
                    print(f"Doku Yukleme Hatasi ({p}): {img_e}")

        if self.total_frames == 0:
            anims_dir = os.path.join(base_dir, "anims")
            if os.path.exists(anims_dir):
                try:
                    available_files = os.listdir(anims_dir)
                    valid_idx = []
                    for f_name in available_files:
                        full_file_path = os.path.join(anims_dir, f_name)
                        if os.path.isfile(full_file_path) and f_name.lower().endswith('.png'):
                            name_part = f_name.rsplit('.', 1)[0]
                            if name_part.isdigit():
                                valid_idx.append(int(name_part))

                    valid_idx.sort()
                    for num in valid_idx:
                        p = os.path.join(anims_dir, f"{num}.png")
                        if os.path.exists(p):
                            try:
                                core_img = CoreImage(p)
                                if core_img and core_img.texture:
                                    self.textures[self.total_frames] = core_img.texture
                                    self.total_frames += 1
                            except Exception as img_e:
                                print(f"Varsayılan Doku Yükleme Hatası ({p}): {img_e}")
                except Exception as e:
                    print(f"Anims klasörü taranırken hata oluştu: {e}")

        self.current_frame = 0
        self.visual_offset = local.get("visual_offset", 15)

    def setup_canvas(self):
        self.canvas_widget.canvas.clear()
        self.rect_w = self.size
        self.rect_h = self.size

        has_texture = False
        if self.textures and self.textures.get(self.current_frame):
            tex = self.textures.get(self.current_frame)
            oran = tex.width / tex.height

            if oran > 1.3:
                self.rect_h = self.size
                self.rect_w = self.size * oran
            elif oran < 0.7:
                self.rect_w = self.size
                self.rect_h = self.size / oran
            else:
                if oran > 1:
                    self.rect_w = self.size
                    self.rect_h = self.size / oran
                else:
                    self.rect_h = self.size
                    self.rect_w = self.size * oran
            has_texture = True

        with self.canvas_widget.canvas:
            PushMatrix()
            self.rot_transform = Rotate(angle=0, axis=(0, 0, 1), origin=self.canvas_widget.center)
            self.scale_transform = Scale(1, 1, 1, origin=self.canvas_widget.center)

            if self.is_super:
                glow_factor = 1.25 if self.size <= 150 else (1.1 + 22.5 / self.size)
                glow_w = self.rect_w * glow_factor
                glow_h = self.rect_h * glow_factor
                Color(1.0, 0.84, 0.0, 0.25)
                self.super_glow = Ellipse(pos=(self.x + (self.size - glow_w)/2, self.y + (self.size - glow_h)/2), size=(glow_w, glow_h))

            if has_texture:
                self.body_color = Color(1.0, 1.0, 1.0, 1.0)
                self.rect_mesh = Rectangle(texture=self.textures[0], pos=(self.x + (self.size - self.rect_w)/2, self.y + (self.size - self.rect_h)/2), size=(self.rect_w, self.rect_h))
            else:
                self.body_color = Color(0.2, 0.7, 0.3, 1.0)
                self.rect_mesh = Ellipse(pos=(self.x + (self.size - self.rect_w)/2, self.y + (self.size - self.rect_h)/2), size=(self.rect_w, self.rect_h))
            PopMatrix()

        self.canvas_widget.unbind(on_touch_down=self.on_touch_down, on_touch_move=self.on_touch_move, on_touch_up=self.on_touch_up)
        self.canvas_widget.bind(on_touch_down=self.on_touch_down, on_touch_move=self.on_touch_move, on_touch_up=self.on_touch_up)

    def activate_super_power(self, duration=15.0):
        self.is_super = True
        self.super_timer = duration
        self.setup_canvas()

    def update_size(self, new_size):
        self.size = new_size
        self.canvas_widget.size = (self.size, self.size)
        self.setup_canvas()

    def on_touch_down(self, widget, touch):
        app = App.get_running_app()
        if app and app.ui_visible and touch.y > app.SCREEN_HEIGHT * 0.10 and touch.y < app.SCREEN_HEIGHT * 0.85 and touch.x > app.SCREEN_WIDTH * 0.15 and touch.x < app.SCREEN_WIDTH * 0.85:
            return False
        if widget.collide_point(*touch.pos):
            self.touch_history.clear()
            self.is_grabbed = True
            self.grab_timer = 0.0
            self.grab_start_pos = (touch.x, touch.y)

            if self.is_orbiting:
                self.is_orbiting = False
                if hasattr(self, 'orbit_counter'):
                    self.orbit_counter = 0

            self.vx = self.vy = 0
            self.last_touch_x = touch.x
            self.last_touch_y = touch.y
            return True
        return False

    def on_touch_move(self, widget, touch):
        if self.is_grabbed:
            dist_moved = math.hypot(touch.x - self.grab_start_pos[0], touch.y - self.grab_start_pos[1])
            if dist_moved > 35:
                self.grab_timer = 0.0
                self.grab_start_pos = (touch.x, touch.y)
                if hasattr(self, 'body_color'):
                    self.body_color.rgba = (1.0, 1.0, 1.0, 1.0)

            self.touch_history.append((time.time(), touch.x, touch.y))
            if len(self.touch_history) > 4:
                self.touch_history.pop(0)
            self.x, self.y = touch.x - self.size / 2, touch.y - self.size / 2
            self.last_touch_x, self.last_touch_y = touch.x, touch.y
            self.finalize_transforms(None)
            return True
        return False

    def on_touch_up(self, widget, touch):
        if self.is_grabbed:
            self.is_grabbed = False
            self.grab_timer = 0.0
            if hasattr(self, 'body_color'):
                self.body_color.rgba = (1.0, 1.0, 1.0, 1.0)
            self.finalize_transforms(None)
            if len(self.touch_history) >= 2:
                t1, x1, y1 = self.touch_history[0]
                t2, x2, y2 = self.touch_history[-1]
                dt = t2 - t1
                if dt > 0:
                    self.vx = ((x2 - x1) / dt) * 1.5
                    self.vy = ((y2 - y1) / dt) * 1.5
                    spd = math.sqrt(self.vx**2 + self.vy**2)
                    if spd > 4000.0:
                        self.vx = (self.vx / spd) * 4000.0
                        self.vy = (self.vy / spd) * 4000.0
                    if spd > 100:
                        self.angle = math.atan2(self.vy, self.vx) % (2 * math.pi)
                        self.is_flung = True
            self.touch_history.clear()
            return True
        return False
    def update_entity(self, dt, sw, sh, settings, walls, spider_list):
        if self.is_grabbed:
            self.grab_timer += dt
            oran = min(1.0, self.grab_timer / 3.0)

            scale_mult = 1.0 + (oran * 0.5)
            if hasattr(self, 'scale_transform'):
                fx = -1 if self.scale_transform.x < 0 else 1
                fy = -1 if self.scale_transform.y < 0 else 1
                self.scale_transform.origin = self.canvas_widget.center
                self.scale_transform.x = fx * scale_mult
                self.scale_transform.y = fy * scale_mult

            if hasattr(self, 'body_color'):
                self.body_color.rgba = (1.0, 1.0 - (oran * 0.85), 1.0 - (oran * 0.85), 1.0)

            if self.grab_timer >= 3.0:
                app = App.get_running_app()
                if app and hasattr(app, 'particle_emitter'):
                    kirmizi_ton = [1.0, random.uniform(0.0, 0.3), random.uniform(0.0, 0.2), 1.0]
                    app.particle_emitter.spawn_shattered_wall(
                        [self.x, self.y, self.size, self.size],
                        kirmizi_ton,
                        self.size * 1.5
                    )
                try:
                    self.canvas_widget.canvas.clear()
                    if app and hasattr(app, 'creature_layer'):
                        app.creature_layer.remove_widget(self.canvas_widget)
                    if self in spider_list:
                        spider_list.remove(self)
                except Exception:
                    pass
            return

        self.anim_time += dt
        if abs(self.roll_speed) > 0.1:
            self.roll_angle += self.roll_speed * dt
            self.roll_speed *= 0.5
        else:
            self.roll_speed = 0.0

        if self.is_super:
            self.super_timer -= dt
            if self.super_timer <= 0:
                self.is_super = False
                self.setup_canvas()
        app = App.get_running_app()
        local = settings.get("folder_settings", {}).get(self.assigned_folder, settings)
        if self.is_super:
            mult = local.get("super_speed_mult", 3.0)
            base_spd = local.get("move_speed", 4) * 30 * mult
        else:
            base_spd = local.get("move_speed", 4) * 30

        if self.is_flung:
            current_speed = math.sqrt(self.vx**2 + self.vy**2)
            if current_speed > base_spd:
                self.vx *= 0.975
                self.vy *= 0.975
                self.angle = math.atan2(self.vy, self.vx) % (2 * math.pi)
            else:
                self.is_flung = False
        else:
            self.vx = math.cos(self.angle) * base_spd
            self.vy = math.sin(self.angle) * base_spd

        if self.is_orbiting:
            big_wall_exists = any(w.get("is_big", False) for w in walls)
            if not big_wall_exists:
                self.is_orbiting = False
                self.angle = random.uniform(0, 2 * math.pi)

            x_m, x_mx = self.orbit_wx - self.size + 15 + self.visual_offset, self.orbit_wx + self.orbit_ww - 15 - self.visual_offset
            y_m, y_mx = self.orbit_wy - self.size + 15 + self.visual_offset, self.orbit_wy + self.orbit_wh - 15 - self.visual_offset

            d_mult = 1.0 if self.orbit_direction == 1 else -1.0
            t_ang = math.pi if self.orbit_phase == 0 else (math.pi*0.5 if self.orbit_phase == 1 else (0.0 if self.orbit_phase == 2 else math.pi*1.5))
            if self.orbit_direction == -1:
                t_ang = (t_ang + math.pi) % (2 * math.pi)

            c_spd = base_spd

            if self.orbit_phase == 0:
                self.y = y_m
                self.x -= c_spd * dt * d_mult
                if self.orbit_direction == 1 and self.x <= x_m:
                    self.x = x_m; self.orbit_phase = 1; self.orbit_counter += 1
                elif self.orbit_direction == -1 and self.x >= x_mx:
                    self.x = x_mx; self.orbit_phase = 3; self.orbit_counter += 1
            elif self.orbit_phase == 1:
                self.x = x_m
                self.y += c_spd * dt * d_mult
                if self.orbit_direction == 1 and self.y >= y_mx:
                    self.y = y_mx; self.orbit_phase = 2; self.orbit_counter += 1
                elif self.orbit_direction == -1 and self.y <= y_m:
                    self.y = y_m; self.orbit_phase = 0; self.orbit_counter += 1
            elif self.orbit_phase == 2:
                self.y = y_mx
                self.x += c_spd * dt * d_mult
                if self.orbit_direction == 1 and self.x >= x_mx:
                    self.x = x_mx; self.orbit_phase = 3; self.orbit_counter += 1
                elif self.orbit_direction == -1 and self.x <= x_m:
                    self.x = x_m; self.orbit_phase = 1; self.orbit_counter += 1
            elif self.orbit_phase == 3:
                self.x = x_mx
                self.y -= c_spd * dt * d_mult
                if self.orbit_direction == 1 and self.y <= y_m:
                    self.y = y_m; self.orbit_phase = 0; self.orbit_counter += 1
                elif self.orbit_direction == -1 and self.y >= y_mx:
                    self.y = y_mx; self.orbit_phase = 2; self.orbit_counter += 1

            if hasattr(self, 'orbit_counter') and self.orbit_counter >= 4 and self.orbit_phase == self.orbit_start_phase:
                self.is_orbiting = False
                self.angle = random.uniform(0, 2 * math.pi)
                self.vx, self.vy = math.cos(self.angle) * base_spd, math.sin(self.angle) * base_spd
                if app and app.big_wall_active and not app.big_wall_pending_destroy:
                    app.big_wall_pending_destroy = True
                    app.big_wall_destroy_timer = 5.0
                self.finalize_transforms(settings)
                return

            self.angle = (self.angle + ((t_ang - self.angle + math.pi) % (2 * math.pi) - math.pi) * (dt * 12.0)) % (2 * math.pi)
            self.vx, self.vy = math.cos(self.angle) * c_spd, math.sin(self.angle) * c_spd
            self.finalize_transforms(settings)
            return

        n_x, n_y, r_sz = self.x + (self.vx * dt), self.y + (self.vy * dt), self.size - (self.visual_offset * 2)
        if walls:
            for i in range(len(walls) - 1, -1, -1):
                r = walls[i]["rect"]
                if (n_x + self.visual_offset < r[0] + r[2] and n_x + self.visual_offset + r_sz > r[0] and n_y + self.visual_offset < r[1] + r[3] and n_y + self.visual_offset + r_sz > r[1]):
                    if self.is_super:
                        if walls[i].get("is_big", False) and app:
                            app.big_wall_active = False
                            app.big_wall_pending_destroy = False
                            app.big_wall_timer = 0.0
                            for s in spider_list:
                                if s.is_orbiting:
                                    s.is_orbiting = False
                                    s.angle = random.uniform(0, 2 * math.pi)

                        if app and hasattr(app, 'particle_emitter'):
                            app.particle_emitter.spawn_shattered_wall(r, walls[i]["color"], self.size)

                        walls.pop(i)
                        if app and hasattr(app, 'redraw_walls'):
                            app.redraw_walls()
                        continue

                    if min(self.x + self.visual_offset + r_sz - r[0], r[0] + r[2] - (self.x + self.visual_offset)) < min(self.y + self.visual_offset + r_sz - r[1], r[1] + r[3] - (self.y + self.visual_offset)):
                        self.vx = -self.vx
                        n_x = r[0] - self.size + self.visual_offset - 2 if self.x + self.size/2 < r[0] + r[2]/2 else r[0] + r[2] - self.visual_offset + 2
                    else:
                        self.vy = -self.vy
                        n_y = r[1] - self.size + self.visual_offset - 2 if self.y + self.size/2 < r[1] + r[3]/2 else r[1] + r[3] - self.visual_offset + 2
                    self.angle = (math.atan2(self.vy, self.vx) + random.uniform(-0.1, 0.1)) % (2 * math.pi)
                    bounce_speed = max(base_spd, math.sqrt(self.vx**2 + self.vy**2) * 0.85)
                    self.vx = math.cos(self.angle) * bounce_speed
                    self.vy = math.sin(self.angle) * bounce_speed
                    self.x, self.y = n_x, n_y
                    self.finalize_transforms(settings)
                    return

        if self.is_super and app and hasattr(app, 'particle_emitter'):
            glow_sz = getattr(self, 'super_glow_size', self.size * 1.25)
            app.particle_emitter.spawn_super_trail(self.x, self.y, self.size, [1.0, 0.84, 0.0], glow_size=glow_sz)

        if app and app.gold_orb:
            orb_dist = math.sqrt(((app.gold_orb["x"] + app.gold_orb["size"]/2) - (n_x + self.size/2))**2 + ((app.gold_orb["y"] + app.gold_orb["size"]/2) - (n_y + self.size/2))**2)
            if orb_dist < ((self.size * 0.35) + (app.gold_orb["size"] / 2)):
                self.activate_super_power(15.0)
                app.gold_orb = None
                app.gold_orb_timer = 0.0
                app.gold_orb_spawn_time = random.uniform(20.0, 40.0)
                app.gold_orb_layer.canvas.clear()

        if spider_list:
            for other in list(spider_list):
                if not other or other.id == self.id or other.is_orbiting or other.is_grabbed:
                    continue
                dx = (other.x + other.size/2) - (n_x + self.size/2)
                dy = (other.y + other.size/2) - (n_y + self.size/2)
                distance = math.sqrt(dx**2 + dy**2)
                min_distance = (self.size * 0.35 + other.size * 0.35) - (self.visual_offset * 0.5 + other.visual_offset * 0.5)

                if not hasattr(self, '_active_passings'):
                    self._active_passings = set()
                if not hasattr(other, '_active_passings'):
                    other._active_passings = set()

                if distance < min_distance and distance > 0:
                    if self.is_super and not other.is_super:
                        try:
                            if app and hasattr(app, 'particle_emitter'):
                                app.particle_emitter.spawn_shattered_wall([other.x, other.y, other.size, other.size], [random.random(), random.random(), random.random(), 1.0], self.size)
                            other.canvas_widget.canvas.clear()
                            app.creature_layer.remove_widget(other.canvas_widget)
                            if other in spider_list:
                                spider_list.remove(other)
                        except:
                            pass
                        continue
                    elif not self.is_super and other.is_super:
                        try:
                            if app and hasattr(app, 'particle_emitter'):
                                app.particle_emitter.spawn_shattered_wall([self.x, self.y, self.size, self.size], [random.random(), random.random(), random.random(), 1.0], other.size)
                            self.canvas_widget.canvas.clear()
                            app.creature_layer.remove_widget(self.canvas_widget)
                            if self in spider_list:
                                spider_list.remove(self)
                        except:
                            pass
                        return
                    if other.id in self._active_passings or self.id in other._active_passings:
                        self.roll_speed = self.roll_angle = other.roll_speed = other.roll_angle = 0.0
                        continue
                    if random.random() < 0.50:
                        self._active_passings.add(other.id)
                        other._active_passings.add(self.id)
                        if app and hasattr(app, 'creature_layer'):
                            try:
                                app.creature_layer.remove_widget(self.canvas_widget)
                                app.creature_layer.add_widget(self.canvas_widget)
                            except:
                                pass
                        continue

                    nx_vec, ny_vec = dx / distance, dy / distance
                    tx_vec, ty_vec = -ny_vec, nx_vec
                    v1n = self.vx * nx_vec + self.vy * ny_vec
                    v1t = self.vx * tx_vec + self.vy * ty_vec
                    v2n = other.vx * nx_vec + other.vy * ny_vec
                    v2t = other.vx * tx_vec + other.vy * ty_vec

                    if self.is_flung:
                        other.is_flung = True
                    elif other.is_flung:
                        self.is_flung = True

                    self.vx, self.vy = v2n * nx_vec + v1t * tx_vec, v2n * ny_vec + v1t * ty_vec
                    other.vx, other.vy = v1n * nx_vec + v2t * tx_vec, v1n * ny_vec + v2t * ty_vec
                    self.angle, other.angle = math.atan2(self.vy, self.vx) % (2 * math.pi), math.atan2(other.vy, other.vx) % (2 * math.pi)

                    rel_vel_n = v1n - v2n
                    roll_intensity = max(20.0, abs(rel_vel_n) * 3.0)
                    self.roll_speed = -roll_intensity if rel_vel_n > 0 else roll_intensity
                    other.roll_speed = roll_intensity if rel_vel_n > 0 else -roll_intensity

                    overlap = min_distance - distance
                    n_x -= (overlap / 2) * nx_vec
                    n_y -= (overlap / 2) * ny_vec
                    other.x += (overlap / 2) * nx_vec
                    other.y += (overlap / 2) * ny_vec
                    self.x, self.y = n_x, n_y
                    self.finalize_transforms(settings)
                    return
                else:
                    if hasattr(self, '_active_passings') and other.id in self._active_passings:
                        self._active_passings.remove(other.id)
                    if hasattr(other, '_active_passings') and self.id in other._active_passings:
                        other._active_passings.remove(self.id)

        self.x, self.y = n_x, n_y
        sf_w, sf_h = (sw if sw > 100 else 1080), (sh if sh > 100 else 1920)
        if (self.x + self.size < -50 or self.x > sf_w + 50 or self.y + self.size < -50 or self.y > sf_h + 50):
            edge = random.randint(0, 3)
            if edge == 0:
                self.x = -self.size + 10; self.y = random.randint(0, max(1, sf_h - self.size))
            elif edge == 1:
                self.x = sf_w - 10; self.y = random.randint(0, max(1, sf_h - self.size))
            elif edge == 2:
                self.x = random.randint(0, max(1, sf_w - self.size)); self.y = -self.size + 10
            elif edge == 3:
                self.x = random.randint(0, max(1, sf_w - self.size)); self.y = sf_h - 10
            self.angle = random.uniform(0, 2 * math.pi)
            self.vx, self.vy = math.cos(self.angle) * base_spd, math.sin(self.angle) * base_spd

        if abs(self.roll_speed) > 1.0:
            self.roll_angle += self.roll_speed * dt
            self.roll_speed *= 0.5
        else:
            self.roll_speed = 0.0
            if abs(self.roll_angle) > 0.1:
                self.roll_angle += (0.0 - self.roll_angle) * (dt * 8.0)
            else:
                self.roll_angle = 0.0
        self.finalize_transforms(settings)

    def finalize_transforms(self, settings=None):
        app = App.get_running_app()
        st = settings if (settings and isinstance(settings, dict)) else (app.settings if app else {})
        local = st.get("folder_settings", {}).get(self.assigned_folder, st)
        self.canvas_widget.pos = (self.x, self.y)

        if hasattr(self, 'rect_mesh') and hasattr(self, 'rect_w'):
            self.rect_mesh.pos = (self.x + (self.size - self.rect_w)/2, self.y + (self.size - self.rect_h)/2)
        if hasattr(self, 'super_glow') and hasattr(self, 'rect_w'):
            glow_factor = 1.25 if self.size <= 150 else (1.1 + 22.5 / self.size)
            glow_w, glow_h = self.rect_w * glow_factor, self.rect_h * glow_factor
            self.super_glow.pos = (self.x + (self.size - glow_w)/2, self.y + (self.size - glow_h)/2)

        self.rot_transform.origin = self.scale_transform.origin = self.canvas_widget.center
        move_deg = math.degrees(self.angle) % 360
        facing_mode = local.get("image_facing", 0) % 4
        fx, fy = 1, 1

        if self.is_orbiting:
            base_offset = facing_mode * 90
            if facing_mode == 1:
                if self.orbit_phase == 0: t_ang = 90
                elif self.orbit_phase == 1: t_ang = 0
                elif self.orbit_phase == 2: t_ang = 270
                elif self.orbit_phase == 3: t_ang = 180
            elif facing_mode == 2:
                if self.orbit_phase == 0: t_ang = 180; fx, fy = -1, 1
                elif self.orbit_phase == 1: t_ang = 270; fx, fy = 1, -1
                elif self.orbit_phase == 2: t_ang = 0; fx, fy = -1, 1
                elif self.orbit_phase == 3: t_ang = 90; fx, fy = 1, -1
            elif facing_mode == 3:
                if self.orbit_phase == 0: t_ang = 270
                elif self.orbit_phase == 1: t_ang = 180
                elif self.orbit_phase == 2: t_ang = 90
                elif self.orbit_phase == 3: t_ang = 0
            else:
                deg = 180 if self.orbit_phase == 0 else (90 if self.orbit_phase == 1 else (0 if self.orbit_phase == 2 else 270))
                t_ang = deg - base_offset

            if hasattr(self, 'orbit_direction') and self.orbit_direction == -1:
                fx = -fx
        else:
            if facing_mode == 0:
                t_ang = move_deg
                if 90 < (t_ang % 360) <= 270:
                    t_ang = t_ang - 180; fx = -1
            elif facing_mode == 1:
                t_ang = move_deg - 90
                if 90 < (move_deg % 360) <= 270:
                    fx = -1
            elif facing_mode == 2:
                t_ang = move_deg - 180
                if not (90 < (move_deg % 360) <= 270):
                    t_ang = t_ang - 180; fx = -1
            elif facing_mode == 3:
                t_ang = move_deg - 270
                if 90 < (move_deg % 360) <= 270:
                    fx = -1

        self.rot_transform.angle = t_ang + (self.roll_angle * fx)
        self.scale_transform.x, self.scale_transform.y = fx, fy

        if self.textures and self.anim_time > (local.get("anim_speed", 80) / 1000.0) and self.total_frames > 0:
            if self.is_grabbed or math.sqrt(self.vx**2 + self.vy**2) > 5:
                self.current_frame = (self.current_frame + 1) % self.total_frames
                if hasattr(self, 'rect_mesh') and self.textures.get(self.current_frame):
                    self.rect_mesh.texture = self.textures.get(self.current_frame)
                self.anim_time = 0

if __name__ == '__main__':
    CreatureOverlayApp().run()



