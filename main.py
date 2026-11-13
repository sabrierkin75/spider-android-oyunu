# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, Ellipse, RoundedRectangle
from kivy.graphics.context_instructions import PushMatrix, PopMatrix, Rotate
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
import random
import math
import time
import os
import json

# Android ve PC için doğru ana dizini (anims klasörünün olduğu yeri) bulur
if 'ANDROID_ARGUMENT' in os.environ:
    current_dir = os.path.abspath(".")
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))

# Ayar ve hata dosyaları için Android'de yazma izni olan dizini kullanır
def get_writable_dir():
    app = App.get_running_app()
    if app and hasattr(app, 'user_data_dir') and app.user_data_dir:
        return app.user_data_dir
    return current_dir

def hata_yaz(mesaj):
    try:
        with open(os.path.join(get_writable_dir(), "hata_kaydi.txt"), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {mesaj}\n")
    except:
        pass

global_settings = {
    'animation': 'spider',
    'min_period': 1.0,
    'max_period': 4.0,
    'base_delay': 0.18,
    'speed': 4,
    'sprite_facing_direction': 'SAG',
    'bg_image_name': 'arkaplan.png',
    'scale_factor': 1.0
}

speed_level = 1.0


try:
    ayar_yolu = os.path.join(current_dir, "oyun_ayarlari.json")
    if os.path.exists(ayar_yolu):
        with open(ayar_yolu, "r", encoding="utf-8") as f:
            tum_hafiza = json.load(f)
            if 'aktif_animasyon' in tum_hafiza:
                global_settings['animation'] = tum_hafiza['aktif_animasyon']
            aktif_anim_adi = global_settings['animation']
            if 'animasyonlar' in tum_hafiza and aktif_anim_adi in tum_hafiza['animasyonlar']:
                global_settings.update(tum_hafiza['animasyonlar'][aktif_anim_adi])
except Exception as e:
    hata_yaz(f"JSON Yukleme Hatasi: {str(e)}")

MIN_SPEED_LIMIT = 1
MAX_SPEED_LIMIT = 25
global_scale_factor = global_settings.get('scale_factor', 1.0)
MIN_SCALE_LIMIT = 0.4
MAX_SCALE_LIMIT = 2.5

from kivy.resources import resource_find

def get_available_animations():
    anims_path = resource_find("anims") or os.path.join(current_dir, "anims")
    if not os.path.exists(anims_path):
        return ['spider', 'spider2', 'spider3']
    try:
        subdirs = sorted([d for d in os.listdir(anims_path) if os.path.isdir(os.path.join(anims_path, d))])
        return subdirs if subdirs else ['spider', 'spider2', 'spider3']
    except Exception as e:
        hata_yaz(f'Animasyon listesi alınamadı: {str(e)}')
        return ['spider', 'spider2', 'spider3']

available_anims = get_available_animations()
current_anim_index = 0
if global_settings['animation'] in available_anims:
    current_anim_index = available_anims.index(global_settings['animation'])

def load_masked_png_frames(anim_name):
    frames = []
    anims_root = resource_find("anims") or os.path.join(current_dir, "anims")
    anim_path = os.path.join(anims_root, anim_name)
    
    if not os.path.exists(anim_path):
        return ["orumcek.png"]
    try:
        all_files = os.listdir(anim_path)
    except:
        return ["orumcek.png"]
    
    color_files = sorted([f for f in all_files if f.lower().endswith('.png')])
    for file_name in color_files:
        frames.append(os.path.join(anim_path, file_name))
    
    return frames if frames else ["orumcek.png"]

def ayari_animasyona_ozel_kaydet():
    try:
        ayar_yolu = os.path.join(current_dir, "oyun_ayarlari.json")
        tum_json_hafiza = {}
        if os.path.exists(ayar_yolu):
            try:
                with open(ayar_yolu, "r", encoding="utf-8") as f:
                    tum_json_hafiza = json.load(f)
            except:
                tum_json_hafiza = {}
        if 'animasyonlar' not in tum_json_hafiza:
            tum_json_hafiza['animasyonlar'] = {}
            
        tum_json_hafiza['aktif_animasyon'] = global_settings['animation']
        aktif_anim_adi = global_settings['animation']
        tum_json_hafiza['animasyonlar'][aktif_anim_adi] = {
            'base_delay': global_settings['base_delay'],
            'speed': global_settings['speed'],
            'sprite_facing_direction': global_settings['sprite_facing_direction'],
            'scale_factor': global_settings['scale_factor']
        }
        with open(ayar_yolu, "w", encoding="utf-8") as json_dosya:
            json.dump(tum_json_hafiza, json_dosya, indent=4)
    except Exception as e:
        hata_yaz(f"Animasyona Ozel JSON Kayit Hatasi: {str(e)}")

class KivyParcacik:
    def __init__(self, x, y, ozel_renk=None):
        self.x = x
        self.y = y
        acisal = random.uniform(0, math.pi * 2)
        hiz = random.uniform(2, 6) if not ozel_renk else random.uniform(3, 9)
        self.vx = math.cos(acisal) * hiz
        self.vy = math.sin(acisal) * hiz
        self.omur = 1.0
        if ozel_renk:
            self.renk = ozel_renk
        else:
            self.renk = random.choice([
                (231/255.0, 76/255.0, 60/255.0, 1),
                (241/255.0, 196/255.0, 15/255.0, 1),
                (142/255.0, 68/255.0, 173/255.0, 1)
            ])

    def guncelle(self, dt):
        self.x += self.vx * (dt * 60)
        self.y += self.vy * (dt * 60)
        self.omur -= 0.03 * (dt * 60)

class KivyAv:
    def __init__(self, tur="sinek", sidebar_duvarlar=None):
        self.tur = tur
        self.is_caught = False
        self.kanat_sayaci = random.uniform(0, 10)
        self.duvarlar = sidebar_duvarlar if sidebar_duvarlar is not None else []
        
        if self.tur == "ari":
            self.boyut = random.randint(12, 16)
            self.renk = (241/255.0, 196/255.0, 15/255.0, 1)
            self.puan = 3
        else:
            self.boyut = random.randint(6, 11)
            self.renk = (40/255.0, 40/255.0, 40/255.0, 1)
            self.puan = 1
            
        self.guvenli_konumlandir()

    def guvenli_konumlandir(self):
        # Güncel pencere boyutunu alıyoruz
        min_x = 50
        max_x = max(51, int(Window.width - 50))
        min_y = 50
        max_y = max(51, int(Window.height - 50))
        
        for _ in range(50):
            self.x = random.randint(min_x, max_x)
            self.y = random.randint(min_y, max_y)
            if not self.duvara_carpiyor_mu(self.x, self.y):
                break
                
        hiz_carpan = random.uniform(0.8, 1.5) * speed_level
        if self.tur == "ari":
            hiz_carpan *= 1.6
            
        self.vx = random.choice([-3, 3]) * hiz_carpan
        self.vy = random.choice([-3, 3]) * hiz_carpan

    def duvara_carpiyor_mu(self, test_x, test_y):
        b = self.boyut
        for d in self.duvarlar:
            dx, dy = d['pos']
            dw, dh = d['size']
            if (test_x - b < dx + dw and test_x + b > dx and 
                test_y - b < dy + dh and test_y + b > dy):
                return True
        return False

    def guncelle(self, spider_cx, spider_cy, dt):
        self.kanat_sayaci += dt * 3
        
        if self.is_caught:
            dx = spider_cx - self.x
            dy = spider_cy - self.y
            dist = math.hypot(dx, dy)
            if dist > 5:
                jitter_x = random.uniform(-3, 3)
                jitter_y = random.uniform(-3, 3)
                self.x += ((dx / dist) * 14 + jitter_x) * (dt * 60)
                self.y += ((dy / dist) * 14 + jitter_y) * (dt * 60)
        else:
            dx_spider = self.x - spider_cx
            dy_spider = self.y - spider_cy
            mesafe_spider = math.hypot(dx_spider, dy_spider)
            
            if self.tur == "ari" and mesafe_spider < 250 and mesafe_spider > 0:
                self.vx = (dx_spider / mesafe_spider) * random.uniform(5, 7) * speed_level
                self.vy = (dy_spider / mesafe_spider) * random.uniform(5, 7) * speed_level
                
            eski_x, eski_y = self.x, self.y
            
            self.x += self.vx * (dt * 60)
            self.y += self.vy * (dt * 60)
                
            if self.x <= 10 or self.x >= Window.width - 10: 
                self.vx *= -1
                self.x = max(10, min(self.x, Window.width - 10))
            if self.y <= 10 or self.y >= Window.height - 10: 
                self.vy *= -1
                self.y = max(10, min(self.y, Window.height - 10))
            
            if self.duvara_carpiyor_mu(self.x, self.y):
                self.x, self.y = eski_x, eski_y
                if random.random() < 0.5: self.vx *= -1
                else: self.vy *= -1

class SpiderGame(Widget):
    def __init__(self, **kwargs):
        super(SpiderGame, self).__init__(**kwargs)
        
        self.skor = 0
        self.toplam_tebrik_sayisi = 0
        self.kalan_sure = 300
        self.game_over = False
        self.ui_panel_acik = False
        self.tebrik_tetiklendi = False
        self.son_ayar_zamani = time.time()
        
        self.geri_sayim_aktif = True
        self.geri_sayim_baslangic = time.time()
        self.geri_sayim_deger = 3
        
        self.base_frames = load_masked_png_frames(global_settings['animation'])
        self.current_frame_index = 0
        self.last_frame_update = time.time()
        
        self.global_scale_factor = global_settings.get('scale_factor', 1.0)
        self.sprite_w = int(130 * self.global_scale_factor)
        self.sprite_h = int(130 * self.global_scale_factor)
        self.sprite_x = Window.width / 2
        self.sprite_y = Window.height / 2
        self.target_x, self.target_y = self.sprite_x, self.sprite_y
        
        self.inertia_vx = 0.0
        self.inertia_vy = 0.0
        self.friction = 0.97
        self.last_touch_x = 0
        self.last_touch_y = 0
        self.touch_velocity_x = 0
        self.touch_velocity_y = 0
        
        self.is_moving = False
        self.is_dragging = False
        self.skor_pop_efekti = 1.0
        self.current_angle = 0.0
        
        self.tebrik_gosteriliyor = False
        self.tebrik_baslangic_zamani = 0.0
        self.olum_efekti_patladi = False
        self.ruh_aktif = False
        self.ruh_x = self.sprite_x
        self.ruh_y = self.sprite_y
        self.ruh_alfa = 200
        
        self.duvarlar = []
        self.avlar = []
        self.parcaciklar = []
        self.spider_web_trail = []
        
        self.wait_start_time = time.time()
        self.wait_duration = 1.0
        self.rastgele_duvarlari_olustur()
        self.orumcek_guvenli_konumlandir()
        self.avları_olustur()
        
        Clock.schedule_interval(self.ana_guncelleme, 1.0 / 60.0)
        Clock.schedule_interval(self.zaman_sayici, 1.0)

    def rastgele_duvarlari_olustur(self):
        self.duvarlar.clear()
        r = random.randint(70, 200) / 255.0
        g = random.randint(70, 200) / 255.0
        b = random.randint(70, 200) / 255.0
        self.duvar_govde_renk = (r, g, b, 1)
        self.duvar_kenar_renk = (max(0, r - 0.15), max(0, g - 0.15), max(0, b - 0.15), 1)

        for _ in range(6):
            yon = random.choice(['YATAY', 'DIKEY'])
            w, h = (random.randint(140, 250), 24) if yon == 'YATAY' else (24, random.randint(140, 250))
            
            min_x = 100
            max_x = max(101, int(Window.width - w - 100))
            min_y = 150
            max_y = max(151, int(Window.height - h - 150))
            
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)

            yeni_duvar = {'pos': (x, y), 'size': (w, h)}
            akraba_var_mi = False
            for d in self.duvarlar:
                dx, dy = d['pos']
                dw, dh = d['size']
                if (x < dx + dw and x + w > dx and y < dy + dh and y + h > dy):
                    akraba_var_mi = True
                    break
            if not akraba_var_mi:
                self.duvarlar.append(yeni_duvar)

    def avları_olustur(self):
        self.avlar = [KivyAv("sinek", self.duvarlar) for _ in range(3)] + [KivyAv("ari", self.duvarlar)]

    def orumcek_guvenli_konumlandir(self):
        hit_w, hit_h = self.sprite_w * 0.75, self.sprite_h * 0.75
        
        min_x = 50
        max_x = max(51, int(Window.width - self.sprite_w - 50))
        min_y = 50
        max_y = max(51, int(Window.height - self.sprite_h - 50))

        for _ in range(100):
            tx = random.randint(min_x, max_x)
            ty = random.randint(min_y, max_y)

            carpisma = False
            for d in self.duvarlar:
                dx, dy = d['pos']
                dw, dh = d['size']
                if (tx < dx + dw and tx + hit_w > dx and ty < dy + dh and ty + hit_h > dy):
                    carpisma = True
                    break
            if not carpisma:
                self.sprite_x, self.sprite_y = tx, ty
                self.target_x, self.target_y = tx, ty
                break

    def on_touch_down(self, touch):
        if self.game_over or self.geri_sayim_aktif: return False
        if touch.x > Window.width * 0.80 and touch.y > Window.height * 0.88:
            return False
        if self.ui_panel_acik and touch.x > Window.width * 0.80:
            return False

        if (self.sprite_x <= touch.x <= self.sprite_x + self.sprite_w and
            self.sprite_y <= touch.y <= self.sprite_y + self.sprite_h):
            self.is_dragging = True
            self.is_moving = False
            self.inertia_vx = 0.0
            self.inertia_vy = 0.0
            self.last_touch_x, self.last_touch_y = touch.x, touch.y
            return True
        else:
            self.target_x = touch.x - self.sprite_w / 2
            self.target_y = touch.y - self.sprite_h / 2
            self.is_moving = True
            self.is_dragging = False
            self.inertia_vx = 0.0
            self.inertia_vy = 0.0
            return True

    def on_touch_move(self, touch):
        if self.is_dragging and not self.game_over:
            self.touch_velocity_x = touch.x - self.last_touch_x
            self.touch_velocity_y = touch.y - self.last_touch_y
            self.last_touch_x, self.last_touch_y = touch.x, touch.y

            nx = max(0, min(touch.x - self.sprite_w / 2, Window.width - self.sprite_w))
            ny = max(0, min(touch.y - self.sprite_h / 2, Window.height - self.sprite_h))

            hit_w, hit_h = self.sprite_w * 0.75, self.sprite_h * 0.75
            carpisma = False
            for d in self.duvarlar:
                dx, dy = d['pos']
                dw, dh = d['size']
                if (nx < dx + dw and nx + hit_w > dx and ny < dy + dh and ny + hit_h > dy):
                    carpisma = True
                    break
            if not carpisma:
                dx_ang = nx - self.sprite_x
                dy_ang = ny - self.sprite_y
                if math.hypot(dx_ang, dy_ang) > 1:
                    self.current_angle = math.degrees(math.atan2(dy_ang, dx_ang)) % 360
                self.sprite_x, self.sprite_y = nx, ny
                self.spider_web_trail.append({"pos": (self.sprite_x + self.sprite_w/2, self.sprite_y + self.sprite_h/2), "time": time.time()})

    def on_touch_up(self, touch):
        if self.is_dragging:
            self.is_dragging = False
            if math.hypot(self.touch_velocity_x, self.touch_velocity_y) > 3:
                self.inertia_vx = self.touch_velocity_x * 0.7
                self.inertia_vy = self.touch_velocity_y * 0.7

    def zaman_sayici(self, dt):
        if self.geri_sayim_aktif:
            gecen = time.time() - self.geri_sayim_baslangic
            if gecen < 1.0: self.geri_sayim_deger = 3
            elif gecen < 2.0: self.geri_sayim_deger = 2
            elif gecen < 3.0: self.geri_sayim_deger = 1
            elif gecen < 4.0: self.geri_sayim_deger = 0
            else:
                self.geri_sayim_aktif = False
                self.wait_start_time = time.time()
                self.wait_duration = random.uniform(global_settings['min_period'], global_settings['max_period'])
            return

        if not self.game_over and not self.geri_sayim_aktif:
            self.kalan_sure -= 1
            if self.kalan_sure <= 0 and self.toplam_tebrik_sayisi < 3:
                self.game_over = True
                if not self.olum_efekti_patladi:
                    sp_cx = self.sprite_x + self.sprite_w/2
                    sp_cy = self.sprite_y + self.sprite_h/2
                    for _ in range(50):
                        klor = random.choice([(46/255.0, 204/255.0, 113/255.0, 1), (155/255.0, 89/255.0, 182/255.0, 1)])
                        self.parcaciklar.append(KivyParcacik(sp_cx, sp_cy, klor))
                    self.ruh_x = sp_cx
                    self.ruh_y = sp_cy
                    self.ruh_alfa = 200
                    self.ruh_aktif = True
                    self.olum_efekti_patladi = True

    def ana_guncelleme(self, dt):
        global speed_level
        current_time = time.time()

        if self.ui_panel_acik and (time.time() - self.son_ayar_zamani >= 5.0):
            self.ui_panel_acik = False

        if self.skor_pop_efekti > 1.0:
            self.skor_pop_efekti -= 0.05 * (dt * 60)
        else:
            self.skor_pop_efekti = 1.0

        if self.game_over or self.geri_sayim_aktif:
            self.kivy_canvas_ciz(dt)
            return

        hit_w, hit_h = self.sprite_w * 0.75, self.sprite_h * 0.75
        sp_cx = self.sprite_x + (self.sprite_w / 2)
        sp_cy = self.sprite_y + (self.sprite_h / 2)

        if math.hypot(self.inertia_vx, self.inertia_vy) > 0.6:
            eski_x, eski_y = self.sprite_x, self.sprite_y
            self.sprite_x += self.inertia_vx * (dt * 60)
            for d in self.duvarlar:
                dx, dy = d['pos']
                dw, dh = d['size']
                if (self.sprite_x < dx + dw and self.sprite_x + hit_w > dx and eski_y < dy + dh and eski_y + hit_h > dy):
                    self.sprite_x = eski_x
                    self.inertia_vx *= -0.85

            self.sprite_y += self.inertia_vy * (dt * 60)
            for d in self.duvarlar:
                dx, dy = d['pos']
                dw, dh = d['size']
                if (self.sprite_x < dx + dw and self.sprite_x + hit_w > dx and self.sprite_y < dy + dh and self.sprite_y + hit_h > dy):
                    self.sprite_y = eski_y
                    self.inertia_vy *= -0.85

            self.spider_web_trail.append({"pos": (sp_cx, sp_cy), "time": current_time})
            if math.hypot(self.inertia_vx, self.inertia_vy) > 0.1:
                self.current_angle = math.degrees(math.atan2(self.inertia_vy, self.inertia_vx)) % 360

            if self.sprite_x <= 0 or self.sprite_x >= Window.width - self.sprite_w: self.inertia_vx *= -0.8
            if self.sprite_y <= 0 or self.sprite_y >= Window.height - self.sprite_h: self.inertia_vy *= -0.8
            self.sprite_x = max(0, min(self.sprite_x, Window.width - self.sprite_w))
            self.sprite_y = max(0, min(self.sprite_y, Window.height - self.sprite_h))
            self.inertia_vx *= self.friction
            self.inertia_vy *= self.friction
        else:
            if not self.is_moving and not self.is_dragging:
                if current_time - self.wait_start_time >= self.wait_duration:
                    min_x = 50
                    max_x = max(51, int(Window.width - self.sprite_w - 50))
                    min_y = 50
                    max_y = max(51, int(Window.height - self.sprite_h - 50))
                    
                    for _ in range(50):
                        tx = random.randint(min_x, max_x)
                        ty = random.randint(min_y, max_y)
                        t_rect_carpisma = False
                        for d in self.duvarlar:
                            dx, dy = d['pos']
                            dw, dh = d['size']
                            if (tx < dx + dw and tx + hit_w > dx and ty < dy + dh and ty + hit_h > dy):
                                t_rect_carpisma = True
                                break
                        if not t_rect_carpisma:
                            self.target_x, self.target_y = tx, ty
                            self.is_moving = True
                            break
                    if not self.is_moving:
                        self.wait_start_time = current_time
                        self.wait_duration = 0.2

            elif self.is_moving:
                dx = self.target_x - self.sprite_x
                dy = self.target_y - self.sprite_y
                dist = math.hypot(dx, dy)
                hiz_adimi = (global_settings['speed'] + 1) * (dt * 60)

                if dist > max(5.0, hiz_adimi):
                    eski_x, eski_y = self.sprite_x, self.sprite_y
                    self.sprite_x += (dx / dist) * hiz_adimi
                    self.sprite_y += (dy / dist) * hiz_adimi

                    carpiyor = False
                    for d in self.duvarlar:
                        dx_d, dy_d = d['pos']
                        dw, dh = d['size']
                        if (self.sprite_x < dx_d + dw and self.sprite_x + hit_w > dx_d and self.sprite_y < dy_d + dh and self.sprite_y + hit_h > dy_d):
                            carpiyor = True
                            break
                    if carpiyor:
                        self.sprite_x, self.sprite_y = eski_x, eski_y
                        self.is_moving = False
                        self.wait_start_time = current_time
                        self.wait_duration = 0.3
                    else:
                        self.spider_web_trail.append({"pos": (self.sprite_x + self.sprite_w/2, self.sprite_y + self.sprite_h/2), "time": current_time})
                        self.current_angle = math.degrees(math.atan2(dy, dx)) % 360
                else:
                    self.sprite_x, self.sprite_y = self.target_x, self.target_y
                    self.is_moving = False
                    self.wait_start_time = current_time
                    self.wait_duration = random.uniform(global_settings['min_period'], global_settings['max_period'])

        active_speed = global_settings['speed']
        if self.is_dragging: active_speed = math.hypot(self.touch_velocity_x, self.touch_velocity_y)
        elif math.hypot(self.inertia_vx, self.inertia_vy) > 0.2: active_speed = math.hypot(self.inertia_vx, self.inertia_vy)
        dynamic_delay = max(0.01, global_settings['base_delay'] / (active_speed * 0.4 + 0.6))

        if self.is_moving or self.is_dragging or math.hypot(self.inertia_vx, self.inertia_vy) > 0.2:
            if current_time - self.last_frame_update >= dynamic_delay:
                self.current_frame_index = (self.current_frame_index + 1) % len(self.base_frames)
                self.last_frame_update = current_time
        else:
            self.current_frame_index = 0

        for s in self.avlar:
            s.guncelle(sp_cx, sp_cy, dt)
            dist_av = math.hypot(s.x - sp_cx, s.y - sp_cy)

            if dist_av < (max(self.sprite_w, self.sprite_h) // 2 + 10):
                if s.is_caught:
                    self.skor += s.puan
                    self.skor_pop_efekti = 1.5
                    patlama_rengi = (241/255.0, 196/255.0, 15/255.0, 1) if s.tur == "ari" else None
                    for _ in range(15):
                        self.parcaciklar.append(KivyParcacik(s.x, s.y, patlama_rengi))

                    if self.skor >= 5 and not self.tebrik_tetiklendi:
                        self.tebrik_gosteriliyor = True
                        self.tebrik_baslangic_zamani = time.time()
                        self.toplam_tebrik_sayisi += 1
                        self.tebrik_tetiklendi = True
                        self.skor = 0
                    s.guvenli_konumlandir()
                    s.is_caught = False
            elif dist_av < 200 and not s.is_caught:
                s.is_caught = True

        if self.tebrik_gosteriliyor and time.time() - self.tebrik_baslangic_zamani >= 3.0:
            self.tebrik_gosteriliyor = False
            self.tebrik_tetiklendi = False
            if self.toplam_tebrik_sayisi >= 3:
                self.toplam_tebrik_sayisi = 0
                self.kalan_sure = 300
                speed_level *= 1.15
                self.rastgele_duvarlari_olustur()
                self.orumcek_guvenli_konumlandir()
                self.avları_olustur()

        self.kivy_canvas_ciz(dt)

    def kivy_canvas_ciz(self, dt):
        self.canvas.clear()
        current_time = time.time()

        with self.canvas:
            bg_name = global_settings['bg_image_name']
            bg_path = os.path.join(current_dir, bg_name)
            if os.path.exists(bg_path):
                Color(1, 1, 1, 1)
                Rectangle(source=bg_path, pos=(0, 0), size=(Window.width, Window.height))
            else:
                Color(0.17, 0.17, 0.17, 1)
                Rectangle(pos=(0, 0), size=(Window.width, Window.height))
                Color(0.23, 0.23, 0.23, 0.4)
                for x in range(0, int(Window.width), 60):
                    Line(points=[x, 0, x, Window.height], width=1)
                for y in range(0, int(Window.height), 60):
                    Line(points=[0, y, Window.width, y], width=1)

            self.spider_web_trail = [line for line in self.spider_web_trail if current_time - line["time"] < 4.0]
            if len(self.spider_web_trail) > 1:
                for i in range(len(self.spider_web_trail) - 1):
                    fade = min(1.0, (current_time - self.spider_web_trail[i]["time"]) / 4.0)
                    renk_val = 0.82 + (0.18 * fade)
                    Color(renk_val, renk_val, renk_val, 1.0 - fade)
                    p1 = self.spider_web_trail[i]["pos"]
                    p2 = self.spider_web_trail[i+1]["pos"]
                    Line(points=[p1[0], p1[1], p2[0], p2[1]], width=2)

            for d in self.duvarlar:
                Color(*self.duvar_govde_renk)
                Rectangle(pos=d['pos'], size=d['size'])

            for s in self.avlar:
                if s.is_caught:
                    Color(160/255.0, 165/255.0, 170/255.0, 0.9)
                    Line(points=[self.sprite_x + self.sprite_w/2, self.sprite_y + self.sprite_h/2, s.x, s.y], width=2)
                Color(*s.renk)
                Ellipse(pos=(s.x - s.boyut, s.y - s.boyut), size=(s.boyut * 2, s.boyut * 2))
                
                # Etraflarına beyaz çember çizimi
                Color(1, 1, 1, 0.9)
                Line(circle=(s.x, s.y, s.boyut + 3), width=1.5)
            kalan_p = []
            for p in self.parcaciklar:
                p.guncelle(dt)
                if p.omur > 0:
                    Color(*p.renk)
                    p_yaricap = max(3, int(14 * p.omur))
                    Ellipse(pos=(p.x - p_yaricap, p.y - p_yaricap), size=(p_yaricap * 2, p_yaricap * 2))
                    kalan_p.append(p)
            self.parcaciklar = kalan_p

            if not self.olum_efekti_patladi:
                sapma_acisi = 0
                mevcut_yon = global_settings['sprite_facing_direction'].upper()
                if mevcut_yon == 'YUKARI': sapma_acisi = -90
                elif mevcut_yon == 'SOL': sapma_acisi = 180
                elif mevcut_yon == 'ASAGI': sapma_acisi = 90

                # --- TEPE TAKLA ENGELLEME HESABI ---
                cal_ang = (self.current_angle + sapma_acisi) % 360
                if 90 < cal_ang < 270:
                    fx = -1
                    final_angle = cal_ang - 180
                else:
                    fx = 1
                    final_angle = cal_ang

                PushMatrix()
                pivot_x = self.sprite_x + self.sprite_w / 2
                pivot_y = self.sprite_y + self.sprite_h / 2
                Rotate(angle=final_angle, origin=(pivot_x, pivot_y))
                # Aynalama için Scale komutunu ekliyoruz (en üste Scale import edilmelidir)
                from kivy.graphics.context_instructions import Scale
                Scale(x=fx, y=1, origin=(pivot_x, pivot_y))

                aktif_resim = self.base_frames[self.current_frame_index] if self.base_frames else "orumcek.png"
                aktif_resim_yol = os.path.join(current_dir, aktif_resim)
                if os.path.exists(aktif_resim_yol) or os.path.exists(aktif_resim):
                    Color(1, 1, 1, 1)
                    Rectangle(source=aktif_resim_yol if os.path.exists(aktif_resim_yol) else aktif_resim, pos=(self.sprite_x, self.sprite_y), size=(self.sprite_w, self.sprite_h))
                else:
                    cx = self.sprite_x + self.sprite_w * 0.5
                    cy = self.sprite_y + self.sprite_h * 0.5
                    
                    # Hareket ediyorsa bacak sallanma açısını hesapla
                    hareket_halinde = (
                        self.is_moving or 
                        self.is_dragging or 
                        math.hypot(self.inertia_vx, self.inertia_vy) > 0.2
                    )
                    adim_fazi = (current_time * (global_settings['speed'] * 3.5)) if hareket_halinde else 0.0

                    # 1. SEKİZ ADET EKLEMLİ BACAK (4 Üst, 4 Alt)
                    Color(0.85, 0.22, 0.18, 1)
                    bacak_x_oranlari = [-0.22, -0.07, 0.08, 0.22]
                    for i, x_oran in enumerate(bacak_x_oranlari):
                        # Çapraz bacakların zıt yönde hareket etmesi için faz kaydırma
                        sallanti = math.sin(adim_fazi + (i * math.pi)) * (self.sprite_w * 0.08) if hareket_halinde else 0.0
                        
                        kok_x = cx + self.sprite_w * x_oran
                        diz_x = cx + self.sprite_w * (x_oran * 1.4) + sallanti
                        uc_x = cx + self.sprite_w * (x_oran * 1.8) - (sallanti * 0.5)

                        # Üst taraftaki 4 bacak
                        Line(points=[
                            kok_x, cy + self.sprite_h * 0.22,
                            diz_x, cy + self.sprite_h * 0.46,
                            uc_x,  cy + self.sprite_h * 0.56
                        ], width=2.2)

                        # Alt taraftaki 4 bacak
                        Line(points=[
                            kok_x, cy - self.sprite_h * 0.22,
                            diz_x, cy - self.sprite_h * 0.46,
                            uc_x,  cy - self.sprite_h * 0.56
                        ], width=2.2)

                    # 2. GÖVDE (Kafa ve Karın)
                    Color(231/255.0, 76/255.0, 60/255.0, 1)
                    # Arka gövde (Karın)
                    Ellipse(
                        pos=(self.sprite_x + self.sprite_w * 0.14, self.sprite_y + self.sprite_h * 0.22),
                        size=(self.sprite_w * 0.48, self.sprite_h * 0.56)
                    )
                    # Ön gövde (Kafa)
                    Ellipse(
                        pos=(self.sprite_x + self.sprite_w * 0.52, self.sprite_y + self.sprite_h * 0.28),
                        size=(self.sprite_w * 0.36, self.sprite_h * 0.44)
                    )

                    # 3. İKİ ADET GÖZ VE GÖZ BEBEKLERİ
                    Color(1, 1, 1, 1)
                    Ellipse(pos=(self.sprite_x + self.sprite_w * 0.72, self.sprite_y + self.sprite_h * 0.53), size=(self.sprite_w * 0.13, self.sprite_h * 0.13))
                    Ellipse(pos=(self.sprite_x + self.sprite_w * 0.72, self.sprite_y + self.sprite_h * 0.34), size=(self.sprite_w * 0.13, self.sprite_h * 0.13))
                    
                    Color(0.1, 0.1, 0.1, 1)
                    Ellipse(pos=(self.sprite_x + self.sprite_w * 0.78, self.sprite_y + self.sprite_h * 0.56), size=(self.sprite_w * 0.06, self.sprite_h * 0.06))
                    Ellipse(pos=(self.sprite_x + self.sprite_w * 0.78, self.sprite_y + self.sprite_h * 0.37), size=(self.sprite_w * 0.06, self.sprite_h * 0.06))
                PopMatrix()

            if self.ruh_aktif:
                self.ruh_y += 0.6 * (dt * 60)
                self.ruh_alfa -= 0.5 * (dt * 60)
                if self.ruh_alfa <= 0:
                    self.ruh_aktif = False
                else:
                    Color(1, 1, 1, max(0, min(1, self.ruh_alfa / 255.0)))
                    resim_ruh = self.base_frames[0] if (self.base_frames and isinstance(self.base_frames, list)) else "orumcek.png"
                    resim_ruh_yol = os.path.join(current_dir, resim_ruh)
                    if os.path.exists(resim_ruh_yol) or os.path.exists(resim_ruh):
                        Rectangle(source=resim_ruh_yol if os.path.exists(resim_ruh_yol) else resim_ruh, pos=(self.ruh_x - self.sprite_w/2, self.ruh_y - self.sprite_h/2), size=(self.sprite_w, self.sprite_h))
                    else:
                        Ellipse(pos=(self.ruh_x - self.sprite_w/2, self.ruh_y - self.sprite_h/2), size=(self.sprite_w, self.sprite_h))

    def ayar_degistir(self, aksiyon):
        global current_anim_index
        self.son_ayar_zamani = time.time()
        if aksiyon == 'hiz_arti':
            global_settings['speed'] = min(25, global_settings['speed'] + 1)
        elif aksiyon == 'hiz_eksi':
            global_settings['speed'] = max(1, global_settings['speed'] - 1)
        elif aksiyon == 'boyut_arti':
            if self.global_scale_factor < 2.5:
                self.global_scale_factor += 0.1
                global_settings['scale_factor'] = self.global_scale_factor
                self.sprite_w = int(130 * self.global_scale_factor)
                self.sprite_h = int(130 * self.global_scale_factor)
        elif aksiyon == 'boyut_eksi':
            if self.global_scale_factor > 0.4:
                self.global_scale_factor -= 0.1
                global_settings['scale_factor'] = self.global_scale_factor
                self.sprite_w = int(130 * self.global_scale_factor)
                self.sprite_h = int(130 * self.global_scale_factor)
        elif aksiyon == 'anim_degis':
            if len(available_anims) > 1:
                current_anim_index = (current_anim_index + 1) % len(available_anims)
                yeni_anim_adi = available_anims[current_anim_index]
                global_settings['animation'] = yeni_anim_adi

                try:
                    ayar_yolu = os.path.join(current_dir, "oyun_ayarlari.json")
                    if os.path.exists(ayar_yolu):
                        with open(ayar_yolu, "r", encoding="utf-8") as f:
                            tum_hafiza = json.load(f)
                            if 'animasyonlar' in tum_hafiza and yeni_anim_adi in tum_hafiza['animasyonlar']:
                                global_settings.update(tum_hafiza['animasyonlar'][yeni_anim_adi])
                            else:
                                global_settings['sprite_facing_direction'] = 'SAG'
                                global_settings['speed'] = 4
                                global_settings['base_delay'] = 0.18
                                global_settings['scale_factor'] = 1.0
                except:
                    pass

                self.global_scale_factor = global_settings.get('scale_factor', 1.0)
                self.sprite_w = int(130 * self.global_scale_factor)
                self.sprite_h = int(130 * self.global_scale_factor)
                self.base_frames = load_masked_png_frames(global_settings['animation'])
                self.current_frame_index = 0
        elif aksiyon == 'yon_sec':
            yonler = ['SAG', 'ASAGI', 'SOL', 'YUKARI']
            mevcut = global_settings['sprite_facing_direction'].upper()
            if mevcut in yonler:
                global_settings['sprite_facing_direction'] = yonler[(yonler.index(mevcut) + 1) % 4]
        elif aksiyon == 'fps_arti':
            global_settings['base_delay'] = max(0.02, global_settings['base_delay'] - 0.02)
        elif aksiyon == 'fps_eksi':
            global_settings['base_delay'] = min(1.5, global_settings['base_delay'] + 0.02)

        ayari_animasyona_ozel_kaydet()

    def oyunu_sifirla(self):
        global speed_level
        self.skor = 0
        self.toplam_tebrik_sayisi = 0
        self.kalan_sure = 300
        self.game_over = False
        self.olum_efekti_patladi = False
        self.ruh_aktif = False
        self.tebrik_tetiklendi = False
        self.geri_sayim_aktif = True
        self.geri_sayim_baslangic = time.time()
        speed_level = 1.0
        self.rastgele_duvarlari_olustur()
        self.orumcek_guvenli_konumlandir()
        self.avları_olustur()

class OrumcekOyunApp(App):
    def yuvarlak_buton_yap(self, btn, renk, yaricap=15):
        btn.background_color = (0, 0, 0, 0)
        btn.background_normal = ''
        btn.background_down = ''
        with btn.canvas.before:
            Color(*renk)
            btn.bg_rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[yaricap])
        def _guncelle(inst, val):
            inst.bg_rect.pos = inst.pos
            inst.bg_rect.size = inst.size
        btn.bind(pos=_guncelle, size=_guncelle)

    def build(self):
        self.main_layout = FloatLayout()
        self.oyun_ekrani = SpiderGame()
        self.main_layout.add_widget(self.oyun_ekrani)

        self.root = FloatLayout()
        self.main_layout.add_widget(self.root)

        self.btn_ayarlar = Button(
            text="Ayarlar", font_size='16sp', bold=True, size_hint=(None, 0.06),
            width=180, pos_hint={'right': 0.97, 'y': 0.90}, color=(1, 1, 1, 1)
        )
        self.yuvarlak_buton_yap(self.btn_ayarlar, (0.16, 0.50, 0.72, 1), yaricap=14)
        self.btn_ayarlar.bind(on_press=self.ayarlar_tetikle)
        self.root.add_widget(self.btn_ayarlar)

        self.menu_butonlari = []
        buton_verileri = [
            ("Hız +", lambda x: self.oyun_ekrani.ayar_degistir('hiz_arti')),
            ("Hız -", lambda x: self.oyun_ekrani.ayar_degistir('hiz_eksi')),
            ("Boyut +", lambda x: self.oyun_ekrani.ayar_degistir('boyut_arti')),
            ("Boyut -", lambda x: self.oyun_ekrani.ayar_degistir('boyut_eksi')),
            ("Animasyon", lambda x: self.oyun_ekrani.ayar_degistir('anim_degis')),
            ("Yön Seç", lambda x: self.oyun_ekrani.ayar_degistir('yon_sec')),
            ("Kare Hızı +", lambda x: self.oyun_ekrani.ayar_degistir('fps_arti')),
            ("Kare Hızı -", lambda x: self.oyun_ekrani.ayar_degistir('fps_eksi'))
        ]

        for i, (txt, fn) in enumerate(buton_verileri):
            y_pos = 0.81 - (i * 0.068)
            btn = Button(
                text=txt, font_size='14sp', bold=True,
                size_hint=(None, 0.055), padding=(20, 0),
                pos_hint={'right': 0.97, 'y': y_pos},
                color=(0.1, 0.1, 0.1, 1)
            )
            btn.bind(texture_size=lambda instance, value, b=btn: setattr(b, 'width', value[0] + 40))
            btn.bind(on_press=fn)
            self.yuvarlak_buton_yap(btn, (0.92, 0.92, 0.92, 1), yaricap=12)
            self.menu_butonlari.append(btn)

        self.sabit_etiketler = {}
        ui_y_oranlari = [0.85, 0.78, 0.71, 0.64, 0.57, 0.50]
        for i, y_orani in enumerate(ui_y_oranlari):
            lbl = Label(
                font_size='15sp', bold=True, size_hint=(None, None),
                pos_hint={'x': 0.02, 'y': y_orani}, padding=(15, 10)
            )
            with lbl.canvas.before:
                Color(0.08, 0.08, 0.08, 0.60)
                rect = Rectangle()
            lbl.bind(texture_size=lambda instance, value, l=lbl: setattr(l, 'size', value))
            lbl.bind(pos=lambda instance, value, r=rect: setattr(r, 'pos', instance.pos))
            lbl.bind(size=lambda instance, value, r=rect: setattr(r, 'size', instance.size))
            self.sabit_etiketler[f'lbl_{i}'] = lbl
            
        self.lbl_skor = Label(font_size="22sp", bold=True, size_hint=(None, None), pos_hint={'x': 0.02, 'y': 0.05}, padding=(25, 15))
        with self.lbl_skor.canvas.before:
            Color(0.08, 0.08, 0.08, 0.60)
            self.rect_skor = Rectangle()
        self.lbl_skor.bind(texture_size=lambda instance, value: setattr(self.lbl_skor, 'size', value))
        self.lbl_skor.bind(pos=lambda instance, value: setattr(self.rect_skor, 'pos', instance.pos))
        self.lbl_skor.bind(size=lambda instance, value: setattr(self.rect_skor, 'size', instance.size))

        self.lbl_acele = Label(
            text="ACELE ET!", font_size="45sp", bold=True, color=(0.9, 0.29, 0.23, 1),
            size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.78}, padding=(35, 20)
        )
        with self.lbl_acele.canvas.before:
            Color(0.08, 0.08, 0.08, 0.60)
            self.rect_acele = Rectangle()
        self.lbl_acele.bind(texture_size=lambda instance, value: setattr(self.lbl_acele, 'size', value))
        self.lbl_acele.bind(pos=lambda instance, value: setattr(self.rect_acele, 'pos', instance.pos))
        self.lbl_acele.bind(size=lambda instance, value: setattr(self.rect_acele, 'size', instance.size))

        self.lbl_gs = Label(
            font_size="60sp", bold=True, size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}, padding=(40, 25)
        )
        with self.lbl_gs.canvas.before:
            Color(0.08, 0.08, 0.08, 0.60)
            self.rect_gs = Rectangle()
        self.lbl_gs.bind(texture_size=lambda instance, value: setattr(self.lbl_gs, 'size', value))
        self.lbl_gs.bind(pos=lambda instance, value: setattr(self.rect_gs, 'pos', instance.pos))
        self.lbl_gs.bind(size=lambda instance, value: setattr(self.rect_gs, 'size', instance.size))

        self.lbl_tebrik = Label(
            font_size='35sp', bold=True, color=(39/255.0, 174/255.0, 96/255.0, 1),
            size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5},
            padding=(40, 25), halign='center', valign='middle'
        )
        with self.lbl_tebrik.canvas.before:
            Color(0.08, 0.08, 0.08, 0.75)
            self.rect_tebrik = RoundedRectangle(radius=[18])
        self.lbl_tebrik.bind(texture_size=lambda inst, val: setattr(inst, 'size', val))
        self.lbl_tebrik.bind(pos=lambda inst, val: setattr(self.rect_tebrik, 'pos', inst.pos))
        self.lbl_tebrik.bind(size=lambda inst, val: setattr(self.rect_tebrik, 'size', inst.size))

        self.lbl_bitti = Label(font_size='40sp', bold=True, color=(0.9, 0.3, 0.25, 1), pos_hint={'center_x': 0.5, 'center_y': 0.80})

        Clock.schedule_interval(self.ui_guncelle, 1.0 / 60.0)
        return self.main_layout

    def ui_guncelle(self, dt):
        self.btn_ayarlar.text = "Kapat" if self.oyun_ekrani.ui_panel_acik else "Ayarlar"

        for btn in self.menu_butonlari:
            if self.oyun_ekrani.ui_panel_acik:
                if btn not in self.root.children: self.root.add_widget(btn)
            else:
                if btn in self.root.children: self.root.remove_widget(btn)

        dakika = self.oyun_ekrani.kalan_sure // 60
        saniye = self.oyun_ekrani.kalan_sure % 60
        kare_hiz_seviyesi = round(0.18 / global_settings['base_delay'], 1)

        ui_veriler = [
            (f"Hız Seviyesi: {global_settings['speed']}", (1, 1, 0, 1)),
            (f"Kalan Süre: {dakika:02d}:{saniye:02d}", (1, 0.4, 0.4, 1)),
            (f"Ölçek: %{int(self.oyun_ekrani.global_scale_factor * 100)}", (1, 1, 0.35, 1)),
            (f"Ayak Hızı: {kare_hiz_seviyesi}x", (1, 0.58, 1, 1)),
            (f"Aktif Görünüm: {global_settings['animation']}", (100/255.0, 255/255.0, 100/255.0, 1)),
            (f"Görsel Yönü: {global_settings['sprite_facing_direction']}", (200/255.0, 200/255.0, 255/255.0, 1))
        ]

        for i, (metin, renk) in enumerate(ui_veriler):
            lbl = self.sabit_etiketler[f'lbl_{i}']
            lbl.text = metin
            lbl.color = renk
            if not self.oyun_ekrani.game_over:
                if lbl not in self.root.children: self.root.add_widget(lbl)

            else:
                if lbl in self.root.children: self.root.remove_widget(lbl)

        skor_font_boyutu = int(22 * self.oyun_ekrani.skor_pop_efekti)
        self.lbl_skor.font_size = f"{skor_font_boyutu}sp"
        self.lbl_skor.color = (0, 1, 1, 1) if self.oyun_ekrani.skor >= 5 else (1, 0, 1, 1)
        self.lbl_skor.text = f"Skor: {self.oyun_ekrani.skor} / 5 | Tur: {self.oyun_ekrani.toplam_tebrik_sayisi}"

        if not self.oyun_ekrani.game_over:
            if self.lbl_skor not in self.root.children: self.root.add_widget(self.lbl_skor)
        else:
            if self.lbl_skor in self.root.children: self.root.remove_widget(self.lbl_skor)

        if self.oyun_ekrani.kalan_sure <= 10 and self.oyun_ekrani.kalan_sure > 0 and not self.oyun_ekrani.game_over and not self.oyun_ekrani.geri_sayim_aktif:
            if self.lbl_acele not in self.root.children: self.root.add_widget(self.lbl_acele)
        else:
            if self.lbl_acele in self.root.children: self.root.remove_widget(self.lbl_acele)

        if self.oyun_ekrani.geri_sayim_aktif:
            self.lbl_gs.text = str(self.oyun_ekrani.geri_sayim_deger) if self.oyun_ekrani.geri_sayim_deger > 0 else "BAŞLA!"
            self.lbl_gs.color = (241/255.0, 196/255.0, 15/255.0, 1) if self.oyun_ekrani.geri_sayim_deger > 0 else (46/255.0, 204/255.0, 113/255.0, 1)
            if self.lbl_gs not in self.root.children: self.root.add_widget(self.lbl_gs)
        else:
            if self.lbl_gs in self.root.children: self.root.remove_widget(self.lbl_gs)

        if self.oyun_ekrani.tebrik_gosteriliyor and not self.oyun_ekrani.game_over:
            self.lbl_tebrik.text = "BÖLÜM TAMAMLANDI!" if self.oyun_ekrani.toplam_tebrik_sayisi >= 3 else "Harika Avcı!"
            if self.lbl_tebrik not in self.root.children: self.root.add_widget(self.lbl_tebrik)
        else:
            if self.lbl_tebrik in self.root.children: self.root.remove_widget(self.lbl_tebrik)

        if self.oyun_ekrani.game_over and not self.oyun_ekrani.ruh_aktif:
            if not hasattr(self, 'pnl_gameover'):
                self.pnl_gameover = FloatLayout(size_hint=(0.85, 0.50), pos_hint={'center_x': 0.5, 'center_y': 0.50})
                with self.pnl_gameover.canvas.before:
                    Color(0.10, 0.10, 0.12, 0.97)
                    self.rect_pnl = Rectangle()
                    Color(0.9, 0.3, 0.25, 1)
                    self.line_pnl = Line(width=3)

                def guncelle_panel_canvas(instance, value):
                    self.rect_pnl.pos = instance.pos
                    self.rect_pnl.size = instance.size
                    self.line_pnl.rectangle = (instance.x, instance.y, instance.width, instance.height)
                self.pnl_gameover.bind(pos=guncelle_panel_canvas, size=guncelle_panel_canvas)

                self.lbl_bitti.text = "OYUN BİTTİ"
                self.lbl_bitti.size_hint = (None, None)
                self.lbl_bitti.padding = (35, 15)
                self.lbl_bitti.halign = 'center'
                self.lbl_bitti.valign = 'middle'
                with self.lbl_bitti.canvas.before:
                    Color(0.05, 0.05, 0.05, 0.70)
                    self.rect_bitti = RoundedRectangle(radius=[15])
                self.lbl_bitti.bind(texture_size=lambda inst, val: setattr(inst, 'size', val))
                self.lbl_bitti.bind(pos=lambda inst, val: setattr(self.rect_bitti, 'pos', inst.pos))
                self.lbl_bitti.bind(size=lambda inst, val: setattr(self.rect_bitti, 'size', inst.size))
                self.pnl_gameover.add_widget(self.lbl_bitti)

                self.lbl_ozet = Label(
                    text=f"Tebrikler! Toplamda {self.oyun_ekrani.toplam_tebrik_sayisi} Tur Başarıyla Tamamlandı.\nAvlanma süresi dolduğu için simülasyon sonlandırıldı.",
                    font_size='18sp', color=(0.8, 0.8, 0.8, 1),
                    size_hint=(0.9, None), pos_hint={'center_x': 0.5, 'center_y': 0.56},
                    halign='center', valign='middle'
                )
                self.lbl_ozet.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
                self.lbl_ozet.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
                self.pnl_gameover.add_widget(self.lbl_ozet)

                btn_tekrar = Button(
                    text="Yeniden\nBaşlat", font_size='18sp', bold=True, size_hint=(0.35, 0.16),
                    pos_hint={'center_x': 0.32, 'center_y': 0.25},
                    halign='center', valign='middle'
                )
                self.yuvarlak_buton_yap(btn_tekrar, (39/255.0, 174/255.0, 96/255.0, 1), yaricap=16)
                btn_tekrar.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
                btn_tekrar.bind(on_press=lambda x: self.oyun_sifirla_ve_paneli_kapat())
                self.pnl_gameover.add_widget(btn_tekrar)

                btn_cikis = Button(
                    text="Oyundan\nÇık", font_size='18sp', bold=True, size_hint=(0.35, 0.16),
                    pos_hint={'center_x': 0.68, 'center_y': 0.25},
                    halign='center', valign='middle'
                )
                self.yuvarlak_buton_yap(btn_cikis, (192/255.0, 57/255.0, 43/255.0, 1), yaricap=16)
                btn_cikis.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
                btn_cikis.bind(on_press=lambda x: App.get_running_app().stop())
                self.pnl_gameover.add_widget(btn_cikis)

            self.lbl_ozet.text = f"Tebrikler! Toplamda {self.oyun_ekrani.toplam_tebrik_sayisi} Tur Başarıyla Tamamlandı.\nAvlanma süresi dolduğu için simülasyon sonlandırıldı."

            if self.pnl_gameover not in self.root.children:
                self.root.add_widget(self.pnl_gameover)

    def oyun_sifirla_ve_paneli_kapat(self):
        self.oyun_ekrani.oyunu_sifirla()
        if hasattr(self, 'pnl_gameover') and self.pnl_gameover in self.root.children:
            self.root.remove_widget(self.pnl_gameover)

    def ayarlar_tetikle(self, instance):
        self.oyun_ekrani.son_ayar_zamani = time.time()
        self.oyun_ekrani.ui_panel_acik = not self.oyun_ekrani.ui_panel_acik

if __name__ == '__main__':
    OrumcekOyunApp().run()
