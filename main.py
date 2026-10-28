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

    def spawn_super_trail(self, x, y, size, color):
        num_particles = random.randint(10, 18)
        cx = x + size / 2
        cy = y + size / 2
        for _ in range(num_particles):
            p_x = cx + random.uniform(-size*0.5, size*0.5)
            p_y = cy + random.uniform(-size*0.5, size*0.5)
            vx = random.uniform(-60, 60)
            vy = random.uniform(-60, 60)
            
            life = 0.35  
            decay = random.uniform(0.3, 0.6)
            p_size = random.uniform(14, 26) * (size / 120.0)
            
            r = random.uniform(0.4, 1.0)
            g = random.uniform(0.4, 1.0)
            b = random.uniform(0.4, 1.0)
            max_c = max(r, g, b)
            p_color = [r/max_c, g/max_c, b/max_c, 1.0]
            
            p_data = {
                "type": 2,  
                "x": p_x, "y": p_y,
                "vx": vx, "vy": vy,
                "size": p_size,
                "color": p_color,
                "life": life,
                "decay": decay,
                "rot": random.uniform(0, 360),
                "rot_speed": random.uniform(-90, 90)
            }
            self.particles.append(p_data)

    def update_particles(self, dt):
        self.particles = [p for p in self.particles if p["life"] > 0]
        with self.canvas:
            for p in self.particles:
                p["life"] -= dt * p["decay"]
                if p["life"] <= 0: continue
                p["color"][3] = max(0.0, p["life"])
                
                if p["type"] == 2:
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["vx"] *= 0.94  
                    p["vy"] *= 0.94
                    p["size"] += dt * 10.0  
                    Color(p["color"][0], p["color"][1], p["color"][2], p["color"][3])
                    Rectangle(pos=(p["x"] - p["size"]/2, p["y"] - p["size"]/8), size=(p["size"], p["size"]/4))
                    Rectangle(pos=(p["x"] - p["size"]/8, p["y"] - p["size"]/2), size=(p["size"]/4, p["size"]))
                    
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

        self.layout.add_widget(self.bg_layer)
        self.layout.add_widget(self.gold_orb_layer) 
        self.layout.add_widget(self.wall_layer)
        self.layout.add_widget(self.particle_layer) 
        self.layout.add_widget(self.creature_layer)
        self.layout.add_widget(self.ui_layer)
        self.layout.add_widget(self.toggle_layer)
        self.wall_layer.bind(on_touch_down=self.on_wall_touch)

        self.particle_emitter = ParticleEmitter(self.particle_layer.canvas)

        self.CONFIG_FILE = "settings_android.json"
        self.settings = {
            "animation_folder_idx": 0, "animation_folder_idx2": 0, "start_program": 0, 
            "creature_size": 120, "anim_speed": 80, "move_speed": 4, "max_creatures": 6,
            "max_creatures2": 6, "type2_enabled": 1, "image_facing": 0, "visual_offset": 15, 
            "screen_awake": 0, "folder_settings": {}, "super_speed_mult": 3.0,
            "current_hab_idx1": 0,  
            "current_hab_idx2": 0   
        }
        self.load_settings()
        self.habitats_list = ["KARA", "HAVA", "DENIZ", "UZAY", "DIGER"]
        self.spider_list = []
        self.walls = [] 
        self.spider_active = True if self.settings["start_program"] == 1 else False
        self.current_view = "main"
        self.active_settings_tab = "visual"
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
        self.big_wall_active = False       
        self.big_wall_pending_destroy = False 
        self.big_wall_destroy_timer = 0.0  
        self.wall_timer = 0
        self.big_wall_timer = 0
        self.big_wall_interval = 120.0  
     
        Window.bind(on_resize=self.on_window_resize)
        
        if ANDROID_AVAILABLE:
            try: force_fullscreen()
            except: pass
                
        return self.layout

    def sync_active_folder_settings(self):
        filtered1 = self.get_filtered_folders_by_slot(1)
        filtered2 = self.get_filtered_folders_by_slot(2)
        current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
        current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]
        
        for folder in [current_folder, current_folder2]:
            if folder not in self.settings["folder_settings"]:
                self.settings["folder_settings"][folder] = {
                    "move_speed": self.settings.get("move_speed", 4),
                    "anim_speed": self.settings.get("anim_speed", 80),
                    "max_creatures": self.settings.get("max_creatures", 6),
                    "max_creatures2": self.settings.get("max_creatures2", 6),
                    "type2_enabled": self.settings.get("type2_enabled", 1),
                    "image_facing": self.settings.get("image_facing", 0),
                    "visual_offset": self.settings.get("visual_offset", 15),
                    "creature_size": self.settings.get("creature_size", 120),
                    "bg_image_idx": self.settings.get("bg_image_idx", 0),
                    "super_speed_mult": self.settings.get("super_speed_mult", 3.0)  
                }
        
        local = self.settings["folder_settings"][current_folder]
        for key in ["move_speed", "anim_speed", "max_creatures", "max_creatures2", "type2_enabled", "image_facing", "visual_offset", "creature_size", "bg_image_idx", "super_speed_mult"]:
            if key in local:
                self.settings[key] = local[key]

    def get_folder_habitat(self, folder_name):
        if folder_name == "default":
            return "DIGER"
        if "/" in folder_name:
            prefix = folder_name.split("/")[0].upper()
            if prefix in ["KARA", "HAVA", "DENIZ", "UZAY"]:
                return prefix
        fn = folder_name.lower()
        if fn.startswith("kara") or "orumcek" in fn or "bocek" in fn:
            return "KARA"
        elif fn.startswith("hava") or "kus" in fn or "ucak" in fn or "ari" in fn:
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
        return filtered if filtered else ["default"]

    def get_filtered_folders_by_current_habitat(self):
        return self.get_filtered_folders_by_slot(1)

    def clear_all_creatures_on_habitat_change(self):
        for spider in list(self.spider_list):
            try:
                spider.canvas_widget.canvas.clear()
                self.creature_layer.remove_widget(spider.canvas_widget)
            except: pass
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
        try: _set_flag()
        except: pass

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
        habitats = ["kara", "hava", "deniz", "uzay"]
        
        if os.path.exists(anims_root):
            try:
                for hab in habitats:
                    hab_path = os.path.join(anims_root, hab)
                    if os.path.exists(hab_path) and os.path.isdir(hab_path):
                        subfolders = sorted([d for d in os.listdir(hab_path) if os.path.isdir(os.path.join(hab_path, d))])
                        for sf in subfolders:
                            folders.append(f"{hab}/{sf}")
            except Exception as e:
                print(f"Klasör tarama hatası: {e}")
        return folders

    def update_background_image(self):
        try:
            self.bg_layer.canvas.clear()
            base_dir = os.path.dirname(os.path.abspath(__file__))
            filtered1 = self.get_filtered_folders_by_slot(1)
            chosen_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
            theme_dir = os.path.join(base_dir, "anims") if chosen_folder == "default" else os.path.join(base_dir, "anims", chosen_folder)
            is_portrait = Window.height >= Window.width
            valid_bg_count = 1  
            while True:
                suffix = str(valid_bg_count)
                if os.path.exists(os.path.join(theme_dir, f"bg{suffix}_v.png")) or os.path.exists(os.path.join(theme_dir, f"bg{suffix}_h.png")):
                    valid_bg_count += 1
                else: break
            local = self.settings["folder_settings"].get(chosen_folder, self.settings)
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
        except: pass

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
            filtered1 = self.get_filtered_folders_by_slot(1)
            filtered2 = self.get_filtered_folders_by_slot(2)
            current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
            current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]
            
            if self.active_settings_tab == "type2":
                target_folder = current_folder2
            else:
                target_folder = current_folder
                
            local1 = self.settings["folder_settings"].setdefault(target_folder, {
                "move_speed": 4, "anim_speed": 80, "max_creatures": 6, "max_creatures2": 6, "type2_enabled": 1,
                "image_facing": 0, "visual_offset": 15, "creature_size": 120, "bg_image_idx": 0, "super_speed_mult": 3.0
            })
            is_type2_on = self.settings.get("type2_enabled", 1) == 1
            
            tab_y = 0.82
            
            btn_tab1 = Button(text="Genel/Çevre", size_hint=(0.26, 0.05), pos_hint={'x': 0.08, 'y': tab_y}, font_size='11sp', bold=True, background_color=(0, 0, 0, 0))
            with btn_tab1.canvas.before:
                Color(*(0.13, 0.77, 0.36, 1) if self.active_settings_tab == "visual" else (0.2, 0.25, 0.33, 1))
                btn_tab1.bg_rect = RoundedRectangle(pos=btn_tab1.pos, size=btn_tab1.size, radius=[10])
                
            btn_tab2 = Button(text="1. Tür Ayar", size_hint=(0.26, 0.05), pos_hint={'x': 0.37, 'y': tab_y}, font_size='11sp', bold=True, background_color=(0, 0, 0, 0))
            with btn_tab2.canvas.before:
                Color(*(0.13, 0.77, 0.36, 1) if self.active_settings_tab == "type1" else (0.2, 0.25, 0.33, 1))
                btn_tab2.bg_rect = RoundedRectangle(pos=btn_tab2.pos, size=btn_tab2.size, radius=[10])
                
            btn_tab3 = Button(text="2. Tür Ayar", size_hint=(0.26, 0.05), pos_hint={'x': 0.66, 'y': tab_y}, font_size='11sp', bold=True, background_color=(0, 0, 0, 0))
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
            if self.active_settings_tab == "visual":
                hab_idx1 = self.settings.get("current_hab_idx1", 0) % len(self.habitats_list)
                current_hab1 = self.habitats_list[hab_idx1]
                self.hab1_label = Label(text=f"[Secili] Sınıf: [color=45b870][b]{current_hab1}[/b][/color]", markup=True)
                self.h1_m, self.h1_p = Button(text="<"), Button(text=">")
                _setup_setting_row(self.hab1_label, self.h1_m, self.h1_p, 0.76)
                self.h1_m.bind(on_press=lambda x: self.change_habitat_class_step(-1, 1))
                self.h1_p.bind(on_press=lambda x: self.change_habitat_class_step(1, 1))
                self.ui_layer.add_widget(self.hab1_label)
                self.ui_layer.add_widget(self.h1_m)
                self.ui_layer.add_widget(self.h1_p)

                self.type_label = Label(text=f"└ 1. Alt Tür: [b]{current_folder.upper()}[/b]", markup=True)
                self.t_minus, self.t_plus = Button(text="<"), Button(text=">")
                _setup_setting_row(self.type_label, self.t_minus, self.t_plus, 0.70)
                self.t_minus.bind(on_press=lambda x: self.change_creature_type_step(-1, 1))
                self.t_plus.bind(on_press=lambda x: self.change_creature_type_step(1, 1))
                self.ui_layer.add_widget(self.type_label)
                self.ui_layer.add_widget(self.t_minus)
                self.ui_layer.add_widget(self.t_plus)

                t2_status_text = "[color=13c444][b]AKTİF[/b][/color]" if is_type2_on else "[color=ed4242][b]PASİF[/b][/color]"
                self.t2_toggle_label = Label(text=f"2. Tür Durumu: {t2_status_text}", markup=True)
                self.t2_left_btn, self.t2_right_btn = Button(text="<"), Button(text=">")
                _setup_setting_row(self.t2_toggle_label, self.t2_left_btn, self.t2_right_btn, 0.62)
                
                def _toggle_type2_switch():
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
                                except: pass
                    self.rebuild_ui()

                self.t2_left_btn.bind(on_press=lambda x: _toggle_type2_switch())
                self.t2_right_btn.bind(on_press=lambda x: _toggle_type2_switch())
                self.ui_layer.add_widget(self.t2_toggle_label)
                self.ui_layer.add_widget(self.t2_left_btn)
                self.ui_layer.add_widget(self.t2_right_btn)
                if is_type2_on:
                    filtered2 = self.get_filtered_folders_by_slot(2)
                    current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]
                    self.type2_label = Label(text=f"└ 2. Alt Tür: [b]{current_folder2.upper()}[/b]", markup=True)
                    self.t2_m, self.t2_p = Button(text="<"), Button(text=">")
                    _setup_setting_row(self.type2_label, self.t2_m, self.t2_p, 0.54)
                    self.t2_m.bind(on_press=lambda x: self.change_creature_type_step(-1, 2))
                    self.t2_p.bind(on_press=lambda x: self.change_creature_type_step(1, 2))
                    self.ui_layer.add_widget(self.type2_label)
                    self.ui_layer.add_widget(self.t2_m)
                    self.ui_layer.add_widget(self.t2_p)
                    y_pos_bg = 0.46
                else:
                    y_pos_bg = 0.54

                bg_display_text = "Varsayılan (bg)" if self.settings.get("bg_image_idx", 0) == 0 else f"Tema {self.settings.get('bg_image_idx', 0)}"
                self.bg_img_label = Label(text=f"Arka Plan: [color=e0a040][b]{bg_display_text}[/b][/color]", markup=True)
                self.bg_minus, self.bg_plus = Button(text="<"), Button(text=">")
                _setup_setting_row(self.bg_img_label, self.bg_minus, self.bg_plus, y_pos_bg, (0.7, 0.5, 0.2, 1), (0.7, 0.5, 0.2, 1))
                self.bg_minus.bind(on_press=lambda x: self.change_bg_image_step(-1))
                self.bg_plus.bind(on_press=lambda x: self.change_bg_image_step(1))
                self.ui_layer.add_widget(self.bg_img_label)
                self.ui_layer.add_widget(self.bg_minus)
                self.ui_layer.add_widget(self.bg_plus)
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

                face1_deg = local1.get("image_facing", 0) * 90
                self.face1_label = Label(text=f"1. Tür Görsel Açısı: {face1_deg}°")
                self.f1_minus, self.f1_plus = Button(text="<"), Button(text=">")
                _setup_setting_row(self.face1_label, self.f1_minus, self.f1_plus, 0.40)
                self.f1_minus.bind(on_press=lambda x: [self.change_setting_face_step(-1), self.rebuild_ui()])
                self.f1_plus.bind(on_press=lambda x: [self.change_setting_face_step(1), self.rebuild_ui()])
                self.ui_layer.add_widget(self.face1_label)
                self.ui_layer.add_widget(self.f1_minus)
                self.ui_layer.add_widget(self.f1_plus)
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

                self.count2_label = Label(text=f"2. Tür Toplam Sayı: {local1.get('max_creatures2', 6)}")
                self.c2_minus, self.c2_plus = Button(text="-"), Button(text="+")
                _setup_setting_row(self.count2_label, self.c2_minus, self.c2_plus, 0.48)
                self._check_button_edge_colors_v2("max_creatures2", 1, 30, self.c2_minus, self.c2_plus, local1)
                self.c2_minus.bind(on_press=lambda x: self.update_stat_live("max_creatures2", -1, 1, 30, self.count2_label, "2. Tür Toplam Sayı: ", "", self.c2_minus, self.c2_plus, target_type=2))
                self.c2_plus.bind(on_press=lambda x: self.update_stat_live("max_creatures2", 1, 1, 30, self.count2_label, "2. Tür Toplam Sayı: ", "", self.c2_minus, self.c2_plus, target_type=2))
                self.ui_layer.add_widget(self.count2_label)
                self.ui_layer.add_widget(self.c2_minus)
                self.ui_layer.add_widget(self.c2_plus)

                face2_deg = local1.get("image_facing", 0) * 90
                self.face2_label = Label(text=f"2. Tür Görsel Açısı: {face2_deg}°")
                self.f2_minus, self.f2_plus = Button(text="<"), Button(text=">")
                _setup_setting_row(self.face2_label, self.f2_minus, self.f2_plus, 0.40)
                
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
            self.ui_layer.add_widget(create_visual_button("Ana Menü", (0.13, 0.77, 0.36, 1), 0.04, lambda x: self.switch_view("main")))
        elif self.current_view == "about":
            self.about_sparkles.clear()
            self.sparkle_spawn_timer = 0.0
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

            if getattr(self, 'sparkle_layer', None) is not None and self.sparkle_layer in self.ui_layer.children:
                self.ui_layer.remove_widget(self.sparkle_layer)
                
            self.sparkle_layer = Widget(size_hint=(0.86, 0.48), pos_hint={'x': 0.07, 'y': 0.32})
            self.ui_layer.add_widget(self.sparkle_layer)
            self.ui_layer.add_widget(create_visual_button("Ana Menü", (0.13, 0.77, 0.36, 1), 0.16, lambda x: self.switch_view("main")))

    def switch_view(self, view_name):
        self.about_sparkles.clear()
        self.sparkle_spawn_timer = 0.0
        if getattr(self, 'sparkle_layer', None) is not None:
            self.sparkle_layer.canvas.clear()
        self.current_view = view_name
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
        
        local[key] = max(min_v, min(local.get(key, min_v) + amount, max_v))
        self.save_settings()
        
        label_obj.text = f"{prefix}{local[key]}{suffix}"
        if btn_m and btn_p: 
            self._check_button_edge_colors_v2(key, min_v, max_v, btn_m, btn_p, local)
        
        if key == "max_creatures":
            type1_spiders = [s for s in self.spider_list if s.assigned_folder == current_folder]
            while len(type1_spiders) > local[key]:
                rem = type1_spiders.pop()
                if rem in self.spider_list: self.spider_list.remove(rem)
                try:
                    rem.canvas_widget.canvas.clear()
                    self.creature_layer.remove_widget(rem.canvas_widget)
                except: pass
        elif key == "max_creatures2":
            if self.settings.get("type2_enabled", 1) == 0: 
                return
            type2_spiders = [s for s in self.spider_list if s.assigned_folder == current_folder2]
            while len(type2_spiders) > local[key]:
                rem = type2_spiders.pop()
                if rem in self.spider_list: self.spider_list.remove(rem)
                try:
                    rem.canvas_widget.canvas.clear()
                    self.creature_layer.remove_widget(rem.canvas_widget)
                except: pass
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
            except Exception: pass
            
        if btn_p.canvas.before and btn_p.canvas.before.children:
            try:
                if current_value >= max_v: 
                    btn_p.canvas.before.children[0].rgba = (0.13, 0.77, 0.36, 1)  
                else: 
                    btn_p.canvas.before.children[0].rgba = (0.2, 0.25, 0.33, 1)
            except Exception: pass

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

    def change_habitat_class_step(self, direction, slot_type=1):
        idx = self.settings.get("current_hab_idx1", 0)
        new_idx = (idx + direction + len(self.habitats_list)) % len(self.habitats_list)
        
        self.settings["current_hab_idx1"] = new_idx
        self.settings["current_hab_idx2"] = new_idx
        self.settings["animation_folder_idx"] = 0 
        self.settings["animation_folder_idx2"] = 0 
        self.clear_all_creatures_on_habitat_change()
            
        self.sync_active_folder_settings()
        self.save_settings()
        self.update_background_image()
        self.rebuild_ui()

    def change_creature_type_step(self, direction, type_slot=1):
        filtered1 = self.get_filtered_folders_by_slot(1)
        filtered2 = self.get_filtered_folders_by_slot(2)
        
        if type_slot == 1:
            idx = self.settings.get("animation_folder_idx", 0)
            self.settings["animation_folder_idx"] = (idx + direction + len(filtered1)) % len(filtered1)
            self.clear_all_creatures_on_habitat_change()
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
                if spider.id % 2 == 1:
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
        filtered1 = self.get_filtered_folders_by_slot(1)
        current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
        theme_dir = os.path.join(base_dir, "anims") if current_folder == "default" else os.path.join(base_dir, "anims", current_folder)
        
        valid_bg_count = 1
        for i in range(1, 10): 
            if os.path.exists(os.path.join(theme_dir, f"bg{i}_v.png")) or os.path.exists(os.path.join(theme_dir, f"bg{i}_h.png")):
                valid_bg_count += 1
                
        current_idx = self.settings.get("bg_image_idx", 0)
        new_idx = (current_idx + direction + valid_bg_count) % valid_bg_count
        
        self.settings["bg_image_idx"] = new_idx
        if current_folder in self.settings["folder_settings"]:
            self.settings["folder_settings"][current_folder]["bg_image_idx"] = new_idx
            
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

    def spawn_gold_orb(self):
        w_size = 70
        x = random.randint(80, max(81, self.SCREEN_WIDTH - w_size - 80))
        y = random.randint(150, max(151, self.SCREEN_HEIGHT - w_size - 150))
        self.gold_orb = {"x": x, "y": y, "size": w_size, "pulse": 0.0}
        self.redraw_gold_orb()

    def redraw_gold_orb(self):
        self.gold_orb_layer.canvas.clear()
        if not self.gold_orb: return
        with self.gold_orb_layer.canvas:
            Color(1, 0.84, 0, 1)
            p_size = self.gold_orb["size"] + math.sin(self.gold_orb["pulse"]) * 8
            offset = (p_size - self.gold_orb["size"]) / 2
            Ellipse(pos=(self.gold_orb["x"] - offset, self.gold_orb["y"] - offset), size=(p_size, p_size))

    def redraw_walls(self):
        self.wall_layer.canvas.clear()
        with self.wall_layer.canvas:
            for wall in self.walls:
                Color(*wall["color"])
                Rectangle(pos=(wall["rect"][0], wall["rect"][1]), size=(wall["rect"][2], wall["rect"][3]))
    def update(self, dt):
        if self.spider_active:
            filtered1 = self.get_filtered_folders_by_slot(1)
            filtered2 = self.get_filtered_folders_by_slot(2)
            current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
            current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]
            
            local1 = self.settings["folder_settings"].get(current_folder, self.settings)
            local2 = self.settings["folder_settings"].get(current_folder2, self.settings)
            
            is_type2_on = self.settings.get("type2_enabled", 1) == 1
            limit_type1 = local1.get("max_creatures", 6)
            limit_type2 = local2.get("max_creatures2", 6) if is_type2_on else 0
            
            current_type1_count = sum(1 for s in self.spider_list if s.assigned_folder == current_folder)
            current_type2_count = sum(1 for s in self.spider_list if s.assigned_folder == current_folder2)
            
            if not is_type2_on and current_type2_count > 0:
                for spider in list(self.spider_list):
                    if spider.assigned_folder == current_folder2:
                        try:
                            spider.canvas_widget.canvas.clear()
                            self.creature_layer.remove_widget(spider.canvas_widget)
                            self.spider_list.remove(spider)
                        except: pass
                current_type2_count = 0
            chosen_f = None
            if current_type1_count < limit_type1 and current_type2_count < limit_type2:
                chosen_f = current_folder if current_type1_count <= current_type2_count else current_folder2
            elif current_type1_count < limit_type1:
                chosen_f = current_folder
            elif current_type2_count < limit_type2:
                chosen_f = current_folder2
                
            if chosen_f:
                new_spider = KivySpiderEntity(self.settings, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.animation_folders, zorunlu_klasor=chosen_f)
                self.spider_list.append(new_spider)
                self.creature_layer.add_widget(new_spider.canvas_widget)

            self.wall_timer += dt
            if self.wall_timer >= self.next_wall_time:
                self.wall_timer = 0
                self.next_wall_time = random.uniform(8.0, 15.0)
                self.spawn_random_wall()

            # --- SIFIRLAMA VE ÇAKIŞMA ÖNLEYİCİ TAM SENKRONİZE KÜRE MOTORU ---
            current_creature_count = len(self.spider_list)
            if current_creature_count >= 6:
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

            # --- BÜYÜK MERKEZİ DUVAR ZAMANLAYICI MOTORU ---
            if not self.big_wall_active:
                self.big_wall_timer += dt
                if self.big_wall_timer >= self.big_wall_interval:
                    if len(self.walls) < 2:
                        bw = random.randint(300, 360)
                        bx = (self.SCREEN_WIDTH - bw) / 2
                        by = (self.SCREEN_HEIGHT - bw) / 2
                        self.walls.append({"rect": [bx, by, bw, bw], "color": (0.8, 0.2, 0.2, 1.0), "life": 0.0, "is_big": True})
                        self.redraw_walls()
                        
                        self.big_wall_active = True
                        self.big_wall_pending_destroy = False
                        self.big_wall_timer = 0.0  
                        
                        for s in self.spider_list:
                            s.start_orbiting(bx, by, bw, bw)
            else:
                if self.big_wall_pending_destroy:
                    self.big_wall_destroy_timer -= dt
                    if self.big_wall_destroy_timer <= 0:
                        self.walls = [w for w in self.walls if not w.get("is_big", False)]
                        self.redraw_walls()
                        
                        self.big_wall_active = False
                        self.big_wall_pending_destroy = False
                        self.big_wall_timer = 0.0  
            for spider in list(self.spider_list):
                if spider in self.spider_list:
                    spider.update_entity(dt, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.settings, self.walls, self.spider_list)

        self.particle_layer.canvas.clear()
        self.particle_emitter.update_particles(dt)

        if self.current_view == "about" and self.ui_visible and hasattr(self, 'sparkle_layer') and self.sparkle_layer:
            self.sparkle_spawn_timer += dt
            if self.sparkle_spawn_timer >= 0.25:  # Yıldızların belirme sıklığı (source 1 altyapısı)
                self.sparkle_spawn_timer = 0.0
                if len(self.about_sparkles) < 15:  # Ekrandaki anlık maksimum aktif yıldız sayısı
                    sp_x = random.uniform(self.SCREEN_WIDTH * 0.1, self.SCREEN_WIDTH * 0.9)
                    sp_y = random.uniform(self.SCREEN_HEIGHT * 0.35, self.SCREEN_HEIGHT * 0.75)
                    base_color = random.choice([[1.0, 0.85, 0.2], [1.0, 1.0, 1.0]]) # Sarı veya Beyaz
                    sparkle_form = random.choice(["plus", "star"]) # + veya * formu
                    
                    self.about_sparkles.append({
                        "x": sp_x, "y": sp_y, "size": random.uniform(12, 22),
                        "base_color": base_color, "form": sparkle_form, 
                        "state": "fade_in", "alpha": 0.0, "speed": random.uniform(1.5, 3.0)
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

class KivySpiderEntity:
    _id_counter = 0
    def __init__(self, settings, sw, sh, animation_folders, zorunlu_klasor=None):
        KivySpiderEntity._id_counter += 1
        self.id = KivySpiderEntity._id_counter
        
        if zorunlu_klasor:
            self.assigned_folder = zorunlu_klasor
        else:
            app = App.get_running_app()
            filtered1 = app.get_filtered_folders_by_slot(1) if app else ["default"]
            filtered2 = app.get_filtered_folders_by_slot(2) if app else ["default"]
            if self.id % 2 == 1:
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
        if self.is_grabbed: return
        
        app = App.get_running_app()
        if app and hasattr(app, 'spider_list'):
            already_orbiting = any(s.is_orbiting for s in app.spider_list if s.id != self.id)
            if already_orbiting:
                return
        
        self.is_orbiting = True
        self.orbit_wx, self.orbit_wy, self.orbit_ww, self.orbit_wh = wx, wy, ww, wh
        self.orbit_phase = random.randint(0, 3)
        self.orbit_start_phase = self.orbit_phase
        self.orbit_counter = 0  
        
        x_m, x_mx = self.orbit_wx - self.size + 15 + self.visual_offset, self.orbit_wx + self.orbit_ww - 15 - self.visual_offset
        y_m, y_mx = self.orbit_wy - self.size + 15 + self.visual_offset, self.orbit_wy + self.orbit_wh - 15 - self.visual_offset
        
        if self.orbit_phase == 0: self.x, self.y = x_mx, y_m  
        elif self.orbit_phase == 1: self.x, self.y = x_m, y_m   
        elif self.orbit_phase == 2: self.x, self.y = x_m, y_mx  
        elif self.orbit_phase == 3: self.x, self.y = x_mx, y_mx 

    def reload_textures(self, settings, animation_folders):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.anim_path_root = os.path.join(base_dir, "anims", self.assigned_folder) if self.assigned_folder != "default" else os.path.join(base_dir, "anims")
        self.total_frames = 0
        self.textures = {}
        local = settings.get("folder_settings", {}).get(self.assigned_folder, settings)
        
        if os.path.exists(self.anim_path_root):
            try:
                valid_idx = sorted([int(f.split('.')[0]) for f in os.listdir(self.anim_path_root) if f.lower().endswith('.png') and f.split('.')[0].isdigit() and f.lower() not in [f"bg{local.get('bg_image_idx', 0)}_v.png", f"bg{local.get('bg_image_idx', 0)}_h.png", 'bg.png']])
                self.total_frames = len(valid_idx)
                for idx, num in enumerate(valid_idx):
                    p = os.path.join(self.anim_path_root, f"{num}.png")
                    if os.path.exists(p): 
                        core_img = CoreImage(p)
                        tex = core_img.texture
                        tex.keep_data = True
                        self.textures[idx] = tex
            except: 
                self.total_frames = 0
                
        if self.total_frames == 0:
            for i in range(4):
                p = os.path.join(self.anim_path_root, f"{i}.png")
                if os.path.exists(p): 
                    core_img = CoreImage(p)
                    tex = core_img.texture
                    tex.keep_data = True
                    self.textures[self.total_frames] = tex
                    self.total_frames += 1
        self.current_frame = 0
        self.visual_offset = local.get("visual_offset", 15)

    def setup_canvas(self):
        self.canvas_widget.canvas.clear()
        self.rect_w = self.size
        self.rect_h = self.size
        
        has_texture = False
        if self.textures and self.textures.get(0):
            tex = self.textures.get(0)
            oran = tex.width / tex.height
            if oran > 1: self.rect_h = self.size / oran
            elif oran < 1: self.rect_w = self.size * oran
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
                self.super_glow = Ellipse(
                    pos=(self.x + (self.size - glow_w)/2, self.y + (self.size - glow_h)/2), 
                    size=(glow_w, glow_h)
                )
            
            if has_texture:
                Color(1.0, 1.0, 1.0, 1.0)
                self.rect_mesh = Rectangle(
                    texture=self.textures.get(0), 
                    pos=(self.x + (self.size - self.rect_w)/2, self.y + (self.size - self.rect_h)/2), 
                    size=(self.rect_w, self.rect_h)
                )
            else:
                Color(0.2, 0.7, 0.3, 1.0)
                self.rect_mesh = Ellipse(
                    pos=(self.x + (self.size - self.rect_w)/2, self.y + (self.size - self.rect_h)/2), 
                    size=(self.rect_w, self.rect_h)
                )
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
        if widget.collide_point(*touch.pos):
            self.touch_history.clear()
            self.is_grabbed = True
            self.is_orbiting = False
            self.vx = self.vy = 0
            self.last_touch_x = touch.x
            self.last_touch_y = touch.y
            return True
        return False
        
    def on_touch_move(self, widget, touch):
        if self.is_grabbed:
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
                    self.vx *= 1.5
                    self.vy *= 1.5
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
        if self.is_grabbed: return
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
            
            t_ang = math.pi if self.orbit_phase == 0 else (math.pi*0.5 if self.orbit_phase == 1 else (0.0 if self.orbit_phase == 2 else math.pi*1.5))
            c_spd = base_spd

            if self.orbit_phase == 0:
                self.y = y_m
                self.x -= c_spd * dt
                if self.x <= x_m: 
                    self.x = x_m
                    self.orbit_phase = 1
                    self.orbit_counter += 1
            elif self.orbit_phase == 1:
                self.x = x_m
                self.y += c_spd * dt
                if self.y >= y_mx: 
                    self.y = y_mx
                    self.orbit_phase = 2
                    self.orbit_counter += 1
            elif self.orbit_phase == 2:
                self.y = y_mx
                self.x += c_spd * dt
                if self.x >= x_mx: 
                    self.x = x_mx
                    self.orbit_phase = 3
                    self.orbit_counter += 1
            elif self.orbit_phase == 3:
                self.x = x_mx
                self.y -= c_spd * dt
                if self.y <= y_m: 
                    self.y = y_m
                    self.orbit_phase = 0
                    self.orbit_counter += 1

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
                        if walls[i].get("is_big", False):
                            if app:
                                app.big_wall_active = False
                                app.big_wall_pending_destroy = False
                                app.big_wall_timer = 0.0
                            for s in spider_list:
                                if s.is_orbiting: 
                                    s.is_orbiting = False
                                    s.angle = random.uniform(0, 2 * math.pi)
                        app.particle_emitter.spawn_shattered_wall(r, walls[i]["color"], self.size)
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

        if app and app.gold_orb:
            self_center_x = n_x + self.size / 2
            self_center_y = n_y + self.size / 2
            orb_center_x = app.gold_orb["x"] + app.gold_orb["size"] / 2
            orb_center_y = app.gold_orb["y"] + app.gold_orb["size"] / 2
            
            orb_dist = math.sqrt((orb_center_x - self_center_x)**2 + (orb_center_y - self_center_y)**2)
            grab_radius = (self.size * 0.35) + (app.gold_orb["size"] / 2)
            
            if orb_dist < grab_radius:
                self.activate_super_power(15.0)  
                app.gold_orb = None  
                app.gold_orb_timer = 0.0
                app.gold_orb_spawn_time = random.uniform(20.0, 40.0) 
                app.gold_orb_layer.canvas.clear()  

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
                
                min_distance = (self.size * 0.35 + other.size * 0.35) - (self.visual_offset * 0.5 + other.visual_offset * 0.5)
                
                if not hasattr(self, '_active_passings'): self._active_passings = set()
                if not hasattr(other, '_active_passings'): other._active_passings = set()

                if distance < min_distance and distance > 0:
                    if self.is_super and not other.is_super:
                        try: 
                            creature_rect = [other.x, other.y, other.size, other.size]
                            creature_color = [random.random(), random.random(), random.random(), 1.0]
                            if app and hasattr(app, 'particle_emitter'): app.particle_emitter.spawn_shattered_wall(creature_rect, creature_color, self.size)
                            other.canvas_widget.canvas.clear()
                            app.creature_layer.remove_widget(other.canvas_widget)
                            if other in spider_list: spider_list.remove(other)
                        except: pass
                        continue
                    elif not self.is_super and other.is_super:
                        try: 
                            my_rect = [self.x, self.y, self.size, self.size]
                            my_color = [random.random(), random.random(), random.random(), 1.0]
                            if app and hasattr(app, 'particle_emitter'): app.particle_emitter.spawn_shattered_wall(my_rect, my_color, other.size)
                            self.canvas_widget.canvas.clear()
                            app.creature_layer.remove_widget(self.canvas_widget)
                            if self in spider_list: spider_list.remove(self)
                        except: pass
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
                            except: pass
                        continue 

                    nx_vec = dx / distance
                    ny_vec = dy / distance
                    tx_vec = -ny_vec
                    ty_vec = nx_vec
                    
                    v1n = self.vx * nx_vec + self.vy * ny_vec
                    v1t = self.vx * tx_vec + self.vy * ty_vec
                    v2n = other.vx * nx_vec + other.vy * ny_vec
                    v2t = other.vx * tx_vec + other.vy * ty_vec
                    
                    if self.is_flung: other.is_flung = True
                    elif other.is_flung: self.is_flung = True
                    
                    self.vx = v2n * nx_vec + v1t * tx_vec
                    self.vy = v2n * ny_vec + v1t * ty_vec
                    other.vx = v1n * nx_vec + v2t * tx_vec
                    other.vy = v1n * ny_vec + v2t * ty_vec
                    
                    self.angle = math.atan2(self.vy, self.vx) % (2 * math.pi)
                    other.angle = math.atan2(other.vy, other.vx) % (2 * math.pi)
                    
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
                    if hasattr(self, '_active_passings') and other.id in self._active_passings: self._active_passings.remove(other.id)
                    if hasattr(other, '_active_passings') and self.id in other._active_passings: other._active_passings.remove(self.id)

        self.x, self.y = n_x, n_y
        sf_w = sw if sw > 100 else 1080
        sf_h = sh if sh > 100 else 1920
        out_of_bounds = False

        if (self.x + self.size < -50 or self.x > sf_w + 50 or self.y + self.size < -50 or self.y > sf_h + 50): 
            out_of_bounds = True

        if out_of_bounds:
            edge = random.randint(0, 3)
            if edge == 0: self.x = -self.size + 10; self.y = random.randint(0, max(1, sf_h - self.size))
            elif edge == 1: self.x = sf_w - 10; self.y = random.randint(0, max(1, sf_h - self.size))
            elif edge == 2: self.x = random.randint(0, max(1, sf_w - self.size)); self.y = -self.size + 10
            elif edge == 3: self.x = random.randint(0, max(1, sf_w - self.size)); self.y = sf_h - 10
            self.angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(self.angle) * base_spd
            self.vy = math.sin(self.angle) * base_spd
            
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
            glow_w = self.rect_w * glow_factor
            glow_h = self.rect_h * glow_factor
            self.super_glow.pos = (self.x + (self.size - glow_w)/2, self.y + (self.size - glow_h)/2)
            
        self.rot_transform.origin = self.scale_transform.origin = self.canvas_widget.center
        move_deg = math.degrees(self.angle) % 360
        facing_mode = local.get("image_facing", 0) % 4

        fx, fy = 1, 1

        if self.is_orbiting:
            base_offset = facing_mode * 90
            if facing_mode == 1:
                if self.orbit_phase == 0: t_ang = 90; fx, fy = 1, 1
                elif self.orbit_phase == 1: t_ang = 0; fx, fy = 1, 1
                elif self.orbit_phase == 2: t_ang = 270; fx, fy = 1, 1
                elif self.orbit_phase == 3: t_ang = 180; fx, fy = 1, 1
            elif facing_mode == 2:
                if self.orbit_phase == 0: t_ang = 180; fx, fy = -1, 1
                elif self.orbit_phase == 1: t_ang = 270; fx, fy = 1, -1
                elif self.orbit_phase == 2: t_ang = 0; fx, fy = -1, 1
                elif self.orbit_phase == 3: t_ang = 90; fx, fy = 1, -1
            elif facing_mode == 3:
                if self.orbit_phase == 0: t_ang = 270; fx, fy = 1, 1
                elif self.orbit_phase == 1: t_ang = 180; fx, fy = 1, 1
                elif self.orbit_phase == 2: t_ang = 90; fx, fy = 1, 1
                elif self.orbit_phase == 3: t_ang = 0; fx, fy = 1, 1
            else:
                if self.orbit_phase == 0: deg = 180
                elif self.orbit_phase == 1: deg = 90
                elif self.orbit_phase == 2: deg = 0
                elif self.orbit_phase == 3: deg = 270
                t_ang = deg - base_offset
        else:
            if facing_mode == 0:    
                t_ang = move_deg
                if 90 < (t_ang % 360) <= 270:
                    t_ang = t_ang - 180
                    fx = -1  
            elif facing_mode == 1:  
                t_ang = move_deg - 90
                if 90 < (move_deg % 360) <= 270:
                    fx = -1 
            elif facing_mode == 2:  
                t_ang = move_deg - 180
                if not (90 < (move_deg % 360) <= 270):
                    t_ang = t_ang - 180
                    fx = -1  
            elif facing_mode == 3:  
                t_ang = move_deg - 270
                if 90 < (move_deg % 360) <= 270:
                    fx = -1

        self.rot_transform.angle = t_ang + (self.roll_angle * fx)
        self.scale_transform.x, self.scale_transform.y = fx, fy
        
        if self.textures and self.anim_time > (local.get("anim_speed", 80) / 1000.0) and self.total_frames > 0:
            if self.is_grabbed or math.sqrt(self.vx**2 + self.vy**2) > 5:
                self.current_frame = (self.current_frame + 1) % self.total_frames
                if hasattr(self, 'rect_mesh') and hasattr(self.rect_mesh, 'texture'): 
                    self.rect_mesh.texture = self.textures.get(self.current_frame)
                self.anim_time = 0

if __name__ == '__main__':
    CreatureOverlayApp().run()
