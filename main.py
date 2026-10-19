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
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Scale, Rotate, Mesh, RoundedRectangle, Ellipse
from kivy.animation import Animation

# Android telefonda OpenGL motorunun kilitlenmemesi için opak yapıyoruz.
Window.clearcolor = (0.12, 0.12, 0.12, 1)

# --- ANDROID ARKA IŞIK VE TAM EKRAN (SYSTEMUI) KONTROL ALTYAPISI ---
try:
    from jnius import autoclass
    from android.runnable import run_on_ui_thread
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')
    
    # --- UYGULAMAYI TAM EKRANA ZORLAYAN SYSTEMUI AYARI ---
    View = autoclass('android.view.View')
    @run_on_ui_thread
    def force_fullscreen():
        window = activity.getWindow()
        window.getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        )
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False

class ParticleEmitter:
    """Yok olan duvarların parçacık efektlerini yöneten sınıf."""
    def __init__(self, canvas):
        self.canvas = canvas
        self.particles = []

    def spawn_shattered_wall(self, rect, color):
        x, y, w, h = rect
        effect_type = random.choice([0, 1, 2])
        num_particles = random.randint(30, 50)
        
        for _ in range(num_particles):
            p_x = random.uniform(x, x + w)
            p_y = random.uniform(y, y + h)
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 250)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            life = 1.5  
            decay = random.uniform(1.0, 2.0) 
            size = random.uniform(8, 20)
            
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

    def spawn_super_trail(self, x, y, size, color):
        num_particles = random.randint(1, 2)
        for _ in range(num_particles):
            p_x = x + random.uniform(0, size)
            p_y = y + random.uniform(0, size)
            vx = random.uniform(-15, 15)
            vy = random.uniform(-15, 15)
            
            life = 0.6  
            decay = random.uniform(1.2, 1.8)
            p_size = random.uniform(6, 12)
            
            r = min(1.0, max(0.8, color[0] + random.uniform(-0.1, 0.1)))
            g = min(1.0, max(0.7, color[1] + random.uniform(-0.1, 0.1)))
            b = random.uniform(0.0, 0.3)
            p_color = [r, g, b, 1.0]
            
            p_data = {
                "type": 2,  
                "x": p_x, "y": p_y,
                "vx": vx, "vy": vy,
                "size": p_size,
                "color": p_color,
                "life": life,
                "decay": decay,
                "rot": random.uniform(0, 360),
                "rot_speed": random.uniform(-45, 45)
            }
            self.particles.append(p_data)

    def update_particles(self, dt):
        self.particles = [p for p in self.particles if p["life"] > 0]
        with self.canvas:
            for p in self.particles:
                p["life"] -= dt * p["decay"]
                if p["life"] <= 0:
                    continue
                p["color"][3] = max(0.0, p["life"])
                
                if p["type"] == 2:
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["vx"] *= 0.92  
                    p["vy"] *= 0.92
                    p["size"] += dt * 25.0  
                    Color(*p["color"])
                    Rectangle(pos=(p["x"] - p["size"]/2, p["y"] - p["size"]/2), size=(p["size"], p["size"]))
                elif p["type"] == 0:
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["rot"] += p["rot_speed"] * dt
                    Color(*p["color"])
                    PushMatrix()
                    Rotate(angle=p["rot"], origin=(p["x"], p["y"]), axis=(0, 0, 1))
                    Rectangle(pos=(p["x"] - p["size"]/2, p["y"] - p["size"]/2), size=(p["size"], p["size"]))
                    PopMatrix()
                elif p["type"] == 1:
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["rot"] += p["rot_speed"] * dt
                    Color(*p["color"])
                    PushMatrix()
                    Rotate(angle=p["rot"], origin=(p["x"], p["y"]), axis=(0, 0, 1))
                    s = p["size"] / 2
                    vertices = [
                        p["x"], p["y"] + s, 0, 0,
                        p["x"] - s, p["y"] - s, 0, 0,
                        p["x"] + s, p["y"] - s, 0, 0
                    ]
                    indices = [0, 1, 2]
                    Mesh(vertices=vertices, indices=indices, mode='triangles')
                    PopMatrix()

class CreatureOverlayApp(App):
    def build(self):
        self.title = "Spider Android - Kivy Saf OpenGL Overlay"
        
        # --- HAKKINDA EKRANI IŞILTI DEĞİŞKENLERİ SIFIRLAMA ---
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

        self.layout.add_widget(self.bg_layer)
        self.layout.add_widget(self.wall_layer)
        self.layout.add_widget(self.gold_orb_layer) 
        self.layout.add_widget(self.particle_layer) 
        self.layout.add_widget(self.creature_layer)
        self.layout.add_widget(self.ui_layer)
        self.layout.add_widget(self.toggle_layer)
        self.wall_layer.bind(on_touch_down=self.on_wall_touch)

        self.particle_emitter = ParticleEmitter(self.particle_layer.canvas)

        self.CONFIG_FILE = "settings_android.json"
        self.settings = {
            "animation_folder_idx": 0, "start_program": 0, 
            "creature_size": 120, "anim_speed": 80, "move_speed": 4, "max_creatures": 6,
            "image_facing": 0, "visual_offset": 15, "screen_awake": 0, "folder_settings": {}  
        }
        if "super_speed_mult" not in self.settings:
            self.settings["super_speed_mult"] = 3.0  
        self.load_settings()

        self.spider_list = []
        self.walls = [] 
        self.spider_active = True if self.settings["start_program"] == 1 else False
        self.current_view = "main"
        self.ui_visible = True
        
        self.gold_orb = None 
        self.gold_orb_timer = 0.0
        self.gold_orb_spawn_time = 20.0 

        self.animation_folders = self.get_available_animation_folders()
        self.sync_active_folder_settings()
        
        self.rebuild_toggle_button()
        self.rebuild_ui()
        self.update_background_image()
        
        self.apply_screen_awake_status()
        
        Clock.schedule_interval(self.update, 1.0 / 60.0)
        self.next_wall_time = random.uniform(6.0, 12.0)
        self.wall_timer = 0
        self.big_wall_timer = 0
        self.big_wall_interval = 120.0  
        
        Window.bind(on_resize=self.on_window_resize)
        
        if ANDROID_AVAILABLE:
            try:
                force_fullscreen()
            except Exception as e:
                print(f"Tam Ekran Zorlama Hatası: {e}")
                
        return self.layout

    def sync_active_folder_settings(self):
        current_folder = self.animation_folders[self.settings["animation_folder_idx"] % len(self.animation_folders)]
        if current_folder not in self.settings["folder_settings"]:
            self.settings["folder_settings"][current_folder] = {
                "move_speed": self.settings.get("move_speed", 4),
                "anim_speed": self.settings.get("anim_speed", 80),
                "max_creatures": self.settings.get("max_creatures", 6),
                "image_facing": self.settings.get("image_facing", 0),
                "visual_offset": self.settings.get("visual_offset", 15),
                "creature_size": self.settings.get("creature_size", 120),
                "bg_image_idx": self.settings.get("bg_image_idx", 0),
                "super_speed_mult": self.settings.get("super_speed_mult", 3.0)  
            }
        
        local = self.settings["folder_settings"][current_folder]
        for key in ["move_speed", "anim_speed", "max_creatures", "image_facing", "visual_offset", "creature_size", "bg_image_idx", "super_speed_mult"]:
            if key in local:
                self.settings[key] = local[key]

    def apply_screen_awake_status(self):
        if not ANDROID_AVAILABLE:
            return
        @run_on_ui_thread
        def _set_flag():
            if self.settings.get("screen_awake", 0) == 1:
                activity.getWindow().addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
            else:
                activity.getWindow().clearFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
        try: _set_flag()
        except Exception as e: print(f"Ekran Uyandırma Hatası: {e}")

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
            except: pass

    def save_settings(self):
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f: 
                json.dump(self.settings, f)
        except: pass

    def get_available_animation_folders(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        anims_root = os.path.join(base_dir, "anims")
        folders = ["default"]
        if os.path.exists(anims_root):
            try:
                subfolders = sorted([d for d in os.listdir(anims_root) if os.path.isdir(os.path.join(anims_root, d))])
                for sf in subfolders:
                    if sf != "default": folders.append(sf)
            except: pass
        return folders

    def update_background_image(self):
        try:
            self.bg_layer.canvas.clear()
            base_dir = os.path.dirname(os.path.abspath(__file__))
            chosen_folder = self.settings["animation_folder_idx"] % len(self.animation_folders)
            folder_name = self.animation_folders[chosen_folder]
            
            theme_dir = os.path.join(base_dir, "anims") if folder_name == "default" else os.path.join(base_dir, "anims", folder_name)
            is_portrait = Window.height >= Window.width
            
            valid_bg_count = 1  
            while True:
                suffix = str(valid_bg_count)
                if os.path.exists(os.path.join(theme_dir, f"bg{suffix}_v.png")) or os.path.exists(os.path.join(theme_dir, f"bg{suffix}_h.png")):
                    valid_bg_count += 1
                else: break
            
            local = self.settings["folder_settings"].get(folder_name, self.settings)
            bg_idx = local.get("bg_image_idx", 0) % valid_bg_count
            suffix = "" if bg_idx == 0 else str(bg_idx)
            
            bg_path = os.path.join(theme_dir, f"bg{suffix}_v.png" if is_portrait else f"bg{suffix}_h.png")
            if not os.path.exists(bg_path): bg_path = os.path.join(theme_dir, "bg.png")
            if not os.path.exists(bg_path): bg_path = os.path.join(base_dir, "anims", "bg.png")
                
            if os.path.exists(bg_path):
                bg_texture = CoreImage(bg_path).texture
                bg_texture.wrap = 'repeat'
                with self.bg_layer.canvas:
                    Color(1, 1, 1, 1)
                    Rectangle(pos=(0, 0), size=(Window.width, Window.height), texture=bg_texture)
        except Exception as e: print(f"Arka Plan Yükleme Hatası: {e}")

    def on_window_resize(self, window, width, height):
        self.SCREEN_WIDTH = width if width > 100 else 1080
        self.SCREEN_HEIGHT = height if height > 100 else 1920
        self.update_background_image()
        if hasattr(self, 'ui_layer'): self.rebuild_ui()
        if hasattr(self, 'toggle_layer'): self.rebuild_toggle_button()

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

    def rebuild_ui(self):
        self.ui_layer.clear_widgets()
        if not self.ui_visible: return
        btn_h = 0.052

        def create_visual_button(text, bg_color, y_pos, on_press_callback):
            btn = Button(text=text, size_hint=(0.6, btn_h), pos_hint={'x': 0.2, 'y': y_pos}, font_size='16sp', background_color=(0, 0, 0, 0), markup=True)
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
            title_text = "Yaratık yürüyor" if self.spider_active else "Yaratık duruyor"
            title_color = (0.13, 0.77, 0.36, 1) if self.spider_active else (1, 1, 1, 1)
            self.title_label = Label(text=title_text, size_hint=(0.8, 0.06), pos_hint={'x': 0.1, 'y': 0.8}, font_size='20sp', color=title_color, bold=True)
            with self.title_label.canvas.before:
                Color(0.05, 0.05, 0.05, 0.5)
                self.title_bg = Rectangle(pos=self.title_label.pos, size=self.title_label.size)
            def _update_title_bg(instance, value):
                self.title_bg.pos = instance.pos
                self.title_bg.size = instance.size
            self.title_label.bind(pos=_update_title_bg, size=_update_title_bg)
            self.ui_layer.add_widget(self.title_label)

            status_text = "Hareketi durdur" if self.spider_active else "Hareketi başlat"
            self.status_btn = create_visual_button(status_text, (0.93, 0.26, 0.26, 1) if self.spider_active else (0.13, 0.77, 0.36, 1), 0.60, self.toggle_spider)
            self.ui_layer.add_widget(self.status_btn)
            
            self.ui_layer.add_widget(create_visual_button("Ayarlar", (0.2, 0.25, 0.33, 1), 0.50, lambda x: self.switch_view("settings")))
            self.ui_layer.add_widget(create_visual_button("Hakkında", (0.2, 0.5, 0.6, 1), 0.40, lambda x: self.switch_view("about")))
            self.ui_layer.add_widget(create_visual_button("Çıkış", (0.93, 0.26, 0.26, 1), 0.30, lambda x: sys.exit()))
            
        elif self.current_view == "settings":
            current_folder = self.animation_folders[self.settings["animation_folder_idx"] % len(self.animation_folders)]
            local = self.settings["folder_settings"][current_folder]

            def _setup_setting_row(label, btn_m, btn_p, y_pos, bg_m_color=(0.2, 0.25, 0.33, 1), bg_p_color=(0.2, 0.25, 0.33, 1)):
                btn_m.size_hint = (0.12, btn_h)
                btn_m.pos_hint = {'x': 0.65, 'y': y_pos}
                btn_m.font_size = '18sp'
                btn_m.background_color = (0, 0, 0, 0)
                
                btn_p.size_hint = (0.12, btn_h)
                btn_p.pos_hint = {'x': 0.79, 'y': y_pos}
                btn_p.font_size = '18sp'
                btn_p.background_color = (0, 0, 0, 0)
                
                label.size_hint = (0.48, btn_h)
                label.pos_hint = {'x': 0.12, 'y': y_pos}
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

            display_folder_name = "[color=45b870][b]VARSAYILAN[/b][/color]" if current_folder == "default" else f"[b]{current_folder.upper()}[/b]"
            self.type_label = Label(text=f"Tür (Type): {display_folder_name}", markup=True)
            self.t_minus, self.t_plus = Button(text="<"), Button(text=">")
            _setup_setting_row(self.type_label, self.t_minus, self.t_plus, 0.82, (0.27, 0.72, 0.44, 1) if current_folder == "default" else (0.2, 0.25, 0.33, 1), (0.27, 0.72, 0.44, 1) if current_folder == "default" else (0.2, 0.25, 0.33, 1))
            self.t_minus.bind(on_press=lambda x: self.change_creature_type_step(-1))
            self.t_plus.bind(on_press=lambda x: self.change_creature_type_step(1))
            self.ui_layer.add_widget(self.type_label)
            self.ui_layer.add_widget(self.t_minus)
            self.ui_layer.add_widget(self.t_plus)

            facing_modes = ["0° (SAĞ)", "90° (YUKARI)", "180° (SOL)", "270° (AŞAĞI)"]
            current_mode_idx = local.get("image_facing", 0) % 4
            current_mode_text = facing_modes[current_mode_idx]
            self.face_label = Label(text=f"Img Face: [color=4080e0][b]{current_mode_text}[/b][/color]", markup=True)
            self.f_minus, self.f_plus = Button(text="<"), Button(text=">")
            _setup_setting_row(self.face_label, self.f_minus, self.f_plus, 0.738, (0.25, 0.50, 0.88, 1), (0.93, 0.26, 0.26, 1))
            self.f_minus.bind(on_press=lambda x: self.change_setting_face_step(-1))
            self.f_plus.bind(on_press=lambda x: self.change_setting_face_step(1))
            self.ui_layer.add_widget(self.face_label)
            self.ui_layer.add_widget(self.f_minus)
            self.ui_layer.add_widget(self.f_plus)

            bg_display_text = "Varsayılan (bg)" if self.settings.get("bg_image_idx", 0) == 0 else f"Tema {self.settings.get('bg_image_idx', 0)}"
            self.bg_img_label = Label(text=f"Arka Plan (BG): [color=e0a040][b]{bg_display_text}[/b][/color]", markup=True)
            self.bg_minus, self.bg_plus = Button(text="<"), Button(text=">")
            _setup_setting_row(self.bg_img_label, self.bg_minus, self.bg_plus, 0.656, (0.7, 0.5, 0.2, 1), (0.7, 0.5, 0.2, 1))
            self.bg_minus.bind(on_press=lambda x: self.change_bg_image_step(-1))
            self.bg_plus.bind(on_press=lambda x: self.change_bg_image_step(1))
            self.ui_layer.add_widget(self.bg_img_label)
            self.ui_layer.add_widget(self.bg_minus)
            self.ui_layer.add_widget(self.bg_plus)

            self.size_label = Label(text=f"Boyut (Size): {local.get('creature_size', 120)} px")
            self.sz_minus, self.sz_plus = Button(text="-"), Button(text="+")
            _setup_setting_row(self.size_label, self.sz_minus, self.sz_plus, 0.574)
            self._check_button_edge_colors("creature_size", 40, 400, self.sz_minus, self.sz_plus)
            self.sz_minus.bind(on_press=lambda x: self.update_stat_live("creature_size", -10, 40, 400, self.size_label, "Boyut (Size): ", " px", self.sz_minus, self.sz_plus))
            self.sz_plus.bind(on_press=lambda x: self.update_stat_live("creature_size", 10, 40, 400, self.size_label, "Boyut (Size): ", " px", self.sz_minus, self.sz_plus))
            self.ui_layer.add_widget(self.size_label)
            self.ui_layer.add_widget(self.sz_minus)
            self.ui_layer.add_widget(self.sz_plus)
            
            self.speed_label = Label(text=f"Hız (Speed): {local.get('move_speed', 4)}")
            self.s_minus, self.s_plus = Button(text="-"), Button(text="+")
            _setup_setting_row(self.speed_label, self.s_minus, self.s_plus, 0.492)
            self._check_button_edge_colors("move_speed", 1, 15, self.s_minus, self.s_plus)
            self.s_minus.bind(on_press=lambda x: self.update_stat_live("move_speed", -1, 1, 15, self.speed_label, "Hız (Speed): ", "", self.s_minus, self.s_plus))
            self.s_plus.bind(on_press=lambda x: self.update_stat_live("move_speed", 1, 1, 15, self.speed_label, "Hız (Speed): ", "", self.s_minus, self.s_plus))
            self.ui_layer.add_widget(self.speed_label)
            self.ui_layer.add_widget(self.s_minus)
            self.ui_layer.add_widget(self.s_plus)

            self.anim_label = Label(text=f"Anim Hızı: {local.get('anim_speed', 80)} ms")
            self.a_minus, self.a_plus = Button(text="-"), Button(text="+")
            _setup_setting_row(self.anim_label, self.a_minus, self.a_plus, 0.41)
            self._check_button_edge_colors("anim_speed", 20, 300, self.a_minus, self.a_plus)
            self.a_minus.bind(on_press=lambda x: self.update_stat_live("anim_speed", -10, 20, 300, self.anim_label, "Anim Hızı: ", " ms", self.a_minus, self.a_plus))
            self.a_plus.bind(on_press=lambda x: self.update_stat_live("anim_speed", 10, 20, 300, self.anim_label, "Anim Hızı: ", " ms", self.a_minus, self.a_plus))
            self.ui_layer.add_widget(self.anim_label)
            self.ui_layer.add_widget(self.a_minus)
            self.ui_layer.add_widget(self.a_plus)

            self.count_label = Label(text=f"Yaratık Sayısı: {local.get('max_creatures', 6)}")
            self.c_minus, self.c_plus = Button(text="-"), Button(text="+")
            _setup_setting_row(self.count_label, self.c_minus, self.c_plus, 0.328)
            self._check_button_edge_colors("max_creatures", 1, 30, self.c_minus, self.c_plus)
            self.c_minus.bind(on_press=lambda x: self.update_stat_live("max_creatures", -1, 1, 30, self.count_label, "Yaratık Sayısı: ", "", self.c_minus, self.c_plus))
            self.c_plus.bind(on_press=lambda x: self.update_stat_live("max_creatures", 1, 1, 30, self.count_label, "Yaratık Sayısı: ", "", self.c_minus, self.c_plus))
            self.ui_layer.add_widget(self.count_label)
            self.ui_layer.add_widget(self.c_minus)
            self.ui_layer.add_widget(self.c_plus)

            self.offset_label = Label(text=f"Ofset (Margin): {local.get('visual_offset', 15)} px")
            self.o_minus, self.o_plus = Button(text="-"), Button(text="+")
            _setup_setting_row(self.offset_label, self.o_minus, self.o_plus, 0.246)
            self._check_button_edge_colors("visual_offset", -10, 50, self.o_minus, self.o_plus)
            self.o_minus.bind(on_press=lambda x: self.update_stat_live("visual_offset", -5, -10, 50, self.offset_label, "Ofset (Margin): ", " px", self.o_minus, self.o_plus))
            self.o_plus.bind(on_press=lambda x: self.update_stat_live("visual_offset", 5, -10, 50, self.offset_label, "Ofset (Margin): ", " px", self.o_minus, self.o_plus))
            self.ui_layer.add_widget(self.offset_label)
            self.ui_layer.add_widget(self.o_minus)
            self.ui_layer.add_widget(self.o_plus)

            current_mult = local.get("super_speed_mult", 3.0)  
            self.mult_label = Label(text=f"Süper Hız (Mult): {current_mult:.1f} x")
            self.m_minus, self.m_plus = Button(text="-"), Button(text="+")
            _setup_setting_row(self.mult_label, self.m_minus, self.m_plus, 0.164, (0.7, 0.5, 0.2, 1), (0.7, 0.5, 0.2, 1))
            
            if current_mult <= 1.5: 
                self.m_minus.canvas.before.children[0].rgba = (0.93, 0.26, 0.26, 1)
            if current_mult >= 5.0: 
                self.m_plus.canvas.before.children[0].rgba = (0.13, 0.77, 0.36, 1)
            
            def _update_mult(amount, min_v, max_v):
                val = max(min_v, min(local.get("super_speed_mult", 3.0) + amount, max_v))  
                local["super_speed_mult"] = round(val, 1)  
                self.settings["super_speed_mult"] = local["super_speed_mult"]
                self.save_settings()
                self.rebuild_ui()
                
            self.m_minus.bind(on_press=lambda x: _update_mult(-0.5, 1.5, 5.0))
            self.m_plus.bind(on_press=lambda x: _update_mult(0.5, 1.5, 5.0))
            
            self.ui_layer.add_widget(self.mult_label)
            self.ui_layer.add_widget(self.m_minus)
            self.ui_layer.add_widget(self.m_plus)

            is_awake = self.settings.get("screen_awake", 0) == 1
            self.awake_btn = create_visual_button("", (0.18, 0.68, 0.38, 1) if is_awake else (0.7, 0.4, 0.2, 1), 0.092, self.toggle_screen_awake)
            self.awake_text_label = Label(text="Ekranı Açık Tut", font_size='16sp', bold=True, color=(1, 1, 1, 1), halign='center', valign='middle', size_hint=(None, None))
            
            def _align_custom_elements(instance, value):
                icon_x = instance.x + instance.width - 160
                if hasattr(instance, 'icon_rect'):
                    instance.icon_rect.pos = (icon_x, instance.y + (instance.height - 120) / 2)
                self.awake_text_label.size = (icon_x - instance.x, instance.height)
                self.awake_text_label.pos = (instance.x, instance.y)
                self.awake_text_label.text_size = (icon_x - instance.x, instance.height)
            
            with self.awake_btn.canvas.after:
                Color(1, 1, 1, 1)
                icon_path = "awake.png" if is_awake else "sleep.png"
                if os.path.exists(icon_path):
                    self.awake_btn.icon_rect = Rectangle(texture=CoreImage(icon_path).texture, size=(120, 120), pos=(0, 0))
            
            self.awake_btn.bind(pos=_align_custom_elements, size=_align_custom_elements)
            self.ui_layer.add_widget(self.awake_btn)
            self.ui_layer.add_widget(self.awake_text_label)
            self.ui_layer.add_widget(create_visual_button("Ana Menü", (0.13, 0.77, 0.36, 1), 0.02, lambda x: self.switch_view("main")))

        elif self.current_view == "about":
            self.about_sparkles.clear()
            self.sparkle_spawn_timer = 0.0
            
            # 1. ÖNCE METİN ETİKETİNİ OLUŞTURUP EKLEYELİM (En altta kalacak)
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
                padding=(40, 40), size_hint=(0.86, 0.48), pos_hint={'x': 0.07, 'y': 0.32}
            )
            self.about_label.bind(size=lambda s, w: setattr(s, 'text_size', s.size))
            
            with self.about_label.canvas.before:
                Color(0.05, 0.05, 0.05, 0.85) 
                self.about_label.bg_rect = RoundedRectangle(pos=self.about_label.pos, size=self.about_label.size, radius=[15])
            
            def _update_about_bg(inst, val): 
                inst.bg_rect.pos = inst.pos
                inst.bg_rect.size = inst.size
            self.about_label.bind(pos=_update_about_bg, size=_update_about_bg)
            
            self.ui_layer.add_widget(self.about_label)

            # 2. SONRA PARILTI KATMANINI EKLEYELİM (Yazının ve siyah arka planın ÜSTÜNDE görünecek)
            if getattr(self, 'sparkle_layer', None) is not None and self.sparkle_layer in self.ui_layer.children:
                self.ui_layer.remove_widget(self.sparkle_layer)
                
            self.sparkle_layer = Widget(size_hint=(0.86, 0.48), pos_hint={'x': 0.07, 'y': 0.32})
            self.ui_layer.add_widget(self.sparkle_layer)
            
            # 3. ANA MENÜ BUTONUNU EKLEYELİM
            self.ui_layer.add_widget(create_visual_button("Ana Menü", (0.13, 0.77, 0.36, 1), 0.16, lambda x: self.switch_view("main")))

    def switch_view(self, view_name):
        # Sayfa her değiştiğinde parıltı listesini sıfırla
        self.about_sparkles.clear()
        self.sparkle_spawn_timer = 0.0
        if getattr(self, 'sparkle_layer', None) is not None:
            self.sparkle_layer.canvas.clear()
            
        self.current_view = view_name
        self.rebuild_ui()

    def _check_button_edge_colors(self, key, min_v, max_v, btn_m, btn_p):
        current_folder = self.animation_folders[self.settings["animation_folder_idx"] % len(self.animation_folders)]
        local = self.settings["folder_settings"][current_folder]
        current_value = local.get(key, min_v)

        if current_value <= min_v: 
            btn_m.canvas.before.children[0].rgba = (0.93, 0.26, 0.26, 1)  
        else: 
            btn_m.canvas.before.children[0].rgba = (0.2, 0.25, 0.33, 1)   

        if current_value >= max_v: 
            btn_p.canvas.before.children[0].rgba = (0.13, 0.77, 0.36, 1)  
        else: 
            btn_p.canvas.before.children[0].rgba = (0.2, 0.25, 0.33, 1)   

    def update_stat_live(self, key, amount, min_v, max_v, label_obj, prefix, suffix="", btn_m=None, btn_p=None):
        current_folder = self.animation_folders[self.settings["animation_folder_idx"] % len(self.animation_folders)]
        local = self.settings["folder_settings"][current_folder]
        
        local[key] = max(min_v, min(local.get(key, min_v) + amount, max_v))
        self.settings[key] = local[key]
        self.save_settings()
        
        label_obj.text = f"{prefix}{local[key]}{suffix}"
        if btn_m and btn_p: 
            self._check_button_edge_colors(key, min_v, max_v, btn_m, btn_p)
        
        if key == "max_creatures":
            while len(self.spider_list) > local[key]:
                last_spider = self.spider_list.pop()
                try:
                    last_spider.canvas_widget.canvas.clear()
                    self.creature_layer.remove_widget(last_spider.canvas_widget)
                except Exception as e: 
                    print(f"Yaratık Canlı Silme Hatası: {e}")
        elif key == "visual_offset":
            for spider in self.spider_list: 
                spider.visual_offset = local[key]
        elif key == "creature_size":
            for spider in self.spider_list: 
                spider.update_size(local[key])
        self.rebuild_ui()

    def toggle_ui_visibility(self, instance):
        self.ui_visible = not self.ui_visible
        self.rebuild_toggle_button()
        self.rebuild_ui()

    def toggle_spider(self, instance):
        self.spider_active = not self.spider_active
        if not self.spider_active:
            for spider in list(self.spider_list):
                try:
                    spider.canvas_widget.canvas.clear()
                    self.creature_layer.remove_widget(spider.canvas_widget)
                except: pass
            self.spider_list.clear()
            self.walls.clear()
            self.gold_orb = None
            try: 
                self.wall_layer.canvas.clear()
                self.gold_orb_layer.canvas.clear()
            except: pass
        self.rebuild_ui()

    def change_creature_type_step(self, direction):
        idx = self.settings.get("animation_folder_idx", 0)
        self.settings["animation_folder_idx"] = (idx + direction + len(self.animation_folders)) % len(self.animation_folders)
        self.sync_active_folder_settings()
        self.save_settings()
        self.update_background_image()
        self.rebuild_ui()
        current_folder = self.animation_folders[self.settings["animation_folder_idx"] % len(self.animation_folders)]
        local_max = self.settings["folder_settings"].get(current_folder, self.settings).get("max_creatures", 6)
        
        while len(self.spider_list) > local_max:
            last_spider = self.spider_list.pop()
            try:
                last_spider.canvas_widget.canvas.clear()
                self.creature_layer.remove_widget(last_spider.canvas_widget)
            except Exception as e: 
                print(f"Tür Değişimi Canlı Silme Hatası: {e}")
        for spider in list(self.spider_list):
            try:
                spider.update_size(self.settings.get("creature_size", 120))
                spider.reload_textures(self.settings, self.animation_folders)
            except: pass

    def change_setting_face_step(self, direction):
        current_folder = self.animation_folders[self.settings["animation_folder_idx"] % len(self.animation_folders)]
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
        chosen_folder = self.settings["animation_folder_idx"] % len(self.animation_folders)
        folder_name = self.animation_folders[chosen_folder]
        theme_dir = os.path.join(base_dir, "anims") if folder_name == "default" else os.path.join(base_dir, "anims", folder_name)
        
        valid_bg_count = 1
        while True:
            suffix = str(valid_bg_count)
            if os.path.exists(os.path.join(theme_dir, f"bg{suffix}_v.png")) or os.path.exists(os.path.join(theme_dir, f"bg{suffix}_h.png")): 
                valid_bg_count += 1
            else: break
        current_folder = self.animation_folders[self.settings["animation_folder_idx"] % len(self.animation_folders)]
        local = self.settings["folder_settings"][current_folder]
        local["bg_image_idx"] = (local.get("bg_image_idx", 0) + direction + valid_bg_count) % valid_bg_count
        self.settings["bg_image_idx"] = local["bg_image_idx"]
        self.save_settings()
        self.update_background_image()
        self.rebuild_ui()

    def on_start(self):
        self.SCREEN_WIDTH = Window.width if (Window.width and Window.width > 100) else 1080
        self.SCREEN_HEIGHT = Window.height if (Window.height and Window.height > 100) else 1920

    def on_wall_touch(self, widget, touch):
        if self.ui_visible and touch.y < self.SCREEN_HEIGHT * 0.90:
            if touch.x > self.SCREEN_WIDTH * 0.1 and touch.x < self.SCREEN_WIDTH * 0.9:
                if self.current_view == "main" and touch.y > self.SCREEN_HEIGHT * 0.30: return 
                if self.current_view == "settings" and touch.y > self.SCREEN_HEIGHT * 0.02: return
                if self.current_view == "about" and touch.y > self.SCREEN_HEIGHT * 0.15: return 

        for i, wall in enumerate(list(self.walls)):
            if not wall or "rect" not in wall or len(wall["rect"]) < 4: continue
            r = wall["rect"]
            if r[0] <= touch.x <= r[0] + r[2] and r[1] <= touch.y <= r[1] + r[3]:
                if wall.get("is_big", False):
                    for s in self.spider_list:
                        if s.is_orbiting: 
                            s.is_orbiting = False
                            s.angle = random.uniform(0, 2 * math.pi)
                self.particle_emitter.spawn_shattered_wall(r, wall["color"])
                self.walls.pop(i)
                self.redraw_walls()
                return True
        return False

    def spawn_random_wall(self):
        if len(self.walls) >= 2: return
        is_hz = random.choice([True, False])
        w = random.randint(200, 450) if is_hz else random.randint(40, 90)
        h = random.randint(40, 90) if is_hz else random.randint(200, 450)
        x = random.randint(50, max(51, self.SCREEN_WIDTH - w - 50))
        y = random.randint(120, max(121, self.SCREEN_HEIGHT - h - 120))
        
        for wall in list(self.walls):
            if not wall or "rect" not in wall: continue
            r = wall["rect"]
            if (x - 120 < r[0] + r[2] and x + w + 120 > r[0] and y - 120 < r[1] + r[3] and y + h + 120 > r[1]): return
        self.walls.append({"rect": [x, y, w, h], "color": (random.random(), random.random(), random.random(), 1.0), "life": 0.0, "is_big": False})
        self.redraw_walls()
        
    def redraw_walls(self):
        try:
            self.wall_layer.canvas.clear()
            if not self.walls: return
            with self.wall_layer.canvas:
                for wall in list(self.walls):
                    if not wall or "rect" not in wall: continue
                    r = wall["rect"]
                    Color(*wall["color"])
                    Rectangle(pos=(r[0], r[1]), size=(r[2], r[3]))
        except: pass

    def spawn_big_central_wall(self):
        w, h = 300, 300
        x = (self.SCREEN_WIDTH - w) / 2 + random.randint(-50, 50)
        y = (self.SCREEN_HEIGHT - h) / 2 + random.randint(-50, 50)
        self.walls.append({"rect": [x, y, w, h], "color": (0.85, 0.18, 0.18, 1.0), "life": 0.0, "is_big": True})
        self.redraw_walls()
        avail = [s for s in self.spider_list if not s.is_orbiting]
        if avail: random.choice(avail).start_orbiting(x, y, w, h)

    def spawn_gold_orb(self):
        size = 50.0
        x = random.uniform(50, max(50, self.SCREEN_WIDTH - size - 50))
        y = random.uniform(150, max(150, self.SCREEN_HEIGHT - size - 150))
        self.gold_orb = {"x": x, "y": y, "size": size}
        self.redraw_gold_orb()

    def redraw_gold_orb(self):
        self.gold_orb_layer.canvas.clear()
        if not self.gold_orb: return
        with self.gold_orb_layer.canvas:
            Color(1.0, 0.84, 0.0, 0.4)
            ext = self.gold_orb["size"] * 1.4
            Ellipse(pos=(self.gold_orb["x"] - (ext - self.gold_orb["size"])/2, self.gold_orb["y"] - (ext - self.gold_orb["size"])/2), size=(ext, ext))
            Color(1.0, 0.84, 0.0, 1.0)
            Ellipse(pos=(self.gold_orb["x"], self.gold_orb["y"]), size=(self.gold_orb["size"], self.gold_orb["size"]))

    def update(self, dt):
        self.particle_layer.canvas.clear()
        self.particle_emitter.update_particles(dt)

        # --- HAKKINDA EKRANI IŞILTI MOTORU ---
        if self.current_view == "about" and getattr(self, 'sparkle_layer', None) is not None and self.ui_visible:
            self.sparkle_layer.canvas.clear()
            self.sparkle_spawn_timer += dt
            
            if self.sparkle_spawn_timer >= 0.25:  # Yıldızların belirme sıklığı
                self.sparkle_spawn_timer = 0.0
                if len(self.about_sparkles) < 15:  # Ekrandaki anlık maksimum aktif yıldız sayısı
                    lx, ly = self.sparkle_layer.pos
                    lw, lh = self.sparkle_layer.size
                    
                    sp_x = random.uniform(lx + 40, lx + lw - 40)
                    sp_y = random.uniform(ly + 40, ly + lh - 40)
                    base_color = random.choice([[1.0, 0.85, 0.2], [1.0, 1.0, 1.0]]) # Sarı veya Beyaz
                    sparkle_form = random.choice(["plus", "star"]) # + veya * formu
                    
                    self.about_sparkles.append({
                        "x": sp_x, "y": sp_y, "size": random.uniform(12, 22),
                        "base_color": base_color, "form": sparkle_form, 
                        "state": "fade_in", "alpha": 0.0, "speed": random.uniform(1.5, 3.0)
                    })

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
                    thick = sz / 10  # Keskinlik ve incelik ayarı (Daireleşmeyi önler)
                    
                    if sp["form"] == "plus":
                        # --- "x" Karakteri Formu (45 Derece Döndürülmüş Artı) ---
                        PushMatrix()
                        Rotate(angle=45, origin=(sp["x"], sp["y"]), axis=(0, 0, 1))
                        Rectangle(pos=(sp["x"] - sz/2, sp["y"] - thick/2), size=(sz, thick))
                        Rectangle(pos=(sp["x"] - thick/2, sp["y"] - sz/2), size=(thick, sz))
                        PopMatrix()
                    
                    elif sp["form"] == "star":
                        # --- Keskin "*" Karakteri Formu ---
                        # Yatay ve Dikey kollar (+)
                        Rectangle(pos=(sp["x"] - sz/2, sp["y"] - thick/2), size=(sz, thick))
                        Rectangle(pos=(sp["x"] - thick/2, sp["y"] - sz/2), size=(thick, sz))
                        
                        # Çapraz kollar (x)
                        PushMatrix()
                        Rotate(angle=45, origin=(sp["x"], sp["y"]), axis=(0, 0, 1))
                        Rectangle(pos=(sp["x"] - sz/2, sp["y"] - thick/2), size=(sz, thick))
                        Rectangle(pos=(sp["x"] - thick/2, sp["y"] - sz/2), size=(thick, sz))
                        PopMatrix()

        if not self.spider_active: return
        sw = Window.width if (Window.width and Window.width > 100) else self.SCREEN_WIDTH
        sh = Window.height if (Window.height and Window.height > 100) else self.SCREEN_HEIGHT

        current_creature_count = len(self.spider_list)
        if current_creature_count >= 6:
            if not self.gold_orb:
                self.gold_orb_timer += dt
                if self.gold_orb_timer >= self.gold_orb_spawn_time:
                    self.spawn_gold_orb()
                    self.gold_orb_timer = 0.0
                    self.gold_orb_spawn_time = random.uniform(20.0, 40.0)
        else:
            self.gold_orb_timer = 0.0  
            if self.gold_orb:
                self.gold_orb = None  
                self.gold_orb_layer.canvas.clear()

        self.big_wall_timer += dt
        if self.big_wall_timer >= self.big_wall_interval: 
            self.big_wall_timer = 0
            self.spawn_big_central_wall()
            
        self.wall_timer += dt
        if self.wall_timer > self.next_wall_time: 
            self.spawn_random_wall()
            self.wall_timer = 0
            self.next_wall_time = random.uniform(6.0, 12.0)

        w_ch = False
        for i in range(len(self.walls) - 1, -1, -1):
            self.walls[i]["life"] += dt
            if self.walls[i]["life"] >= 30.0:
                if self.walls[i].get("is_big", False):
                    for s in self.spider_list:
                        if s.is_orbiting: s.is_orbiting = False; s.angle = random.uniform(0, 2 * math.pi)
                self.particle_emitter.spawn_shattered_wall(self.walls[i]["rect"], self.walls[i]["color"])
                self.walls.pop(i)
                w_ch = True
        if w_ch: self.redraw_walls()

        current_folder = self.animation_folders[self.settings["animation_folder_idx"] % len(self.animation_folders)]
        local_max = self.settings.get("folder_settings", {}).get(current_folder, self.settings).get("max_creatures", 6)
        
        if len(self.spider_list) < local_max:
            new_spider = KivySpiderEntity(self.settings, sw, sh, self.animation_folders)
            self.spider_list.append(new_spider)
            self.creature_layer.add_widget(new_spider.canvas_widget)

        for spider in list(self.spider_list):
            try:
                spider.update_entity(dt, sw, sh, self.settings, self.walls, 0, self.spider_list)
                if self.gold_orb:
                    dist = math.sqrt(((spider.x + spider.size/2) - (self.gold_orb["x"] + self.gold_orb["size"]/2))**2 + ((spider.y + spider.size/2) - (self.gold_orb["y"] + self.gold_orb["size"]/2))**2)
                    if dist < (spider.size / 2 + self.gold_orb["size"] / 2 - spider.visual_offset):
                        spider.activate_super_power(15.0)
                        self.gold_orb = None
                        self.gold_orb_layer.canvas.clear()
            except Exception as e: print(f"Döngü hatası: {e}")

class KivySpiderEntity:
    _id_counter = 0
    def __init__(self, settings, sw, sh, animation_folders):
        KivySpiderEntity._id_counter += 1
        self.id = KivySpiderEntity._id_counter
        current_folder = animation_folders[settings["animation_folder_idx"] % len(animation_folders)]
        local = settings["folder_settings"].get(current_folder, settings)
        
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
        self.last_touch_x = self.last_touch_y = 0.0
        self.current_frame = self.anim_time = 0
        self.is_orbiting = False
        self.visual_offset = local.get("visual_offset", 15) 
        self.is_super = False
        self.super_timer = 0.0
        self.textures = {}
        self.reload_textures(settings, animation_folders)
        #(mevcut init kodlarının sonu)
        self.is_flung = False
        self.touch_history = []  
        
        # --- YUVARLANMA (ROLL) EFEKTİ DEĞİŞKENLERİ ---
        self.roll_angle = 0.0   # Anlık yuvarlanma açısı (derece)
        self.roll_speed = 0.0   # Dönüş hızı (derece/saniye)
        
        self.setup_canvas()

    def setup_canvas(self):
        self.canvas_widget.canvas.clear()
        with self.canvas_widget.canvas:
            PushMatrix()
            self.rot_transform = Rotate(angle=0, axis=(0, 0, 1), origin=self.canvas_widget.center)
            self.scale_transform = Scale(1, 1, 1, origin=self.canvas_widget.center)
            if self.is_super:
                Color(1.0, 0.84, 0.0, 0.5)
                self.super_glow = Ellipse(pos=(self.x, self.y), size=(self.size, self.size))
            Color(1, 1, 1, 1)
            self.rect_mesh = Rectangle(texture=self.textures.get(0) if self.textures else None, pos=(self.x, self.y), size=self.canvas_widget.size)
            PopMatrix()
        self.canvas_widget.unbind(on_touch_down=self.on_touch_down, on_touch_move=self.on_touch_move, on_touch_up=self.on_touch_up)
        self.canvas_widget.bind(on_touch_down=self.on_touch_down, on_touch_move=self.on_touch_move, on_touch_up=self.on_touch_up)

    def activate_super_power(self, duration=15.0):
        self.is_super = True; self.super_timer = duration; self.setup_canvas()

    def update_size(self, new_size):
        self.size = new_size; self.canvas_widget.size = (self.size, self.size); self.setup_canvas()

    def on_touch_down(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.is_grabbed = True; self.is_orbiting = False
            self.vx = self.vy = 0; self.last_touch_x = touch.x; self.last_touch_y = touch.y
            return True
        return False
        
    def on_touch_move(self, widget, touch):
        if self.is_grabbed:
            import time
            self.touch_history.append((time.time(), touch.x, touch.y))
            if len(self.touch_history) > 4: self.touch_history.pop(0)
            self.x, self.y = touch.x - self.size / 2, touch.y - self.size / 2
            self.last_touch_x, self.last_touch_y = touch.x, touch.y
            self.finalize_transforms(None)
            return True
        return False

    def on_touch_up(self, widget, touch):
        if self.is_grabbed:
            self.is_grabbed = False
            if len(self.touch_history) >= 2:
                t1, x1, y1 = self.touch_history[0]
                t2, x2, y2 = self.touch_history[-1]
                dt = t2 - t1
                if dt > 0:
                    self.vx = (x2 - x1) / dt
                    self.vy = (y2 - y1) / dt
                    self.vx *= 1.5; self.vy *= 1.5
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

    def start_orbiting(self, wx, wy, ww, wh):
        if self.is_grabbed: return
        self.is_orbiting = True; self.orbit_wx, self.orbit_wy, self.orbit_ww, self.orbit_wh = wx, wy, ww, wh
        self.orbit_phase = 0; self.x, self.y = wx - 15, wy - self.size - 5 + self.visual_offset

    def reload_textures(self, settings, animation_folders):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        f_name = animation_folders[settings.get("animation_folder_idx", 0) % len(animation_folders)]
        self.anim_path_root = os.path.join(base_dir, "anims" if f_name == "default" else f"anims/{f_name}")
        self.total_frames = 0; self.textures = {}
        local = settings["folder_settings"].get(f_name, settings)
        
        if os.path.exists(self.anim_path_root):
            try:
                valid_idx = sorted([int(f.split('.')[0]) for f in os.listdir(self.anim_path_root) if f.lower().endswith('.png') and f.split('.')[0].isdigit() and f.lower() not in [f"bg{local.get('bg_image_idx', 0)}_v.png", f"bg{local.get('bg_image_idx', 0)}_h.png", 'bg.png']])
                self.total_frames = len(valid_idx)
                for idx, num in enumerate(valid_idx):
                    p = os.path.join(self.anim_path_root, f"{num}.png")
                    if os.path.exists(p): self.textures[idx] = CoreImage(p).texture
            except: self.total_frames = 0
        if self.total_frames == 0:
            for i in range(4):
                p = os.path.join(self.anim_path_root, f"{i}.png")
                if os.path.exists(p): self.textures[self.total_frames] = CoreImage(p).texture; self.total_frames += 1
        self.current_frame = 0; self.visual_offset = local.get("visual_offset", 15)

    def update_entity(self, dt, sw, sh, settings, walls, count_bw, spider_list):
        if self.is_grabbed: return
        self.anim_time += dt
        
        # --- YUVARLANMA SÖNÜMLEME MOTORU ---
        if abs(self.roll_speed) > 0.1:
            self.roll_angle += self.roll_speed * dt
            self.roll_speed *= 0.5  # Her karede %8 sönümlenerek durur
        else:
            self.roll_speed = 0.0
            # Açıyı yavaşça sıfıra veya en yakın katına eşitlemek yerine serbest bırakabiliriz, 
            # finalize_transforms bunu yön açısıyla birleştirecektir.

        if self.is_super:
            self.super_timer -= dt
            # ... (mevcut süper güç kodları aynen devam ediyor)

            if self.super_timer <= 0: self.is_super = False; self.setup_canvas()

        app = App.get_running_app()
        f_name = app.animation_folders[settings["animation_folder_idx"] % len(app.animation_folders)]
        local = settings["folder_settings"].get(f_name, settings)

        if self.is_super:
            mult = local.get("super_speed_mult", 3.0) 
            base_spd = local.get("move_speed", 4) * 30 * mult
        else: base_spd = local.get("move_speed", 4) * 30        

        if self.is_flung:
            current_speed = math.sqrt(self.vx**2 + self.vy**2)
            if current_speed > base_spd:
                self.vx *= 0.975; self.vy *= 0.975
                self.angle = math.atan2(self.vy, self.vx) % (2 * math.pi)
            else: self.is_flung = False
        else:
            self.vx = math.cos(self.angle) * base_spd
            self.vy = math.sin(self.angle) * base_spd

        if self.is_orbiting:
            x_m, x_mx = self.orbit_wx - self.size + 15 + self.visual_offset, self.orbit_wx + self.orbit_ww - 15 - self.visual_offset
            y_m, y_mx = self.orbit_wy - self.size + 15 + self.visual_offset, self.orbit_wy + self.orbit_wh - 15 - self.visual_offset
            t_ang = math.pi if self.orbit_phase == 0 else (math.pi*0.5 if self.orbit_phase == 1 else (0.0 if self.orbit_phase == 2 else math.pi*1.5))
            c_spd = base_spd * max(0.5, 1.0 - (abs((t_ang - self.angle + math.pi) % (2 * math.pi) - math.pi) / (math.pi * 0.5)) * 0.5)

            if self.orbit_phase == 0:
                self.y = y_m; self.x -= c_spd * dt
                if self.x <= x_m: self.x = x_m; self.orbit_phase = 1
            elif self.orbit_phase == 1:
                self.x = x_m; self.y += c_spd * dt
                if self.y >= y_mx: self.y = y_mx; self.orbit_phase = 2
            elif self.orbit_phase == 2:
                self.y = y_mx; self.x += c_spd * dt
                if self.x >= x_mx: self.x = x_mx; self.orbit_phase = 3
            elif self.orbit_phase == 3:
                self.x = x_mx
                self.y -= c_spd * dt
                if self.y <= y_m:
                    self.y = y_m
                    self.is_orbiting = False
                    self.vx, self.vy = math.cos(self.angle) * base_spd, math.sin(self.angle) * base_spd
                    self.finalize_transforms(settings)
                    return
            self.angle = (self.angle + ((t_ang - self.angle + math.pi) % (2 * math.pi) - math.pi) * (dt * 8.0)) % (2 * math.pi)
            self.vx, self.vy = math.cos(self.angle) * c_spd, math.sin(self.angle) * c_spd
            self.finalize_transforms(settings)
            return

        n_x, n_y, r_sz = self.x + (self.vx * dt), self.y + (self.vy * dt), self.size - (self.visual_offset * 2)

        if walls:
            for i in range(len(walls) - 1, -1, -1):
                r = walls[i]["rect"]
                if (n_x + self.visual_offset < r[0] + r[2] and n_x + self.visual_offset + r_sz > r[0] and n_y + self.visual_offset < r[1] + r[3] and n_y + self.visual_offset + r_sz > r[1]):
                    if self.is_super: 
                        app.particle_emitter.spawn_shattered_wall(r, walls[i]["color"])
                        walls.pop(i)
                        app.redraw_walls()
                        continue
                    if min(self.x + self.visual_offset + r_sz - r[0], r[0] + r[2] - (self.x + self.visual_offset)) < min(self.y + self.visual_offset + r_sz - r[1], r[1] + r[3] - (self.y + self.visual_offset)):
                        self.vx = -self.vx
                        n_x = r[0] - self.size + self.visual_offset - 2 if self.x + self.size/2 < r[0] + r[2]/2 else r[0] + r[2] - self.visual_offset + 2
                    else:
                        self.vy = -self.vy
                        n_y = r[1] - self.size + self.visual_offset - 2 if self.y + self.size/2 < r[1] + r[3]/2 else r[1] + r[3] - self.visual_offset + 2
                    self.angle = (math.atan2(self.vy, self.vx) + random.uniform(-0.1, 0.1)) % (2 * math.pi)
                    current_speed = math.sqrt(self.vx**2 + self.vy**2)
                    bounce_speed = max(base_spd, current_speed * 0.85) 
                    self.vx = math.cos(self.angle) * bounce_speed
                    self.vy = math.sin(self.angle) * bounce_speed
                    self.x, self.y = n_x, n_y
                    self.finalize_transforms(settings)
                    return

        if self.is_super and app and hasattr(app, 'particle_emitter'):
            app.particle_emitter.spawn_super_trail(self.x, self.y, self.size, [1.0, 0.84, 0.0])

        if spider_list:
            for other in list(spider_list):
                if not other or other.id == self.id or other.is_orbiting or other.is_grabbed: continue
                self_center_x = n_x + self.size / 2
                self_center_y = n_y + self.size / 2
                other_center_x = other.x + other.size / 2
                other_center_y = other.y + other.size / 2
                dx = other_center_x - self_center_x
                dy = other_center_y - self_center_y
                distance = math.sqrt(dx**2 + dy**2)
                min_distance = (self.size / 2 + other.size / 2) - (self.visual_offset + other.visual_offset)
                
                if distance < min_distance and distance > 0:
                    if self.is_super and not other.is_super:
                        try: 
                            creature_rect = [other.x, other.y, other.size, other.size]
                            creature_color = [random.random(), random.random(), random.random(), 1.0]
                            if app and hasattr(app, 'particle_emitter'): app.particle_emitter.spawn_shattered_wall(creature_rect, creature_color)
                            other.canvas_widget.canvas.clear()
                            app.creature_layer.remove_widget(other.canvas_widget)
                            if other in spider_list: spider_list.remove(other)
                        except Exception as e: print(f"Yaratık Parçalama Hatası: {e}")
                        continue
                    elif not self.is_super and other.is_super:
                        try: 
                            my_rect = [self.x, self.y, self.size, self.size]
                            my_color = [random.random(), random.random(), random.random(), 1.0]
                            if app and hasattr(app, 'particle_emitter'): app.particle_emitter.spawn_shattered_wall(my_rect, my_color)
                            self.canvas_widget.canvas.clear()
                            app.creature_layer.remove_widget(self.canvas_widget)
                            if self in spider_list: spider_list.remove(self)
                        except Exception as e: print(f"Yaratık Parçalama Hatası: {e}")
                        return

                    nx_vec = dx / distance
                    ny_vec = dy / distance
                    tx_vec = -ny_vec
                    ty_vec = nx_vec
                    
                    v1n = self.vx * nx_vec + self.vy * ny_vec
                    v1t = self.vx * tx_vec + self.vy * ty_vec
                    v2n = other.vx * nx_vec + other.vy * ny_vec
                    v2t = other.vx * tx_vec + other.vy * ty_vec
                    
                    v1n_new = v2n
                    v2n_new = v1n
                    
                    if self.is_flung: other.is_flung = True
                    elif other.is_flung: self.is_flung = True
                    
                    self.vx = v1n_new * nx_vec + v1t * tx_vec
                    self.vy = v1n_new * ny_vec + v1t * ty_vec
                    other.vx = v2n_new * nx_vec + v2t * tx_vec
                    other.vy = v2n_new * ny_vec + v2t * ty_vec
                    
                    self.angle = math.atan2(self.vy, self.vx) % (2 * math.pi)
                    other.angle = math.atan2(other.vy, other.vx) % (2 * math.pi)
                    
                    # --- ANLIK YUVARLANMA (ROLL) MOTORUNU BAŞLATMA ---
                    # Bağıl çarpışma hızı şiddetinde dönme hızı tetikliyoruz
                    rel_vel_n = v1n - v2n
                    roll_intensity = max(400.0, abs(rel_vel_n) * 3.0) 
                    
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

        self.x, self.y = n_x, n_y
        sf_w = sw if sw > 100 else 1080
        sf_h = sh if sh > 100 else 1920
        out_of_bounds = False

        if (self.x + self.size < -50 or self.x > sf_w + 50 or self.y + self.size < -50 or self.y > sf_h + 50):
            out_of_bounds = True

        if out_of_bounds:
            edge = random.randint(0, 3)
            if edge == 0:
                self.x = -self.size + 10
                self.y = random.randint(0, max(1, sf_h - self.size))
            elif edge == 1:
                self.x = sf_w - 10
                self.y = random.randint(0, max(1, sf_h - self.size))
            elif edge == 2:
                self.x = random.randint(0, max(1, sf_w - self.size))
                self.y = -self.size + 10
            elif edge == 3:
                self.x = random.randint(0, max(1, sf_w - self.size))
                self.y = sf_h - 10

            self.angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(self.angle) * base_spd
            self.vy = math.sin(self.angle) * base_spd
            
        # --- YUVARLANMA DURUM KONTROLÜ VE YAVAŞÇA DÜZELME MOTORU ---
        if abs(self.roll_speed) > 1.0:
            self.roll_angle += self.roll_speed * dt
            self.roll_speed *= 0.5  # Dönüş hızı zamanla sıfıra yaklaşır
        else:
            # Yuvarlanma hızı tamamen bittiğinde açıyı yumuşakça (Lerp) 0 dereceye geri çekiyoruz
            self.roll_speed = 0.0
            if abs(self.roll_angle) > 0.1:
                self.roll_angle += (0.0 - self.roll_angle) * (dt * 8.0) # Adım adım düzelir
            else:
                self.roll_angle = 0.0  # Tamamen sıfırlanıp düz yürüyüşe geçer

        self.finalize_transforms(settings)

    def finalize_transforms(self, settings=None):
        app = App.get_running_app()
        st = settings if (settings and isinstance(settings, dict)) else (app.settings if app else {})
        local = st.get("folder_settings", {}).get(app.animation_folders[st.get("animation_folder_idx", 0) % len(app.animation_folders)], st) if (app and hasattr(app, 'animation_folders')) else st

        self.canvas_widget.pos = (self.x, self.y)
        if hasattr(self, 'rect_mesh'): self.rect_mesh.pos = (self.x, self.y)
        if hasattr(self, 'super_glow'): self.super_glow.pos = (self.x, self.y)
            
        self.rot_transform.origin = self.scale_transform.origin = self.canvas_widget.center
        move_deg = math.degrees(self.angle) % 360
        facing_mode = local.get("image_facing", 0) % 4
        base_offset = facing_mode * 90
        fx, fy = 1, 1

        if self.is_orbiting:
            if facing_mode == 2:
                if self.orbit_phase == 0: t_ang = 180; fx, fy = -1, 1
                elif self.orbit_phase == 1: t_ang = 270; fx, fy = 1, -1
                elif self.orbit_phase == 2: t_ang = 0; fx, fy = -1, 1
                elif self.orbit_phase == 3: t_ang = 90; fx, fy = 1, -1
            else:
                if self.orbit_phase == 0: deg = 180
                elif self.orbit_phase == 1: deg = 90
                elif self.orbit_phase == 2: deg = 0
                elif self.orbit_phase == 3: deg = 270
                t_ang = deg - base_offset
                fx, fy = 1, 1
        else:
            t_ang = move_deg - base_offset
            check_angle = (move_deg - base_offset) % 360
            if 90 < check_angle <= 270:
                t_ang = t_ang - 180
                fx = -1

        # --- DINAMIK YUVARLANMA AÇISINI EKLİYORUZ ---
        self.rot_transform.angle = t_ang + (self.roll_angle * fx)
        self.scale_transform.x, self.scale_transform.y = fx, fy
        
        if self.textures and self.anim_time > (local.get("anim_speed", 80) / 1000.0) and self.total_frames > 0:
            if self.is_grabbed or math.sqrt(self.vx**2 + self.vy**2) > 5:
                self.current_frame = (self.current_frame + 1) % self.total_frames
                if hasattr(self, 'rect_mesh'): self.rect_mesh.texture = self.textures.get(self.current_frame)
                self.anim_time = 0

if __name__ == '__main__':
    CreatureOverlayApp().run()

