#Pydroid run kivy
# -*- coding: utf-8 -*-
import os
import sys
import random
import math

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Triangle, Line
from kivy.config import Config

Config.set('graphics', 'resizable', '1')
Config.set('graphics', 'max_fps', '60')
Window.clearcolor = (0.06, 0.09, 0.16, 1)

try:
    from jnius import autoclass
    from android.runnable import run_on_ui_thread
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')
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

    @run_on_ui_thread
    def set_keep_screen_on(keep_on):
        window = activity.getWindow()
        if keep_on:
            window.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
        else:
            window.clearFlags(WindowManager.FLAG_KEEP_SCREEN_ON)

    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False

class GameCanvas(Widget):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref

class KorsanMacerasiApp(App):
    def build(self):
        self.title = "Korsan Macerası"
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.WIDTH = Window.width if Window.width > 100 else 1080
        self.HEIGHT = Window.height if Window.height > 100 else 1920

        # Sabitler ve Varsayılan Ayarlar
        self.BOYUT = 110
        self.ADA_BOYUT = 135
        self.BUYUK_ADA_BOYUT = 250
        self.BASLANGIC_HIZI = 4.0
        self.MAX_CAN = 3

        self.ayar_hedef_skor = 100
        self.ayar_hizlanma_adimi = 10
        self.ayar_dusman_sayisi = 3
        self.ayar_ada_sayisi = 4
        self.ayar_ekran_uyanik = True

        self.game_state = "MENU"  # "MENU", "SETTINGS", "PLAYING"

        # Görselleri Yükle
        self.tex_playerR = self._load_tex("images/pirateR.png")
        self.tex_playerL = self._load_tex("images/pirateL.png")
        self.tex_playerU = self._load_tex("images/pirateU.png")
        self.tex_playerD = self._load_tex("images/PirateD.png")
        self.tex_player = self.tex_playerR

        self.tex_treasure = self._load_tex("images/treasure.png")
        self.tex_island = self._load_tex("images/island.png")
        self.tex_big_island = self._load_tex("images/bigland.png")
        self.tex_kraken = self._load_tex("images/kraken.png")
        self.tex_bg = self._load_tex("images/backgr.png")

        # Oyun Değişkenleri
        self.playerX = self.WIDTH / 2.0
        self.playerY = self.HEIGHT / 2.0
        self.islands = []  # (x, y, w, h, buyuk_mu)
        self.treasureX = 0.0
        self.treasureY = 0.0

        self.heart_active = False
        self.heartX = 0.0
        self.heartY = 0.0
        self.heart_spawn_timer = 0

        self.enemies = []  # [{"x":, "y":, "vx":, "vy":}]
        self.score_value = 0
        self.canlar = self.MAX_CAN
        self.koruma_suresi = 0
        self.level_banner_timer = 0
        self.current_level = 1
        self.is_game_over = False
        self.is_game_won = False

        # Dokunma ve Kumanda Değişkenleri
        self.touch_active = False
        self.touch_pos = (0, 0)
        self.key_vx = 0.0
        self.key_vy = 0.0
        self.focus_items = []
        self.focus_index = 0

        # Katmanlar
        self.root_layout = FloatLayout()
        self.game_canvas = GameCanvas(self, size_hint=(1, 1))
        self.ui_layer = FloatLayout()
        self.hud_layer = FloatLayout()

        self.root_layout.add_widget(self.game_canvas)
        self.root_layout.add_widget(self.hud_layer)
        self.root_layout.add_widget(self.ui_layer)

        # Dokunma Bağlantıları
        self.game_canvas.bind(
            on_touch_down=self.on_game_touch_down,
            on_touch_move=self.on_game_touch_move,
            on_touch_up=self.on_game_touch_up
        )

        # Pencere ve Tuş Bağlantıları
        Window.bind(on_resize=self.on_window_resize)
        Window.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

        if ANDROID_AVAILABLE:
            try:
                force_fullscreen()
                set_keep_screen_on(self.ayar_ekran_uyanik)
            except Exception:
                pass

        self.build_hud()
        self.rebuild_ui()
        Clock.schedule_interval(self.update, 1.0 / 60.0)
        return self.root_layout

    def _load_tex(self, rel_path):
        full_path = os.path.join(self.base_dir, rel_path)
        if not os.path.exists(full_path):
            # Büyük/küçük harf duyarsız yedek arama (Linux/Android için)
            folder = os.path.dirname(full_path)
            fname = os.path.basename(full_path).lower()
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    if f.lower() == fname:
                        full_path = os.path.join(folder, f)
                        break
        if os.path.exists(full_path):
            return CoreImage(full_path).texture
        return None

    def on_window_resize(self, window, width, height):
        self.WIDTH = width if width > 100 else 1080
        self.HEIGHT = height if height > 100 else 1920
        self.build_hud()
        self.rebuild_ui()

    # --- ÇARPIŞMA VE KONUM YARDIMCILARI ---
    def _rects_collide(self, r1, r2, shrink=0):
        x1, y1, w1, h1 = r1[0] + shrink, r1[1] + shrink, r1[2] - shrink * 2, r1[3] - shrink * 2
        x2, y2, w2, h2 = r2[0] + shrink, r2[1] + shrink, r2[2] - shrink * 2, r2[3] - shrink * 2
        return (x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2)

    def adalari_olustur(self, seviye):
        yeni_adalar = []
        merkez_rect = ((self.WIDTH / 2) - 170, (self.HEIGHT / 2) - 170, 340, 340)
        # Kivy'de Y=0 ekranın altıdır; HUD üstte (HEIGHT - 145 ile HEIGHT arası) yer alır
        ust_hud_rect = (0, self.HEIGHT - 145, self.WIDTH, 145)

        if seviye == 2:
            for _ in range(200):
                bx = random.randint(50, max(51, int(self.WIDTH - self.BUYUK_ADA_BOYUT - 50)))
                by = random.randint(50, max(51, int(self.HEIGHT - self.BUYUK_ADA_BOYUT - 155)))
                b_rect = (bx, by, self.BUYUK_ADA_BOYUT, self.BUYUK_ADA_BOYUT)
                if not self._rects_collide(b_rect, merkez_rect) and not self._rects_collide(b_rect, ust_hud_rect):
                    yeni_adalar.append((bx, by, self.BUYUK_ADA_BOYUT, self.BUYUK_ADA_BOYUT, True))
                    break

        kucuk_hedef = max(0, self.ayar_ada_sayisi - 1) if seviye == 2 else self.ayar_ada_sayisi
        deneme = 0
        eklenen_kucuk = 0
        while eklenen_kucuk < kucuk_hedef and deneme < 250:
            deneme += 1
            ax = random.randint(40, max(41, int(self.WIDTH - self.ADA_BOYUT - 40)))
            ay = random.randint(40, max(41, int(self.HEIGHT - self.ADA_BOYUT - 155)))
            aday_rect = (ax, ay, self.ADA_BOYUT, self.ADA_BOYUT)

            if self._rects_collide(aday_rect, merkez_rect) or self._rects_collide(aday_rect, ust_hud_rect):
                continue

            cakisma = False
            for mx, my, mw, mh, _ in yeni_adalar:
                if self._rects_collide((ax - 38, ay - 38, self.ADA_BOYUT + 76, self.ADA_BOYUT + 76), (mx, my, mw, mh)):
                    cakisma = True
                    break
            if cakisma:
                continue

            yeni_adalar.append((ax, ay, self.ADA_BOYUT, self.ADA_BOYUT, False))
            eklenen_kucuk += 1

        return yeni_adalar

    def bos_konum_bul(self, mevcut_adalar, boy=110, p_x=None, p_y=None):
        oyuncu_alan = (p_x - 150, p_y - 150, self.BOYUT + 300, self.BOYUT + 300) if p_x is not None else None
        for _ in range(200):
            rx = random.randint(15, max(16, int(self.WIDTH - boy - 15)))
            ry = random.randint(15, max(16, int(self.HEIGHT - boy - 140)))
            test_rect = (rx, ry, boy, boy)

            if any(self._rects_collide(test_rect, (ax - 8, ay - 8, aw + 16, ah + 16)) for ax, ay, aw, ah, _ in mevcut_adalar):
                continue
            if oyuncu_alan and self._rects_collide(test_rect, oyuncu_alan):
                continue
            return float(rx), float(ry)
        return 40.0, 40.0

    def kraken_ekle(self, hiz=4.0):
        ex, ey = self.bos_konum_bul(self.islands, self.BOYUT, self.playerX, self.playerY)
        self.enemies.append({
            "x": ex,
            "y": ey,
            "vx": random.choice([-hiz, hiz]),
            "vy": random.choice([-hiz, hiz])
        })

    # --- OYUN AKIŞ KONTROLLERİ ---
    def reset_game(self):
        self.score_value = 0
        self.canlar = self.MAX_CAN
        self.koruma_suresi = 90
        self.level_banner_timer = 0
        self.current_level = 1
        self.heart_active = False
        self.heart_spawn_timer = 0
        self.is_game_over = False
        self.is_game_won = False
        self.touch_active = False

        self.playerX = self.WIDTH / 2.0
        self.playerY = self.HEIGHT / 2.0
        self.tex_player = self.tex_playerR

        self.islands = self.adalari_olustur(1)
        self.treasureX, self.treasureY = self.bos_konum_bul(self.islands, self.BOYUT)

        self.enemies.clear()
        for _ in range(self.ayar_dusman_sayisi):
            self.kraken_ekle(self.BASLANGIC_HIZI)

    def seviye_2_baslat(self):
        self.current_level = 2
        self.level_banner_timer = 120
        self.koruma_suresi = 90
        self.heart_active = False
        self.playerX = self.WIDTH / 2.0
        self.playerY = self.HEIGHT / 2.0
        self.tex_player = self.tex_playerR

        self.islands = self.adalari_olustur(2)
        self.treasureX, self.treasureY = self.bos_konum_bul(self.islands, self.BOYUT)

        self.enemies.clear()
        for _ in range(self.ayar_dusman_sayisi + 1):
            self.kraken_ekle(self.BASLANGIC_HIZI)

    # --- ARAYÜZ VE BUTON OLUŞTURMA ---
    def _create_styled_button(self, text, bg_color, pos_hint, size_hint, callback, font_size='18sp'):
        btn = Button(
            text=text,
            pos_hint=pos_hint,
            size_hint=size_hint,
            font_size=font_size,
            bold=True,
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1)
        )
        with btn.canvas.before:
            Color(*bg_color)
            btn.bg_rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[16])
            Color(1, 1, 1, 0.85)
            btn.border_line = Line(rounded_rectangle=(btn.x, btn.y, btn.width, btn.height, 16), width=1.5)

        def _upd(inst, val):
            inst.bg_rect.pos = inst.pos
            inst.bg_rect.size = inst.size
            inst.border_line.rounded_rectangle = (inst.x, inst.y, inst.width, inst.height, 16)

        btn.bind(pos=_upd, size=_upd)
        btn.bind(on_press=callback)
        return btn

    def build_hud(self):
        self.hud_layer.clear_widgets()
        self.hud_score_lbl = Label(
            text=f"Seviye {self.current_level} | Skor: {self.score_value} / {self.ayar_hedef_skor}",
            size_hint=(0.52, 0.065),
            pos_hint={'x': 0.03, 'top': 0.98},
            font_size='17sp',
            bold=True,
            color=(1, 1, 1, 1)
        )
        with self.hud_score_lbl.canvas.before:
            Color(0.06, 0.09, 0.16, 0.8)
            self.hud_score_lbl.bg = RoundedRectangle(pos=self.hud_score_lbl.pos, size=self.hud_score_lbl.size, radius=[14])
            Color(1.0, 0.84, 0.0, 1.0)
            self.hud_score_lbl.bd = Line(rounded_rectangle=(self.hud_score_lbl.x, self.hud_score_lbl.y, self.hud_score_lbl.width, self.hud_score_lbl.height, 14), width=1.8)

        def _upd_hud(inst, val):
            inst.bg.pos = inst.pos
            inst.bg.size = inst.size
            inst.bd.rounded_rectangle = (inst.x, inst.y, inst.width, inst.height, 14)

        self.hud_score_lbl.bind(pos=_upd_hud, size=_upd_hud)
        self.hud_layer.add_widget(self.hud_score_lbl)

        # Sağ Üst Can Kutusu
        self.hud_life_box = Widget(size_hint=(0.26, 0.065), pos_hint={'right': 0.97, 'top': 0.98})
        self.hud_layer.add_widget(self.hud_life_box)

        # Seviye 2 Banner Etiketi
        self.banner_lbl = Label(
            text="SEVİYE 2! Büyük Ada!",
            size_hint=(0.75, 0.08),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            font_size='24sp',
            bold=True,
            color=(1, 1, 1, 1),
            opacity=0
        )
        with self.banner_lbl.canvas.before:
            Color(0.15, 0.68, 0.37, 0.92)
            self.banner_lbl.bg = RoundedRectangle(pos=self.banner_lbl.pos, size=self.banner_lbl.size, radius=[18])
            Color(1, 1, 1, 1)
            self.banner_lbl.bd = Line(rounded_rectangle=(self.banner_lbl.x, self.banner_lbl.y, self.banner_lbl.width, self.banner_lbl.height, 18), width=2)

        def _upd_ban(inst, val):
            inst.bg.pos = inst.pos
            inst.bg.size = inst.size
            inst.bd.rounded_rectangle = (inst.x, inst.y, inst.width, inst.height, 18)

        self.banner_lbl.bind(pos=_upd_ban, size=_upd_ban)
        self.hud_layer.add_widget(self.banner_lbl)

    def _draw_heart_shapes(self, canvas_obj, x, y, size, color_rgba):
        with canvas_obj:
            Color(*color_rgba)
            r = size / 4.0
            Ellipse(pos=(x, y + size - 2 * r), size=(2 * r, 2 * r))
            Ellipse(pos=(x + 2 * r, y + size - 2 * r), size=(2 * r, 2 * r))
            Triangle(points=[x, y + size - r, x + size, y + size - r, x + size / 2.0, y])

    def update_hud_visuals(self):
        if self.game_state != "PLAYING":
            self.hud_layer.opacity = 0
            return
        self.hud_layer.opacity = 1
        self.hud_score_lbl.text = f"Seviye {self.current_level} | Skor: {self.score_value} / {self.ayar_hedef_skor}"

        # Sağ Üst Can Kutusu Çizimi
        self.hud_life_box.canvas.clear()
        bx, by, bw, bh = self.hud_life_box.x, self.hud_life_box.y, self.hud_life_box.width, self.hud_life_box.height
        with self.hud_life_box.canvas:
            Color(0.06, 0.09, 0.16, 0.8)
            RoundedRectangle(pos=(bx, by), size=(bw, bh), radius=[14])
            Color(0.9, 0.3, 0.23, 1.0)
            Line(rounded_rectangle=(bx, by, bw, bh, 14), width=1.8)

        h_size = min(32, bh * 0.58)
        spacing = 10
        total_w = self.MAX_CAN * h_size + (self.MAX_CAN - 1) * spacing
        start_x = bx + (bw - total_w) / 2.0
        start_y = by + (bh - h_size) / 2.0
        for c in range(self.MAX_CAN):
            col = (0.9, 0.3, 0.23, 1) if c < self.canlar else (0.35, 0.39, 0.45, 1)
            self._draw_heart_shapes(self.hud_life_box.canvas, start_x + c * (h_size + spacing), start_y, h_size, col)

        self.banner_lbl.opacity = 1 if self.level_banner_timer > 0 else 0

    def rebuild_ui(self):
        # 1. Mevcut katmandaki TÜM çocukların çizimlerini tek tek zorla temizle ve ekran dışına al
        if getattr(self, 'ui_layer', None):
            for child in list(self.ui_layer.children):
                child.canvas.before.clear()
                child.canvas.clear()
                child.canvas.after.clear()
                child.opacity = 0
                child.pos = (-9999, -9999)
            self.ui_layer.clear_widgets()
            self.ui_layer.canvas.before.clear()
            self.ui_layer.canvas.clear()
            self.ui_layer.canvas.after.clear()
            if self.ui_layer.parent:
                self.root_layout.remove_widget(self.ui_layer)

        self.focus_items = []
        self.focus_index = 0

        # Oyun aktif oynanıyorsa yeni bir arayüz katmanı oluşturma
        if self.game_state == "PLAYING" and not self.is_game_over and not self.is_game_won:
            self.ui_layer = FloatLayout()
            return

        # Menü, Ayarlar veya Oyun Sonu için sıfırdan tertemiz katman oluştur
        self.ui_layer = FloatLayout(size_hint=(1, 1))
        self.root_layout.add_widget(self.ui_layer)

        if self.game_state == "MENU":
            panel = FloatLayout(size_hint=(0.72, 0.52), pos_hint={'center_x': 0.5, 'center_y': 0.5})
            with panel.canvas:
                Color(0, 0, 0, 0.45)
                panel.dim = Rectangle(pos=(0, 0), size=(self.WIDTH, self.HEIGHT))
                Color(0.06, 0.09, 0.16, 0.92)
                panel.bg = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[26])
                Color(1.0, 0.84, 0.0, 1.0)
                panel.bd = Line(rounded_rectangle=(panel.x, panel.y, panel.width, panel.height, 26), width=2.2)

            def _upd_p(inst, val):
                panel.dim.size = (self.WIDTH, self.HEIGHT)
                inst.bg.pos = inst.pos
                inst.bg.size = inst.size
                inst.bd.rounded_rectangle = (inst.x, inst.y, inst.width, inst.height, 26)

            panel.bind(pos=_upd_p, size=_upd_p)
            self.ui_layer.add_widget(panel)

            title = Label(
                text="KORSAN MACERASI",
                size_hint=(0.7, 0.08),
                pos_hint={'center_x': 0.5, 'center_y': 0.68},
                font_size='26sp',
                bold=True,
                color=(1.0, 0.84, 0.0, 1.0)
            )
            self.ui_layer.add_widget(title)

            btn_start = self._create_styled_button("Başla", (0.15, 0.68, 0.37, 1), {'center_x': 0.5, 'center_y': 0.55}, (0.48, 0.075), self._start_clicked)
            btn_settings = self._create_styled_button("Ayarlar", (0.16, 0.50, 0.72, 1), {'center_x': 0.5, 'center_y': 0.44}, (0.48, 0.075), self._open_settings)
            btn_exit = self._create_styled_button("Çıkış", (0.75, 0.22, 0.17, 1), {'center_x': 0.5, 'center_y': 0.33}, (0.48, 0.075), lambda x: sys.exit())

            self.ui_layer.add_widget(btn_start)
            self.ui_layer.add_widget(btn_settings)
            self.ui_layer.add_widget(btn_exit)
            self.focus_items = [btn_start, btn_settings, btn_exit]

        elif self.game_state == "SETTINGS":
            panel = FloatLayout(size_hint=(0.88, 0.72), pos_hint={'center_x': 0.5, 'center_y': 0.5})
            with panel.canvas:
                Color(0, 0, 0, 0.5)
                panel.dim = Rectangle(pos=(0, 0), size=(self.WIDTH, self.HEIGHT))
                Color(0.06, 0.09, 0.16, 0.94)
                panel.bg = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[26])
                Color(0.20, 0.60, 0.86, 1.0)
                panel.bd = Line(rounded_rectangle=(panel.x, panel.y, panel.width, panel.height, 26), width=2.2)

            def _upd_sp(inst, val):
                panel.dim.size = (self.WIDTH, self.HEIGHT)
                inst.bg.pos = inst.pos
                inst.bg.size = inst.size
                inst.bd.rounded_rectangle = (inst.x, inst.y, inst.width, inst.height, 26)

            panel.bind(pos=_upd_sp, size=_upd_sp)
            self.ui_layer.add_widget(panel)

            title = Label(
                text="OYUN AYARLARI",
                size_hint=(0.8, 0.07),
                pos_hint={'center_x': 0.5, 'center_y': 0.80},
                font_size='24sp',
                bold=True,
                color=(1, 1, 1, 1)
            )
            self.ui_layer.add_widget(title)

            satirlar = [
                ("hedef", "Hedef Skor", self.ayar_hedef_skor, 20, 300, 10, 0.70),
                ("hizlanma", "Hızlanma Adımı", self.ayar_hizlanma_adimi, 5, 50, 5, 0.61),
                ("dusman", "Başlangıç Kraken", self.ayar_dusman_sayisi, 1, 10, 1, 0.52),
                ("ada", "Küçük Ada Sayısı", self.ayar_ada_sayisi, 0, 8, 1, 0.43),
            ]

            for sid, etiket, deger, mn, mx, adim, ypos in satirlar:
                row_lbl = Label(
                    text=f"{etiket}: [color=ffd700][b]{deger}[/b][/color]",
                    markup=True,
                    size_hint=(0.54, 0.065),
                    pos_hint={'x': 0.10, 'center_y': ypos},
                    font_size='16sp'
                )
                with row_lbl.canvas.before:
                    Color(0.12, 0.16, 0.23, 0.9)
                    row_lbl.bg = RoundedRectangle(pos=row_lbl.pos, size=row_lbl.size, radius=[12])
                row_lbl.bind(
                    pos=lambda i, v: setattr(i.bg, 'pos', i.pos),
                    size=lambda i, v: setattr(i.bg, 'size', i.size)
                )

                btn_m = self._create_styled_button(
                    "-", (0.75, 0.22, 0.17, 1),
                    {'x': 0.67, 'center_y': ypos}, (0.10, 0.065),
                    lambda x, s=sid, a=-adim, lo=mn, hi=mx: self._change_setting(s, a, lo, hi)
                )
                btn_p = self._create_styled_button(
                    "+", (0.15, 0.68, 0.37, 1),
                    {'x': 0.79, 'center_y': ypos}, (0.10, 0.065),
                    lambda x, s=sid, a=adim, lo=mn, hi=mx: self._change_setting(s, a, lo, hi)
                )

                self.ui_layer.add_widget(row_lbl)
                self.ui_layer.add_widget(btn_m)
                self.ui_layer.add_widget(btn_p)
                self.focus_items.append({"left": btn_m, "right": btn_p, "ok": btn_p})

            awake_durum = "[color=2ecc71][b]AÇIK[/b][/color]" if self.ayar_ekran_uyanik else "[color=e74c3c][b]KAPALI[/b][/color]"
            awake_lbl = Label(
                text=f"Ekranı Uyanık Tut: {awake_durum}",
                markup=True,
                size_hint=(0.54, 0.065),
                pos_hint={'x': 0.10, 'center_y': 0.34},
                font_size='16sp'
            )
            with awake_lbl.canvas.before:
                Color(0.12, 0.16, 0.23, 0.9)
                awake_lbl.bg = RoundedRectangle(pos=awake_lbl.pos, size=awake_lbl.size, radius=[12])
            awake_lbl.bind(
                pos=lambda i, v: setattr(i.bg, 'pos', i.pos),
                size=lambda i, v: setattr(i.bg, 'size', i.size)
            )

            btn_aw_l = self._create_styled_button(
                "<", (0.16, 0.50, 0.72, 1),
                {'x': 0.67, 'center_y': 0.34}, (0.10, 0.065),
                lambda x: self._toggle_screen_awake()
            )
            btn_aw_r = self._create_styled_button(
                ">", (0.16, 0.50, 0.72, 1),
                {'x': 0.79, 'center_y': 0.34}, (0.10, 0.065),
                lambda x: self._toggle_screen_awake()
            )

            self.ui_layer.add_widget(awake_lbl)
            self.ui_layer.add_widget(btn_aw_l)
            self.ui_layer.add_widget(btn_aw_r)
            self.focus_items.append({"left": btn_aw_l, "right": btn_aw_r, "ok": btn_aw_r})

            btn_save = self._create_styled_button(
                "Kaydet ve Dön", (0.15, 0.68, 0.37, 1),
                {'center_x': 0.5, 'center_y': 0.21}, (0.50, 0.07),
                self._back_to_menu
            )
            self.ui_layer.add_widget(btn_save)
            self.focus_items.append(btn_save)

        elif self.game_state == "PLAYING" and (self.is_game_over or self.is_game_won):
            baslik = "Tebrikler! Oyunu Kazandınız!" if self.is_game_won else "Oyun Bitti!"
            renk = (0.15, 0.68, 0.37, 1) if self.is_game_won else (0.75, 0.22, 0.17, 1)

            panel = FloatLayout(size_hint=(0.86, 0.35), pos_hint={'center_x': 0.5, 'center_y': 0.5})
            with panel.canvas:
                Color(0, 0, 0, 0.55)
                panel.dim = Rectangle(pos=(0, 0), size=(self.WIDTH, self.HEIGHT))
                Color(0.08, 0.10, 0.14, 0.94)
                panel.bg = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[24])
                Color(*renk)
                panel.bd = Line(rounded_rectangle=(panel.x, panel.y, panel.width, panel.height, 24), width=2.5)

            def _upd_end(inst, val):
                panel.dim.size = (self.WIDTH, self.HEIGHT)
                inst.bg.pos = inst.pos
                inst.bg.size = inst.size
                inst.bd.rounded_rectangle = (inst.x, inst.y, inst.width, inst.height, 24)

            panel.bind(pos=_upd_end, size=_upd_end)
            self.ui_layer.add_widget(panel)

            end_lbl = Label(
                text=baslik,
                size_hint=(0.8, 0.08),
                pos_hint={'center_x': 0.5, 'center_y': 0.58},
                font_size='22sp',
                bold=True,
                color=(1, 1, 1, 1)
            )
            self.ui_layer.add_widget(end_lbl)

            btn_rep = self._create_styled_button(
                "Tekrar Oyna", (0.15, 0.68, 0.37, 1),
                {'x': 0.10, 'center_y': 0.43}, (0.25, 0.07),
                self._replay_clicked, font_size='15sp'
            )
            btn_mnu = self._create_styled_button(
                "Ana Menü", (0.16, 0.50, 0.72, 1),
                {'x': 0.375, 'center_y': 0.43}, (0.25, 0.07),
                self._back_to_menu, font_size='15sp'
            )
            btn_ext = self._create_styled_button(
                "Çıkış", (0.75, 0.22, 0.17, 1),
                {'x': 0.65, 'center_y': 0.43}, (0.25, 0.07),
                lambda x: sys.exit(), font_size='15sp'
            )

            self.ui_layer.add_widget(btn_rep)
            self.ui_layer.add_widget(btn_mnu)
            self.ui_layer.add_widget(btn_ext)
            self.focus_items = [btn_rep, btn_mnu, btn_ext]

    def _start_clicked(self, inst):
        self.reset_game()
        self.game_state = "PLAYING"
        Clock.schedule_once(lambda dt: self.rebuild_ui(), 0)

    def _replay_clicked(self, inst):
        self.enemies.clear()
        self.is_game_over = False
        self.is_game_won = False
        self.koruma_suresi = 90
        self.reset_game()
        self.rebuild_ui()

    def _open_settings(self, inst):
        self.game_state = "SETTINGS"
        Clock.schedule_once(lambda dt: self.rebuild_ui(), 0)

    def _back_to_menu(self, inst):
        self.enemies.clear()
        self.islands.clear()
        self.heart_active = False
        self.is_game_over = False
        self.is_game_won = False
        self.touch_active = False
        self.game_state = "MENU"
        self.rebuild_ui()

    def _change_setting(self, sid, delta, lo, hi):
        if sid == "hedef":
            self.ayar_hedef_skor = max(lo, min(hi, self.ayar_hedef_skor + delta))
        elif sid == "hizlanma":
            self.ayar_hizlanma_adimi = max(lo, min(hi, self.ayar_hizlanma_adimi + delta))
        elif sid == "dusman":
            self.ayar_dusman_sayisi = max(lo, min(hi, self.ayar_dusman_sayisi + delta))
        elif sid == "ada":
            self.ayar_ada_sayisi = max(lo, min(hi, self.ayar_ada_sayisi + delta))
        self.rebuild_ui()

    def _toggle_screen_awake(self):
        self.ayar_ekran_uyanik = not self.ayar_ekran_uyanik
        if ANDROID_AVAILABLE:
            try:
                set_keep_screen_on(self.ayar_ekran_uyanik)
            except Exception:
                pass
        self.rebuild_ui()

    # --- DOKUNMA VE KUMANDA GİRİŞLERİ ---
    def on_game_touch_down(self, widget, touch):
        if self.game_state == "PLAYING" and not self.is_game_over and not self.is_game_won:
            self.touch_active = True
            self.touch_pos = touch.pos
            return True
        return False

    def on_game_touch_move(self, widget, touch):
        if self.touch_active:
            self.touch_pos = touch.pos
            return True
        return False

    def on_game_touch_up(self, widget, touch):
        self.touch_active = False
        return False

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        KEY_UP = (273, 19)
        KEY_DOWN = (274, 20)
        KEY_LEFT = (276, 21)
        KEY_RIGHT = (275, 22)
        KEY_OK = (13, 32, 23, 66)
        KEY_BACK = (27, 4)

        if key in KEY_BACK and self.game_state != "MENU":
            self._back_to_menu(None)
            return True

        if self.game_state == "PLAYING" and not self.is_game_over and not self.is_game_won:
            spd = 8.0
            if key in KEY_UP:
                self.key_vy = spd
                self.tex_player = self.tex_playerU
            elif key in KEY_DOWN:
                self.key_vy = -spd
                self.tex_player = self.tex_playerD
            elif key in KEY_LEFT:
                self.key_vx = -spd
                self.tex_player = self.tex_playerL
            elif key in KEY_RIGHT:
                self.key_vx = spd
                self.tex_player = self.tex_playerR
            return True

        if self.focus_items:
            self.focus_index = self.focus_index % len(self.focus_items)
            item = self.focus_items[self.focus_index]
            if key in KEY_UP:
                self.focus_index = (self.focus_index - 1) % len(self.focus_items)
            elif key in KEY_DOWN:
                self.focus_index = (self.focus_index + 1) % len(self.focus_items)
            elif key in KEY_LEFT and isinstance(item, dict):
                item["left"].trigger_action(duration=0.05)
            elif key in KEY_RIGHT and isinstance(item, dict):
                item["right"].trigger_action(duration=0.05)
            elif key in KEY_OK:
                target = item["ok"] if isinstance(item, dict) else item
                target.trigger_action(duration=0.05)
            return True
        return False

    def on_key_up(self, window, key, scancode):
        if key in (273, 19, 274, 20):
            self.key_vy = 0.0
        elif key in (276, 21, 275, 22):
            self.key_vx = 0.0
        return False

    # --- ANA OYUN DÖNGÜSÜ ---
    def update(self, dt):
        self.game_canvas.canvas.clear()

        with self.game_canvas.canvas:
            # 1. Arka Plan
            Color(1, 1, 1, 1)
            if self.tex_bg:
                Rectangle(pos=(0, 0), size=(self.WIDTH, self.HEIGHT), texture=self.tex_bg)
            else:
                Color(0.08, 0.28, 0.45, 1)
                Rectangle(pos=(0, 0), size=(self.WIDTH, self.HEIGHT))

            if self.game_state == "PLAYING":
                # 2. Adaları Çiz
                Color(1, 1, 1, 1)
                for ax, ay, aw, ah, buyuk_mu in self.islands:
                    tex = self.tex_big_island if buyuk_mu else self.tex_island
                    if tex:
                        Rectangle(pos=(ax, ay), size=(aw, ah), texture=tex)

                if not self.is_game_over and not self.is_game_won:
                    if self.koruma_suresi > 0:
                        self.koruma_suresi -= 1

                    # Bonus Kalp Oluşturma
                    if self.canlar < self.MAX_CAN and not self.heart_active:
                        self.heart_spawn_timer += 1
                        if self.heart_spawn_timer >= 240:
                            self.heartX, self.heartY = self.bos_konum_bul(self.islands, 75, self.playerX, self.playerY)
                            self.heart_active = True
                            self.heart_spawn_timer = 0

                    # Bonus Kalp Çizimi ve Toplama
                    if self.heart_active:
                        Color(1, 1, 1, 0.75)
                        Ellipse(pos=(self.heartX, self.heartY), size=(75, 75))
                        Color(0.9, 0.3, 0.23, 1)
                        Line(ellipse=(self.heartX, self.heartY, 75, 75), width=2.5)
                        self._draw_heart_shapes(
                            self.game_canvas.canvas,
                            self.heartX + 15, self.heartY + 13, 45,
                            (0.9, 0.3, 0.23, 1)
                        )

                        dist_h = math.hypot(
                            (self.playerX + self.BOYUT / 2) - (self.heartX + 37.5),
                            (self.playerY + self.BOYUT / 2) - (self.heartY + 37.5)
                        )
                        if dist_h < self.BOYUT * 0.7:
                            self.canlar = min(self.MAX_CAN, self.canlar + 1)
                            self.heart_active = False

                    # Oyuncu Hareketi (Dokunma veya Tuş)
                    hedefX, hedefY = self.playerX, self.playerY
                    moved = False

                    if self.touch_active:
                        tx, ty = self.touch_pos
                        dx = tx - (self.playerX + self.BOYUT / 2)
                        dy = ty - (self.playerY + self.BOYUT / 2)
                        if abs(dx) > 5 or abs(dy) > 5:
                            if abs(dx) >= abs(dy):
                                self.tex_player = self.tex_playerR if dx > 0 else self.tex_playerL
                            else:
                                # Kivy'de dy > 0 yukarı demektir
                                self.tex_player = self.tex_playerU if dy > 0 else self.tex_playerD
                        hedefX = max(0, min(tx - (self.BOYUT / 2), self.WIDTH - self.BOYUT))
                        hedefY = max(0, min(ty - (self.BOYUT / 2), self.HEIGHT - self.BOYUT))
                        moved = True
                    elif self.key_vx != 0 or self.key_vy != 0:
                        hedefX = max(0, min(self.playerX + self.key_vx, self.WIDTH - self.BOYUT))
                        hedefY = max(0, min(self.playerY + self.key_vy, self.HEIGHT - self.BOYUT))
                        moved = True

                    if moved:
                        test_x = (hedefX, self.playerY, self.BOYUT, self.BOYUT)
                        if not any(self._rects_collide(test_x, (ax, ay, aw, ah), shrink=28) for ax, ay, aw, ah, _ in self.islands):
                            self.playerX = hedefX

                        test_y = (self.playerX, hedefY, self.BOYUT, self.BOYUT)
                        if not any(self._rects_collide(test_y, (ax, ay, aw, ah), shrink=28) for ax, ay, aw, ah, _ in self.islands):
                            self.playerY = hedefY

                    # Hazine Çizimi
                    Color(1, 1, 1, 1)
                    if self.tex_treasure:
                        Rectangle(pos=(self.treasureX, self.treasureY), size=(self.BOYUT, self.BOYUT), texture=self.tex_treasure)

                    # Oyuncu Çizimi (Koruma Yanıp Sönmesi Dahil)
                    if self.koruma_suresi == 0 or (self.koruma_suresi // 6) % 2 == 0:
                        Color(1, 1, 1, 1)
                        if self.tex_player:
                            Rectangle(pos=(self.playerX, self.playerY), size=(self.BOYUT, self.BOYUT), texture=self.tex_player)

                    # Kraken Hareketi ve Çarpışma
                    for en in self.enemies:
                        eski_x = en["x"]
                        en["x"] += en["vx"]
                        if en["x"] >= self.WIDTH - self.BOYUT or en["x"] <= 0 or any(
                            self._rects_collide((en["x"], en["y"], self.BOYUT, self.BOYUT), (ax, ay, aw, ah), shrink=26)
                            for ax, ay, aw, ah, _ in self.islands
                        ):
                            en["x"] = eski_x
                            en["vx"] = -en["vx"]

                        eski_y = en["y"]
                        en["y"] += en["vy"]
                        if en["y"] >= self.HEIGHT - self.BOYUT or en["y"] <= 0 or any(
                            self._rects_collide((en["x"], en["y"], self.BOYUT, self.BOYUT), (ax, ay, aw, ah), shrink=26)
                            for ax, ay, aw, ah, _ in self.islands
                        ):
                            en["y"] = eski_y
                            en["vy"] = -en["vy"]

                        Color(1, 1, 1, 1)
                        if self.tex_kraken:
                            Rectangle(pos=(en["x"], en["y"]), size=(self.BOYUT, self.BOYUT), texture=self.tex_kraken)

                        dist_en = math.hypot(self.playerX - en["x"], self.playerY - en["y"])
                        if dist_en < self.BOYUT * 0.65 and self.koruma_suresi == 0:
                            self.canlar -= 1
                            self.koruma_suresi = 90
                            if self.canlar <= 0:
                                self.is_game_over = True
                                self.rebuild_ui()
                                break

                    # Hazine Toplama ve Seviye Kontrolü
                    dist_tr = math.hypot(self.playerX - self.treasureX, self.playerY - self.treasureY)
                    if dist_tr < self.BOYUT * 0.7:
                        self.score_value += 1
                        seviye_1_gecis = max(1, self.ayar_hedef_skor // 2)

                        if self.score_value == seviye_1_gecis and self.current_level == 1:
                            self.seviye_2_baslat()
                        elif self.score_value >= self.ayar_hedef_skor:
                            self.is_game_won = True
                            self.rebuild_ui()
                        else:
                            self.treasureX, self.treasureY = self.bos_konum_bul(self.islands, self.BOYUT)
                            if self.score_value % self.ayar_hizlanma_adimi == 0:
                                for en in self.enemies:
                                    en["vx"] += 1 if en["vx"] > 0 else -1
                                    en["vy"] += 1 if en["vy"] > 0 else -1
                                seviye_ici_artis = (self.score_value - (seviye_1_gecis if self.current_level == 2 else 0)) // self.ayar_hizlanma_adimi
                                guncel_hiz = self.BASLANGIC_HIZI + max(1, seviye_ici_artis)
                                self.kraken_ekle(guncel_hiz)

                    if self.level_banner_timer > 0:
                        self.level_banner_timer -= 1

        self.update_hud_visuals()

if __name__ == '__main__':
    KorsanMacerasiApp().run()
