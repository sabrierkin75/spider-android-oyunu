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
from kivy.uix.scrollview import ScrollView
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Scale, Rotate, Mesh, RoundedRectangle, Ellipse
from kivy.animation import Animation
Window.allow_screensize_orientation = True

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
    """Yok olan duvarların, süper mod efektlerinin og yıldız parçacıklarının yöneticisi."""
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
            
            # --- HER PARÇACIK İÇİN RASTGELE CANLI NEON RENKLERİ ---
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
                
                # --- SÜPER RENGÂRENK NEON REYONLARI (TİP 2) ---
                if p["type"] == 2:
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["vx"] *= 0.92  
                    p["vy"] *= 0.92
                    p["size"] += dt * 9.0  
                    p["rot"] += p["rot_speed"] * dt
                    
                    # Kaydedilen rastgele neon rengi al, yoksa varsayılan sarı yap
                    nc = p.get("neon_color", [1.0, 0.9, 0.0])
                    
                    if p.get("sub_type", "orb") == "orb":
                        # Katman 1: Dıştaki geniş parlayan neon çeper (Rastgele Renkli)
                        Color(nc[0], nc[1], nc[2], alpha * 0.35)
                        Ellipse(pos=(p["x"] - p["size"]/2, p["y"] - p["size"]/2), size=(p["size"], p["size"]))
                        # Katman 2: Merkezdeki parlak çekirdek (Sabit Beyaz)
                        Color(1.0, 1.0, 1.0, alpha * 0.85)
                        Ellipse(pos=(p["x"] - p["size"]/4, p["y"] - p["size"]/4), size=(p["size"]/2, p["size"]/2))
                    else:
                        PushMatrix()
                        Rotate(angle=p["rot"], origin=(p["x"], p["y"]), axis=(0, 0, 1))
                        # Katman 1: Dıştaki parlayan neon hatlar (Rastgele Renkli)
                        Color(nc[0], nc[1], nc[2], alpha * 0.4)
                        Ellipse(pos=(p["x"] - p["size"]/2, p["y"] - p["size"]/6), size=(p["size"], p["size"]/3))
                        Ellipse(pos=(p["x"] - p["size"]/6, p["y"] - p["size"]/2), size=(p["size"]/3, p["size"]))
                        # Katman 2: İçteki keskin parlayan hatlar (Sabit Beyaz)
                        Color(1.0, 1.0, 1.0, alpha * 0.85)
                        Ellipse(pos=(p["x"] - p["size"]/2.5, p["y"] - p["size"]/12), size=(p["size"]/1.25, p["size"]/6))
                        Ellipse(pos=(p["x"] - p["off_size" if "off_size" in p else "size"]/12, p["y"] - p["size"]/2.5), size=(p["size"]/6, p["size"]/1.25))
                        PopMatrix()
                        
                # --- DUVAR PARÇALANMA DİKDÖRTGENLERİ (TİP 0) ---
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
                    
                # --- DUVAR PARÇALANMA ÜÇGENLERİ (TİP 1) ---
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
            "max_creatures2": 1, "type2_enabled": 1, "image_facing": 0, "visual_offset": 15, 
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
        self.big_wall_interval = 40.0  
     
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
        
        # 1. TÜR İÇİN BAĞIMSIZ HAFIZA ALANI KURULUMU
        if current_folder not in self.settings["folder_settings"]:
            self.settings["folder_settings"][current_folder] = {
                "move_speed": 4, "anim_speed": 80, "max_creatures": 6, "max_creatures2": 1,
                "type2_enabled": 0 if len(filtered1) <= 1 else 1, "image_facing": 0,
                "visual_offset": 15, "creature_size": 120, "bg_image_idx": 0, "super_speed_mult": 3.0
            }
            
        # 2. TÜR İÇİN TAMAMEN BAĞIMSIZ VE YALITILMIŞ HAFIZA ALANI KURULUMU
        if current_folder2 not in self.settings["folder_settings"]:
            self.settings["folder_settings"][current_folder2] = {
                "move_speed": 4, "anim_speed": 80, "max_creatures": 6, "max_creatures2": 1,
                "type2_enabled": 0 if len(filtered1) <= 1 else 1, "image_facing": 0,
                "visual_offset": 15, "creature_size": 120, "bg_image_idx": 0, "super_speed_mult": 3.0
            }
            
        # Eğer sınıfta tek tür varsa her iki yerel hafızada da type2'yi kesin olarak kapat
        if len(filtered1) <= 1:
            self.settings["type2_enabled"] = 0
            self.settings["folder_settings"][current_folder]["type2_enabled"] = 0
            self.settings["folder_settings"][current_folder2]["type2_enabled"] = 0
        else:
            # --- MUTLAK KORUMA BARİYERİ ---
            # Geçiş anlarında hafızanın bozulmaması için yerel type2_enabled ayarını 
            # daima global ayarlardaki "type2_enabled" değerine eşitliyoruz.
            self.settings["folder_settings"][current_folder]["type2_enabled"] = self.settings.get("type2_enabled", 1)
            self.settings["folder_settings"][current_folder2]["type2_enabled"] = self.settings.get("type2_enabled", 1)
        
        # Sadece o an aktif olan 1. slotun ayarlarını globale yansıt
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
        
        if not filtered: 
            return ["default"]
            
        # --- KESİN TAMİR: 9 türün de sırası ve uzunluğu daima sabit kalır, asla dalgalanmaz ---
        return filtered

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
                        subfolders = sorted([d for d in os.listdir(hab_path) if os.path.isdir(os.path.join(hab_path, d)) and not d.startswith('.')])
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
            
            if len(filtered1) <= 1:
                self.settings["type2_enabled"] = 0
                is_type2_on = False
                if self.active_settings_tab == "type2":
                    self.active_settings_tab = "visual"
            else:
                is_type2_on = self.settings.get("type2_enabled", 1) == 1
            
            if self.active_settings_tab == "type2":
                target_folder = current_folder2
            else:
                target_folder = current_folder
                
            local1 = self.settings["folder_settings"].setdefault(target_folder, {
                "move_speed": 4, "anim_speed": 80, "max_creatures": 6, "max_creatures2": 6, "type2_enabled": 1,
                "image_facing": 0, "visual_offset": 15, "creature_size": 120, "bg_image_idx": 0, "super_speed_mult": 3.0
            })
            
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
                self.hab1_label = Label(text=f"Seçili Sınıf: [color=45b870][b]{current_hab1}[/b][/color]", markup=True)
                self.h1_m, self.h1_p = Button(text="<"), Button(text=">")
                _setup_setting_row(self.hab1_label, self.h1_m, self.h1_p, 0.76)
                self.h1_m.bind(on_press=lambda x: self.change_habitat_class_step(-1, 1))
                self.h1_p.bind(on_press=lambda x: self.change_habitat_class_step(1, 1))
                self.ui_layer.add_widget(self.hab1_label)
                self.ui_layer.add_widget(self.h1_m)
                self.ui_layer.add_widget(self.h1_p)

                self.type_label = Label(text=f"1. Alt Tür: [b]{current_folder.upper()}[/b]", markup=True)
                self.t_minus, self.t_plus = Button(text="<"), Button(text=">")
                _setup_setting_row(self.type_label, self.t_minus, self.t_plus, 0.70)
                self.t_minus.bind(on_press=lambda x: self.change_creature_type_step(-1, 1))
                self.t_plus.bind(on_press=lambda x: self.change_creature_type_step(1, 1))
                self.ui_layer.add_widget(self.type_label)
                self.ui_layer.add_widget(self.t_minus)
                self.ui_layer.add_widget(self.t_plus)

                if len(self.get_filtered_folders_by_slot(1)) <= 1:
                    t2_status_text = "[color=a0a0a0]YOK\n(TEK TÜR)[/color]"
                    self.t2_toggle_label = Label(text=f"2. Tür Durumu: {t2_status_text}", markup=True)
                    self.t2_left_btn, self.t2_right_btn = Button(text="X"), Button(text="X")
                    _setup_setting_row(self.t2_toggle_label, self.t2_left_btn, self.t2_right_btn, 0.62, (0.15, 0.15, 0.15, 0.6), (0.15, 0.15, 0.15, 0.6))
                    self.t2_left_btn.disabled = True
                    self.t2_right_btn.disabled = True
                else:
                    t2_status_text = "[color=13c444][b]AKTİF[/b][/color]" if is_type2_on else "[color=ed4242][b]PASİF[/b][/color]"
                    self.t2_toggle_label = Label(text=f"2. Tür Durumu: {t2_status_text}", markup=True)
                    self.t2_left_btn, self.t2_right_btn = Button(text="<"), Button(text=">")
                    _setup_setting_row(self.t2_toggle_label, self.t2_left_btn, self.t2_right_btn, 0.62)
                    
                    def _toggle_type2_switch():
                        current_status = 1 if self.settings.get("type2_enabled", 1) == 1 else 0
                        new_status = 0 if current_status == 1 else 1
                        
                        # Hem global ayarı hem de iki slotun yerel hafıza ayarını aynı anda güncelliyoruz
                        self.settings["type2_enabled"] = new_status
                        
                        if current_folder in self.settings["folder_settings"]:
                            self.settings["folder_settings"][current_folder]["type2_enabled"] = new_status
                        if current_folder2 in self.settings["folder_settings"]:
                            self.settings["folder_settings"][current_folder2]["type2_enabled"] = new_status
                            
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

                if is_type2_on and len(self.get_filtered_folders_by_slot(1)) > 1:
                    self.type2_label = Label(text=f"2. Alt Tür: [b]{current_folder2.upper()}[/b]", markup=True)
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
                _setup_setting_row(self.face1_label, self.f1_minus, self.f1_plus, 0.33)
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
                _setup_setting_row(self.face2_label, self.f2_minus, self.f2_plus, 0.33)
                
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
            
            # --- DÜĞMEYİ KAPATMAYACAK ŞEKİLDE YENİ KONUMLANDIRMA ÖLÇÜLERİ ---

            panel_y = 0.24
            panel_h = 0.62
            panel_w = 0.86
            panel_x = 0.07

            # --- 1. ADIM: İÇERİK İÇİN SABİT ARKA PLAN PANELİ ---
            about_panel = Widget(size_hint=(panel_w, panel_h), pos_hint={'x': panel_x, 'y': panel_y})
            with about_panel.canvas.before:
                Color(0.05, 0.05, 0.05, 0.85) 
                about_panel.bg_rect = RoundedRectangle(pos=about_panel.pos, size=about_panel.size, radius=[15])
            def _update_about_bg(inst, val): 
                inst.bg_rect.pos = inst.pos
                inst.bg_rect.size = inst.size
            about_panel.bind(pos=_update_about_bg, size=_update_about_bg)
            self.ui_layer.add_widget(about_panel)

            # --- 2. ADIM: GÜVENLİ KAYDIRMA ALANI (SCROLLVIEW) ---
            # Kaydırma alanını yeni panel sınırlarına tam olarak eşitliyoruz
            scroll_container = ScrollView(size_hint=(panel_w, panel_h), pos_hint={'x': panel_x, 'y': panel_y}, do_scroll_x=False, do_scroll_y=True)

            # --- 3. ADIM: TAM YATAY ORTALANMIŞ METİN KATMANI ---
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
                size_hint_x=None,
                size_hint_y=None
            )
            
            # Kesin ortalama motoru
            def _sync_sizes(instance, value):
                self.about_label.width = value
                self.about_label.text_size = (value, None)
            scroll_container.bind(width=_sync_sizes)
            
            # Metin boyutu değiştikçe yüksekliği korumalı hesaplıyoruz
            def _update_label_height(instance, txt_size):
                if isinstance(txt_size, (list, tuple)) and len(txt_size) >= 2:
                    metin_yuksekligi = txt_size[1]
                    instance.height = max(scroll_container.height, metin_yuksekligi + 80)
            self.about_label.bind(texture_size=_update_label_height)
            
            scroll_container.add_widget(self.about_label)
            self.ui_layer.add_widget(scroll_container)

            # --- 4. ADIM: PARTİKÜL KATMANI VE BUTONLAR ---
            if getattr(self, 'sparkle_layer', None) is not None and self.sparkle_layer in self.ui_layer.children:
                self.ui_layer.remove_widget(self.sparkle_layer)
                
            self.sparkle_layer = Widget(size_hint=(panel_w, panel_h), pos_hint={'x': panel_x, 'y': panel_y})
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
            idx1 = self.settings.get("animation_folder_idx", 0)
            self.settings["animation_folder_idx"] = (idx1 + direction + len(filtered1)) % len(filtered1)
            self.clear_all_creatures_on_habitat_change()
            
            # --- 9 TÜR İÇİN MUTLAK ÇAKIŞMA ÖNLEYİCİ ---
            # Eğer üstteki tür butonla değiştirildiğinde alttakiyle aynı indekse denk gelirse:
            if len(filtered1) > 1 and self.settings["animation_folder_idx"] == self.settings["animation_folder_idx2"]:
                # 2. türün indeksini güvenli mod (%) ile 1 ileri zıplat (Asla ayarı kapatmaz)
                self.settings["animation_folder_idx2"] = (self.settings["animation_folder_idx2"] + 1) % len(filtered2)
        else:
            idx2 = self.settings.get("animation_folder_idx2", 0)
            new_idx2 = (idx2 + direction + len(filtered2)) % len(filtered2)
            
            # Kullanıcı elle 2. türü değiştirirken 1. türün üzerine gelirse bir adım daha zıpla
            if len(filtered2) > 1 and new_idx2 == self.settings["animation_folder_idx"]:
                new_idx2 = (new_idx2 + direction + len(filtered2)) % len(filtered2)
                
            self.settings["animation_folder_idx2"] = new_idx2
            
        self.sync_active_folder_settings()
        self.save_settings()
        self.update_background_image()
        self.rebuild_ui()
        
        # Canlı yaratıkların dokularını yenileyen alt kısım
        current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
        current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]
        is_type2_on = self.settings.get("type2_enabled", 1) == 1
        
        for i, spider in enumerate(list(self.spider_list)):
            try:
                if not is_type2_on:
                    spider.assigned_folder = current_folder
                else:
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
                # --- KESİN ÇÖZÜM: EL YAPIMI DOKUNMALARDA OYNATICIYI RESETLEME ---
                if wall.get("is_big", False):
                    # Yörüngedeki yaratıkları serbest bırak
                    for s in self.spider_list:
                        if s.is_orbiting: 
                            s.is_orbiting = False
                            s.angle = random.uniform(0, 2 * math.pi)
                    
                    # Uygulama motoruna büyük duvarın bittiğini bildir ve zamanlayıcıyı sıfırla
                    self.big_wall_active = False
                    self.big_wall_pending_destroy = False
                    self.big_wall_timer = 0.0

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
# --- YENİ / EKLENECEK KOD BLOĞU ---
        if self.spider_active:
            filtered1 = self.get_filtered_folders_by_slot(1)
            filtered2 = self.get_filtered_folders_by_slot(2)
            
            # Koruma: Listenin boş kalmamasını garanti altına alıyoruz
            if not filtered1: filtered1 = ["default"]
            if not filtered2: filtered2 = ["default"]
            
            current_folder = filtered1[self.settings["animation_folder_idx"] % len(filtered1)]
            current_folder2 = filtered2[self.settings["animation_folder_idx2"] % len(filtered2)]
            
            local1 = self.settings["folder_settings"].get(current_folder, self.settings)
            local2 = self.settings["folder_settings"].get(current_folder2, self.settings)
            
            # --- KESİN TAMİR: Geçiş anındaki anlık liste dalgalanmalarının type2'yi kapatmasını engelliyoruz ---
            if len(filtered1) <= 1:
                is_type2_on = False
            else:
                is_type2_on = self.settings.get("type2_enabled", 1) == 1
                
            limit_type1 = local1.get("max_creatures", 6)
            limit_type2 = local2.get("max_creatures2", 6) if is_type2_on else 0
            
            if not is_type2_on:
                current_type1_count = len(self.spider_list)
                current_type2_count = 0
            else:
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
            if not is_type2_on:
                if current_type1_count < limit_type1:
                    chosen_f = current_folder
            else:
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
            # --- YENİ: ORTA ENGEL AKTİFKEN YÖRÜNGEDE KİMSE YOKSA YAKINDAKİ YARATIĞI AL ---
            # --- ORTA ENGEL AKTİFKEN YÖRÜNGEDE KİMSE YOKSA SADECE 1 YARATIK AL ---
            if self.big_wall_active and not self.big_wall_pending_destroy:
                # Şu an yörüngede AKTİF dönen biri var mı kontrol et
                any_orbiting = any(s.is_orbiting for s in self.spider_list)
                if not any_orbiting:
                    # Büyük engelin koordinatlarını bul
                    for wall in self.walls:
                        if wall.get("is_big", False):
                            wx, wy, ww, wh = wall["rect"]
                            
                            # Uygun bir yaratık bul ve döngüyü hemen kır!
                            for s in self.spider_list:
                                if not s.is_grabbed and not s.is_flung and not s.is_orbiting:
                                    s.start_orbiting(wx, wy, ww, wh)
                                    break # <--- KRİTİK: İlk yaratığı aldıktan sonra döngüden çık, diğerleri serbest gezsin!

            else:
                if self.big_wall_pending_destroy:
                    self.big_wall_destroy_timer -= dt
                    if self.big_wall_destroy_timer <= 0:
                        self.big_wall_pending_destroy = False
                        self.big_wall_active = False
                        
                        # --- SÜRE BİTTİĞİNDE DEVASA PATLAMA EFEKTİNİ TETİKLE ---
                        if hasattr(self, 'particle_emitter'):
                            for wall in self.walls:
                                if wall.get("is_big", False):
                                    # Orta engelin koordinatlarını alıp parçacık motoruna gönderiyoruz
                                    r = wall["rect"]
                                    # Büyük duvar olduğu için yaratık boyutunu (creature_size) 300 vererek patlamayı devasa yapıyoruz
                                    self.particle_emitter.spawn_shattered_wall(r, wall["color"], creature_size=300)
                        
                        # Büyük engeli listeden temizle ve ekranı güncelle
                        self.walls = [w for w in self.walls if not w.get("is_big", False)]
                        self.redraw_walls()
                        self.big_wall_timer = 0.0  

            for spider in list(self.spider_list):
                if spider in self.spider_list:
                    spider.update_entity(dt, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.settings, self.walls, self.spider_list)

        self.particle_layer.canvas.clear()
        self.particle_emitter.update_particles(dt)
        # --- HAKKINDA SAYFASI PARILTI MOTORU GİRİNTİ DÜZENLEMESİ ---
        if self.current_view == "about" and self.ui_visible and hasattr(self, 'sparkle_layer') and self.sparkle_layer:
            self.sparkle_spawn_timer += dt
            if self.sparkle_spawn_timer >= 0.25:
                self.sparkle_spawn_timer = 0.0
                if len(self.about_sparkles) < 15:
                    sp_x = random.uniform(self.SCREEN_WIDTH * 0.1, self.SCREEN_WIDTH * 0.9)
                    # Sizin yeni panel konumunuza göre alt ve üst sınır genişletildi (4 adet boşluk girintili)
                    sp_y = random.uniform(self.SCREEN_HEIGHT * 0.27, self.SCREEN_HEIGHT * 0.85)
                    base_color = random.choice([[1.0, 0.85, 0.2], [1.0, 1.0, 1.0]])
                    sparkle_form = random.choice(["plus", "star"])
                    
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
                    thick = sz / 10
                    
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

class KivySpiderEntity:
    _id_counter = 0
    def __init__(self, settings, sw, sh, animation_folders, zorunlu_klasor=None):
        KivySpiderEntity._id_counter += 1
        self.id = KivySpiderEntity._id_counter
        
        safe_settings = settings if (settings and isinstance(settings, dict)) else {}
        app = App.get_running_app()
        
        # --- KESİN TAMİR: Eğer update motoru zorunlu bir klasör belirttiyse, başka hiçbir şart aramadan onu ata ---
        if zorunlu_klasor is not None:
            self.assigned_folder = zorunlu_klasor
        else:
            filtered1 = app.get_filtered_folders_by_slot(1) if app else ["default"]
            filtered2 = app.get_filtered_folders_by_slot(2) if app else ["default"]
            
            # Sınıftaki gerçek klasör sayısını doğrudan kontrol ediyoruz
            if len(filtered1) <= 1 or safe_settings.get("type2_enabled", 1) == 0:
                idx1 = safe_settings.get("animation_folder_idx", 0)
                self.assigned_folder = filtered1[idx1 % len(filtered1)]
            else:
                if self.id % 2 == 1:
                    idx2 = safe_settings.get("animation_folder_idx2", 0)
                    self.assigned_folder = filtered2[idx2 % len(filtered2)]
                else:
                    idx1 = safe_settings.get("animation_folder_idx", 0)
                    self.assigned_folder = filtered1[idx1 % len(filtered1)]
            
        local = safe_settings.get("folder_settings", {}).get(self.assigned_folder, {})
        if not local:
            local = safe_settings
            
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
        
        self.reload_textures(safe_settings, animation_folders)
        self.is_flung = False
        self.touch_history = []  
        self.roll_angle = 0.0   
        self.roll_speed = 0.0   
        self.setup_canvas()
    def start_orbiting(self, wx, wy, ww, wh):
        if self.is_grabbed or self.is_orbiting: return
        
        app = App.get_running_app()
        if app and hasattr(app, 'spider_list'):
            if any(s.is_orbiting for s in app.spider_list if s.id != self.id):
                return
                
        self.is_orbiting = True
        self.orbit_wx, self.orbit_wy, self.orbit_ww, self.orbit_wh = wx, wy, ww, wh
        
        # --- YENİ: RASTGELE DÖNÜŞ YÖNÜ SEÇİMİ (1: Saat yönü tersi, -1: Saat yönü) ---
        self.orbit_direction = random.choice([1, -1])
        
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
        
        if self.assigned_folder == "default":
            self.anim_path_root = os.path.join(base_dir, "anims")
        else:
            self.anim_path_root = os.path.join(base_dir, "anims", self.assigned_folder)
            
        self.total_frames = 0
        self.textures = {}
        safe_settings = settings if (settings and isinstance(settings, dict)) else {}
        local = safe_settings.get("folder_settings", {}).get(self.assigned_folder, safe_settings)
        
        if os.path.exists(self.anim_path_root):
            try:
                matched_files = []
                for f in os.listdir(self.anim_path_root):
                    f_low = f.lower()
                    if f_low.endswith('.png') and 'bg' not in f_low:
                        # .png uzantısını güvenli string dilimleme ile kesip saf dosya adını alıyoruz
                        pure_name = f_low[:-4]
                        try:
                            file_num = int(pure_name)
                            matched_files.append((file_num, f))
                        except ValueError:
                            continue
                                
                matched_files.sort(key=lambda x: x[0])
                self.total_frames = len(matched_files)
                
                for idx, (num, original_filename) in enumerate(matched_files):
                    p = os.path.join(self.anim_path_root, original_filename)
                    core_img = CoreImage(p, nocache=True)
                    self.textures[idx] = core_img.texture
            except Exception as e: 
                print(f"Doku tarama hatası: {e}")
                self.total_frames = 0
                
        # --- EMNİYET KEMERİ (FALLBACK) ---
        if self.total_frames == 0:
            try:
                fallback_files = []
                fallback_path = os.path.join(base_dir, "anims")
                if os.path.exists(fallback_path):
                    for f in os.listdir(fallback_path):
                        f_low = f.lower()
                        if f_low.endswith('.png') and 'bg' not in f_low:
                            pure_name = f_low[:-4]
                            try:
                                file_num = int(pure_name)
                                fallback_files.append((file_num, f))
                            except ValueError: continue
                    fallback_files.sort(key=lambda x: x[0])
                    for idx, (num, original_filename) in enumerate(fallback_files):
                        p = os.path.join(fallback_path, original_filename)
                        core_img = CoreImage(p, nocache=True)
                        self.textures[self.total_frames] = core_img.texture
                        self.total_frames += 1
            except: pass
                    
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
            
            # --- ASPEKT ORANI KORUMALI KÜTLE MOTORU ---
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
                self.super_glow = Ellipse(
                    pos=(self.x + (self.size - glow_w)/2, self.y + (self.size - glow_h)/2), 
                    size=(glow_w, glow_h)
                )
            if has_texture:
                Color(1.0, 1.0, 1.0, 1.0)
                self.rect_mesh = Rectangle(
                    texture=self.textures.get(self.current_frame), 
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
            
            # --- YÖRÜNGEYİ BIRAK AMA ENGELİ YOK ETME (YENİ YARATIK BEKLESİN) ---
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
        else: self.roll_speed = 0.0

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
            else: self.is_flung = False
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
            
            # Dönüş yönüne göre hedef bakış açısını esnetiyoruz
            d_mult = 1.0 if self.orbit_direction == 1 else -1.0
            t_ang = math.pi if self.orbit_phase == 0 else (math.pi*0.5 if self.orbit_phase == 1 else (0.0 if self.orbit_phase == 2 else math.pi*1.5))
            if self.orbit_direction == -1:
                t_ang = (t_ang + math.pi) % (2 * math.pi) # Ters yönde bakış açısını çevir
                
            c_spd = base_spd
            
            # --- DİNAMİK YÖNLÜ FAZ GEÇİŞLERİ ---
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
                        if walls[i].get("is_big", False):
                            if app:
                                app.big_wall_active = False
                                app.big_wall_pending_destroy = False
                                app.big_wall_timer = 0.0
                            for s in spider_list:
                                if s.is_orbiting: s.is_orbiting = False; s.angle = random.uniform(0, 2 * math.pi)
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
                    bounce_speed = max(base_spd, math.sqrt(self.vx**2 + self.vy**2) * 0.85) 
                    self.vx, self.vy = math.cos(self.angle) * bounce_speed, math.sin(self.angle) * bounce_speed
                    self.x, self.y = n_x, n_y
                    self.finalize_transforms(settings)
                    return
                    
        if self.is_super and app and hasattr(app, 'particle_emitter'):
            glow_sz = getattr(self, 'super_glow_size', self.size * 1.25)
            app.particle_emitter.spawn_super_trail(self.x, self.y, self.size, [1.0, 0.84, 0.0], glow_size=glow_sz)

        if app and app.gold_orb:
            self_center_x, self_center_y = n_x + self.size / 2, n_y + self.size / 2
            orb_center_x, orb_center_y = app.gold_orb["x"] + app.gold_orb["size"] / 2, app.gold_orb["y"] + app.gold_orb["size"] / 2
            if math.sqrt((orb_center_x - self_center_x)**2 + (orb_center_y - self_center_y)**2) < (self.size * 0.35) + (app.gold_orb["size"] / 2):
                self.activate_super_power(15.0)  
                app.gold_orb = None; app.gold_orb_timer = 0.0
                app.gold_orb_spawn_time = random.uniform(20.0, 40.0) 
                app.gold_orb_layer.canvas.clear()  

        if spider_list:
            for other in list(spider_list):
                if not other or other.id == self.id or other.is_orbiting or other.is_grabbed: continue
                self_center_x, self_center_y = n_x + self.size / 2, n_y + self.size / 2
                other_center_x, other_center_y = other.x + other.size / 2, other.y + other.size / 2
                dx, dy = other_center_x - self_center_x, other_center_y - self_center_y
                distance = math.sqrt(dx**2 + dy**2)
                min_distance = (self.size * 0.35 + other.size * 0.35) - (self.visual_offset * 0.5 + other.visual_offset * 0.5)
                
                if not hasattr(self, '_active_passings'): self._active_passings = set()
                if not hasattr(other, '_active_passings'): other._active_passings = set()

                if distance < min_distance and distance > 0:
                    if self.is_super and not other.is_super:
                        try: 
                            if app and hasattr(app, 'particle_emitter'): app.particle_emitter.spawn_shattered_wall([other.x, other.y, other.size, other.size], [random.random(), random.random(), random.random(), 1.0], self.size)
                            other.canvas_widget.canvas.clear(); app.creature_layer.remove_widget(other.canvas_widget)
                            if other in spider_list: spider_list.remove(other)
                        except: pass
                        continue
                    elif not self.is_super and other.is_super:
                        try: 
                            if app and hasattr(app, 'particle_emitter'): app.particle_emitter.spawn_shattered_wall([self.x, self.y, self.size, self.size], [random.random(), random.random(), random.random(), 1.0], other.size)
                            self.canvas_widget.canvas.clear(); app.creature_layer.remove_widget(self.canvas_widget)
                            if self in spider_list: spider_list.remove(self)
                        except: pass
                        return
                        
                    if other.id in self._active_passings or self.id in other._active_passings:
                        self.roll_speed = self.roll_angle = other.roll_speed = other.roll_angle = 0.0
                        continue

                    if random.random() < 0.50:
                        self._active_passings.add(other.id); other._active_passings.add(self.id)
                        continue 

                    nx_vec, ny_vec = dx / distance, dy / distance
                    tx_vec, ty_vec = -ny_vec, nx_vec
                    v1n, v1t = self.vx * nx_vec + self.vy * ny_vec, self.vx * tx_vec + self.vy * ty_vec
                    v2n, v2t = other.vx * nx_vec + other.vy * ny_vec, other.vx * tx_vec + other.vy * ty_vec
                    
                    if self.is_flung: other.is_flung = True
                    elif other.is_flung: self.is_flung = True
                    
                    self.vx, self.vy = v2n * nx_vec + v1t * tx_vec, v2n * ny_vec + v1t * tx_vec
                    other.vx, other.vy = v1n * nx_vec + v2t * tx_vec, v1n * ny_vec + v2t * ty_vec
                    self.angle, other.angle = math.atan2(self.vy, self.vx) % (2 * math.pi), math.atan2(other.vy, other.vx) % (2 * math.pi)
                    
                    rel_vel_n = v1n - v2n
                    roll_intensity = max(20.0, abs(rel_vel_n) * 3.0) 
                    self.roll_speed = -roll_intensity if rel_vel_n > 0 else roll_intensity
                    other.roll_speed = roll_intensity if rel_vel_n > 0 else -roll_intensity
                    
                    overlap = min_distance - distance
                    n_x -= (overlap / 2) * nx_vec; n_y -= (overlap / 2) * ny_vec
                    other.x += (overlap / 2) * nx_vec; other.y += (overlap / 2) * ny_vec
                    self.x, self.y = n_x, n_y
                    self.finalize_transforms(settings)
                    return
                else:
                    if hasattr(self, '_active_passings') and other.id in self._active_passings: self._active_passings.remove(other.id)
                    if hasattr(other, '_active_passings') and self.id in other._active_passings: other._active_passings.remove(self.id)

        self.x, self.y = n_x, n_y
        sf_w, sf_h = (sw if sw > 100 else 1080), (sh if sh > 100 else 1920)
        if (self.x + self.size < -50 or self.x > sf_w + 50 or self.y + self.size < -50 or self.y > sf_h + 50): 
            edge = random.randint(0, 3)
            if edge == 0: self.x = -self.size + 10; self.y = random.randint(0, max(1, sf_h - self.size))
            elif edge == 1: self.x = sf_w - 10; self.y = random.randint(0, max(1, sf_h - self.size))
            elif edge == 2: self.x = random.randint(0, max(1, sf_w - self.size)); self.y = -self.size + 10
            elif edge == 3: self.x = random.randint(0, max(1, sf_w - self.size)); self.y = sf_h - 10
            self.angle = random.uniform(0, 2 * math.pi)
            self.vx, self.vy = math.cos(self.angle) * base_spd, math.sin(self.angle) * base_spd
            
        if abs(self.roll_speed) > 1.0:
            self.roll_angle += self.roll_speed * dt
            self.roll_speed *= 0.5 
        else:
            self.roll_speed = 0.0
            if abs(self.roll_angle) > 0.1: self.roll_angle += (0.0 - self.roll_angle) * (dt * 8.0)
            else: self.roll_angle = 0.0
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
                
            # --- KRİTİK: TERS YÖNDE DÖNÜLÜYORSA AYNALAMA (FLIP) YAP ---
            if hasattr(self, 'orbit_direction') and self.orbit_direction == -1:
                fy = -fy
        else:
            if facing_mode == 0:    
                t_ang = move_deg
                if 90 < (t_ang % 360) <= 270: t_ang = t_ang - 180; fx = -1  
            elif facing_mode == 1:  
                t_ang = move_deg - 90
                if 90 < (move_deg % 360) <= 270: fx = -1 
            elif facing_mode == 2:  
                t_ang = move_deg - 180
                if not (90 < (move_deg % 360) <= 270): t_ang = t_ang - 180; fx = -1  
            elif facing_mode == 3:  
                t_ang = move_deg - 270
                if 90 < (move_deg % 360) <= 270: fx = -1

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
