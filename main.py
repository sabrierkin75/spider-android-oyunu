#Pydroid run sdl2
import pygame, random, os

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except Exception:
    pass

pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()

# Sabit görsel boyutları ve temel değerler
BOYUT = 110
ADA_BOYUT = 135
BUYUK_ADA_BOYUT = 250
BASLANGIC_HIZI = 4
MAX_CAN = 3

# Kullanıcı tarafından değiştirilebilen ayarlar (Varsayılan değerler)
ayar_hedef_skor = 100
ayar_hizlanma_adimi = 10
ayar_dusman_sayisi = 3
ayar_ada_sayisi = 4

# Oyun durumu: "MENU", "SETTINGS", "PLAYING"
game_state = "MENU"

# 4 yönlü oyuncu gemisi görselleri
playerImgR = pygame.transform.scale(pygame.image.load("images/pirateR.png"), (BOYUT, BOYUT))
playerImgL = pygame.transform.scale(pygame.image.load("images/pirateL.png"), (BOYUT, BOYUT))
playerImgU = pygame.transform.scale(pygame.image.load("images/pirateU.png"), (BOYUT, BOYUT))
playerImgD = pygame.transform.scale(pygame.image.load("images/PirateD.png"), (BOYUT, BOYUT))
playerImg = playerImgR

playerX = WIDTH // 2
playerY = HEIGHT // 2

treasureImg = pygame.transform.scale(pygame.image.load("images/treasure.png"), (BOYUT, BOYUT))
islandImg = pygame.transform.scale(pygame.image.load("images/island.png"), (ADA_BOYUT, ADA_BOYUT))
bigIslandImg = pygame.transform.scale(pygame.image.load("images/bigland.png"), (BUYUK_ADA_BOYUT, BUYUK_ADA_BOYUT))
kraken_scaled = pygame.transform.scale(pygame.image.load("images/kraken.png"), (BOYUT, BOYUT))
background = pygame.transform.scale(pygame.image.load("images/backgr.png"), (WIDTH, HEIGHT))

islands = []
treasureX, treasureY = 0, 0

heart_active = False
heartX, heartY = 0, 0
heart_spawn_timer = 0

enemyImg = []
enemyX = []
enemyY = []
enemyX_change = []
enemyY_change = []
num_of_enemies = ayar_dusman_sayisi

score_value = 0
canlar = MAX_CAN
koruma_suresi = 0
level_banner_timer = 0
current_level = 1
is_game_over = False
is_game_won = False

font = pygame.font.SysFont("Arial", 40, bold=True)
small_font = pygame.font.SysFont("Arial", 34, bold=True)
big_font = pygame.font.SysFont("Arial", 56, bold=True)

# Ana Menü Butonları
menu_btn_w, menu_btn_h = 340, 82
start_btn = pygame.Rect((WIDTH // 2) - (menu_btn_w // 2), (HEIGHT // 2) - 85, menu_btn_w, menu_btn_h)
settings_btn = pygame.Rect((WIDTH // 2) - (menu_btn_w // 2), (HEIGHT // 2) + 20, menu_btn_w, menu_btn_h)
menu_exit_btn = pygame.Rect((WIDTH // 2) - (menu_btn_w // 2), (HEIGHT // 2) + 125, menu_btn_w, menu_btn_h)

# Ayarlar Ekranı Butonları
settings_back_btn = pygame.Rect((WIDTH // 2) - 180, (HEIGHT // 2) + 185, 360, 75)
ayar_satirlari = [
    {"id": "hedef", "etiket": "Hedef Skor", "min": 20, "max": 300, "adim": 10},
    {"id": "hizlanma", "etiket": "Hızlanma Adımı (Skor)", "min": 5, "max": 50, "adim": 5},
    {"id": "dusman", "etiket": "Başlangıç Kraken", "min": 1, "max": 10, "adim": 1},
    {"id": "ada", "etiket": "Küçük Ada Sayısı", "min": 0, "max": 8, "adim": 1},
]

# Oyun Sonu Butonları
end_btn_w, end_btn_h = 240, 78
replay_btn = pygame.Rect((WIDTH // 2) - end_btn_w - 130, (HEIGHT // 2) + 55, end_btn_w, end_btn_h)
to_menu_btn = pygame.Rect((WIDTH // 2) - (end_btn_w // 2), (HEIGHT // 2) + 55, end_btn_w, end_btn_h)
exit_btn = pygame.Rect((WIDTH // 2) + 130, (HEIGHT // 2) + 55, end_btn_w, end_btn_h)

def draw_rounded_box(rect, color, alpha=200, border_color=None, radius=20):
    box_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(box_surf, (*color, alpha), box_surf.get_rect(), border_radius=radius)
    if border_color:
        pygame.draw.rect(box_surf, (*border_color, 255), box_surf.get_rect(), width=3, border_radius=radius)
    screen.blit(box_surf, rect.topleft)

def draw_button(rect, text, bg_color, text_font=font):
    pygame.draw.rect(screen, bg_color, rect, border_radius=16)
    pygame.draw.rect(screen, (255, 255, 255), rect, width=2, border_radius=16)
    txt_surf = text_font.render(text, True, (255, 255, 255))
    screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))

def adalari_olustur(seviye):
    yeni_adalar = []
    merkez_rect = pygame.Rect((WIDTH // 2) - 170, (HEIGHT // 2) - 170, 340, 340)
    ust_hud_rect = pygame.Rect(0, 0, WIDTH, 145)

    if seviye == 2:
        for _ in range(200):
            bx = random.randint(50, max(51, WIDTH - BUYUK_ADA_BOYUT - 50))
            by = random.randint(155, max(156, HEIGHT - BUYUK_ADA_BOYUT - 50))
            b_rect = pygame.Rect(bx, by, BUYUK_ADA_BOYUT, BUYUK_ADA_BOYUT)
            if not b_rect.colliderect(merkez_rect) and not b_rect.colliderect(ust_hud_rect):
                yeni_adalar.append((b_rect, True))
                break

    kucuk_hedef = max(0, ayar_ada_sayisi - 1) if seviye == 2 else ayar_ada_sayisi
    deneme = 0
    eklenen_kucuk = 0
    while eklenen_kucuk < kucuk_hedef and deneme < 250:
        deneme += 1
        ax = random.randint(40, max(41, WIDTH - ADA_BOYUT - 40))
        ay = random.randint(155, max(156, HEIGHT - ADA_BOYUT - 40))
        aday_rect = pygame.Rect(ax, ay, ADA_BOYUT, ADA_BOYUT)

        if aday_rect.colliderect(merkez_rect) or aday_rect.colliderect(ust_hud_rect):
            continue
        if any(aday_rect.inflate(75, 75).colliderect(mevcut_rect) for mevcut_rect, _ in yeni_adalar):
            continue

        yeni_adalar.append((aday_rect, False))
        eklenen_kucuk += 1

    return yeni_adalar

def bos_konum_bul(mevcut_adalar, boy=BOYUT, p_x=None, p_y=None):
    oyuncu_alan = pygame.Rect(p_x - 150, p_y - 150, BOYUT + 300, BOYUT + 300) if p_x is not None else None
    for _ in range(200):
        rx = random.randint(15, max(16, WIDTH - boy - 15))
        ry = random.randint(140, max(141, HEIGHT - boy - 15))
        test_rect = pygame.Rect(rx, ry, boy, boy)
        if any(test_rect.colliderect(ada_rect.inflate(15, 15)) for ada_rect, _ in mevcut_adalar):
            continue
        if oyuncu_alan and test_rect.colliderect(oyuncu_alan):
            continue
        return rx, ry
    return 40, 145

def kraken_ekle(hiz=BASLANGIC_HIZI):
    enemyImg.append(kraken_scaled)
    ex, ey = bos_konum_bul(islands, BOYUT, playerX, playerY)
    enemyX.append(ex)
    enemyY.append(ey)
    enemyX_change.append(random.choice([-hiz, hiz]))
    enemyY_change.append(random.choice([-hiz, hiz]))

def call_treasure(image, x, y):
    screen.blit(image, (x, y))

def call_player(image, x, y, koruma_sayaci):
    if koruma_sayaci == 0 or (koruma_sayaci // 6) % 2 == 0:
        screen.blit(image, (x, y))

def enemy(x, y, i):
    screen.blit(enemyImg[i], (x, y))

def draw_heart(surface, x, y, size, color):
    r = size // 4
    pygame.draw.circle(surface, color, (x + r, y + r), r)
    pygame.draw.circle(surface, color, (x + 3 * r, y + r), r)
    points = [
        (x, y + r + 2),
        (x + size, y + r + 2),
        (x + size // 2, y + size)
    ]
    pygame.draw.polygon(surface, color, points)

def draw_bonus_heart(x, y):
    glow_rect = pygame.Rect(x, y, 75, 75)
    draw_rounded_box(glow_rect, (255, 255, 255), alpha=180, border_color=(231, 76, 60), radius=38)
    draw_heart(screen, x + 15, y + 17, 45, (231, 76, 60))

def show_hud(score_val, kalan_can, seviye):
    score_render = font.render(f"Seviye {seviye} | Skor: {score_val} / {ayar_hedef_skor}", True, (255, 255, 255))
    text_rect = score_render.get_rect(topleft=(52, 44))
    bg_rect = pygame.Rect(32, 32, text_rect.width + 40, text_rect.height + 24)
    draw_rounded_box(bg_rect, (15, 23, 42), alpha=190, border_color=(255, 215, 0), radius=16)
    screen.blit(score_render, text_rect)

    kalp_boyutu = 38
    kalp_bosluk = 14
    kutu_genislik = (MAX_CAN * kalp_boyutu) + ((MAX_CAN - 1) * kalp_bosluk) + 40
    kutu_yukseklik = bg_rect.height
    can_rect = pygame.Rect(WIDTH - kutu_genislik - 32, 32, kutu_genislik, kutu_yukseklik)
    draw_rounded_box(can_rect, (15, 23, 42), alpha=190, border_color=(231, 76, 60), radius=16)

    baslangic_x = can_rect.x + 20
    baslangic_y = can_rect.y + (kutu_yukseklik - kalp_boyutu) // 2
    for c in range(MAX_CAN):
        renk = (231, 76, 60) if c < kalan_can else (90, 100, 115)
        draw_heart(screen, baslangic_x + c * (kalp_boyutu + kalp_bosluk), baslangic_y, kalp_boyutu, renk)

def draw_menu():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(120)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    panel_rect = pygame.Rect(0, 0, 560, 480)
    panel_rect.center = (WIDTH // 2, HEIGHT // 2 + 10)
    draw_rounded_box(panel_rect, (15, 23, 42), alpha=225, border_color=(255, 215, 0), radius=28)

    title_surf = big_font.render("KORSAN MACERASI", True, (255, 215, 0))
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, (HEIGHT // 2) - 165)))

    draw_button(start_btn, "Başla", (39, 174, 96))
    draw_button(settings_btn, "Ayarlar", (41, 128, 185))
    draw_button(menu_exit_btn, "Çıkış", (192, 57, 43))

def draw_settings():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(140)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    panel_w = min(860, WIDTH - 60)
    panel_h = 560
    panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
    panel_rect.center = (WIDTH // 2, HEIGHT // 2)
    draw_rounded_box(panel_rect, (15, 23, 42), alpha=235, border_color=(52, 152, 219), radius=28)

    title_surf = big_font.render("OYUN AYARLARI", True, (255, 255, 255))
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, panel_rect.top + 55)))

    degerler = {
        "hedef": ayar_hedef_skor,
        "hizlanma": ayar_hizlanma_adimi,
        "dusman": ayar_dusman_sayisi,
        "ada": ayar_ada_sayisi,
    }

    start_y = panel_rect.top + 125
    row_h = 78

    for idx, satir in enumerate(ayar_satirlari):
        ry = start_y + idx * row_h
        row_rect = pygame.Rect(panel_rect.left + 35, ry, panel_w - 70, 64)
        draw_rounded_box(row_rect, (30, 41, 59), alpha=200, border_color=(100, 116, 139), radius=14)

        lbl_surf = small_font.render(satir["etiket"], True, (255, 255, 255))
        screen.blit(lbl_surf, lbl_surf.get_rect(midleft=(row_rect.left + 25, row_rect.centery)))

        # - ve + Butonları
        plus_rect = pygame.Rect(row_rect.right - 75, row_rect.top + 7, 55, 50)
        val_rect = pygame.Rect(row_rect.right - 175, row_rect.top + 7, 90, 50)
        minus_rect = pygame.Rect(row_rect.right - 240, row_rect.top + 7, 55, 50)

        draw_button(minus_rect, "-", (192, 57, 43), font)
        val_surf = font.render(str(degerler[satir["id"]]), True, (255, 215, 0))
        screen.blit(val_surf, val_surf.get_rect(center=val_rect.center))
        draw_button(plus_rect, "+", (39, 174, 96), font)

        satir["minus_rect"] = minus_rect
        satir["plus_rect"] = plus_rect

    draw_button(settings_back_btn, "Kaydet ve Dön", (39, 174, 96))

def end_screen(baslik, renk):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    title_text = big_font.render(baslik, True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(WIDTH // 2, (HEIGHT // 2) - 65))

    panel_w = max(title_rect.width + 100, (end_btn_w * 3) + 100)
    panel_h = 300
    panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
    panel_rect.center = (WIDTH // 2, HEIGHT // 2 + 10)
    draw_rounded_box(panel_rect, (20, 25, 35), alpha=235, border_color=renk, radius=25)

    badge_rect = title_rect.inflate(50, 26)
    draw_rounded_box(badge_rect, renk, alpha=220, border_color=(255, 255, 255), radius=15)
    screen.blit(title_text, title_rect)

    draw_button(replay_btn, "Tekrar Oyna", (39, 174, 96), small_font)
    draw_button(to_menu_btn, "Ana Menü", (41, 128, 185), small_font)
    draw_button(exit_btn, "Çıkış", (192, 57, 43), small_font)

def seviye_2_baslat():
    global current_level, islands, playerX, playerY, playerImg, treasureX, treasureY, num_of_enemies, koruma_suresi, level_banner_timer, heart_active
    current_level = 2
    level_banner_timer = 120
    koruma_suresi = 90
    heart_active = False
    playerX = WIDTH // 2
    playerY = HEIGHT // 2
    playerImg = playerImgR
    islands = adalari_olustur(2)
    treasureX, treasureY = bos_konum_bul(islands, BOYUT)

    enemyImg.clear()
    enemyX.clear()
    enemyY.clear()
    enemyX_change.clear()
    enemyY_change.clear()
    num_of_enemies = ayar_dusman_sayisi + 1
    for _ in range(num_of_enemies):
        kraken_ekle(BASLANGIC_HIZI)

def reset_game():
    global score_value, canlar, koruma_suresi, playerX, playerY, playerImg, treasureX, treasureY, is_game_over, is_game_won, islands, num_of_enemies, current_level, heart_active, heart_spawn_timer
    score_value = 0
    canlar = MAX_CAN
    koruma_suresi = 0
    current_level = 1
    heart_active = False
    heart_spawn_timer = 0
    is_game_over = False
    is_game_won = False
    playerX = WIDTH // 2
    playerY = HEIGHT // 2
    playerImg = playerImgR
    islands = adalari_olustur(1)
    treasureX, treasureY = bos_konum_bul(islands, BOYUT)

    enemyImg.clear()
    enemyX.clear()
    enemyY.clear()
    enemyX_change.clear()
    enemyY_change.clear()
    num_of_enemies = ayar_dusman_sayisi
    for _ in range(num_of_enemies):
        kraken_ekle(BASLANGIC_HIZI)

running = True

while running:
    screen.blit(background, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()

            if game_state == "MENU":
                if start_btn.collidepoint(pos):
                    reset_game()
                    game_state = "PLAYING"
                elif settings_btn.collidepoint(pos):
                    game_state = "SETTINGS"
                elif menu_exit_btn.collidepoint(pos):
                    running = False

            elif game_state == "SETTINGS":
                if settings_back_btn.collidepoint(pos):
                    game_state = "MENU"
                else:
                    for satir in ayar_satirlari:
                        sid = satir["id"]
                        if "minus_rect" in satir and satir["minus_rect"].collidepoint(pos):
                            if sid == "hedef":
                                ayar_hedef_skor = max(satir["min"], ayar_hedef_skor - satir["adim"])
                            elif sid == "hizlanma":
                                ayar_hizlanma_adimi = max(satir["min"], ayar_hizlanma_adimi - satir["adim"])
                            elif sid == "dusman":
                                ayar_dusman_sayisi = max(satir["min"], ayar_dusman_sayisi - satir["adim"])
                            elif sid == "ada":
                                ayar_ada_sayisi = max(satir["min"], ayar_ada_sayisi - satir["adim"])

                        elif "plus_rect" in satir and satir["plus_rect"].collidepoint(pos):
                            if sid == "hedef":
                                ayar_hedef_skor = min(satir["max"], ayar_hedef_skor + satir["adim"])
                            elif sid == "hizlanma":
                                ayar_hizlanma_adimi = min(satir["max"], ayar_hizlanma_adimi + satir["adim"])
                            elif sid == "dusman":
                                ayar_dusman_sayisi = min(satir["max"], ayar_dusman_sayisi + satir["adim"])
                            elif sid == "ada":
                                ayar_ada_sayisi = min(satir["max"], ayar_ada_sayisi + satir["adim"])

            elif game_state == "PLAYING" and (is_game_over or is_game_won):
                if replay_btn.collidepoint(pos):
                    reset_game()
                elif to_menu_btn.collidepoint(pos):
                    game_state = "MENU"
                elif exit_btn.collidepoint(pos):
                    running = False

    if game_state == "MENU":
        draw_menu()

    elif game_state == "SETTINGS":
        draw_settings()

    elif game_state == "PLAYING":
        for ada_rect, buyuk_mu in islands:
            if buyuk_mu:
                screen.blit(bigIslandImg, ada_rect.topleft)
            else:
                screen.blit(islandImg, ada_rect.topleft)

        if not is_game_over and not is_game_won:
            if koruma_suresi > 0:
                koruma_suresi -= 1

            if canlar < MAX_CAN and not heart_active:
                heart_spawn_timer += 1
                if heart_spawn_timer >= 240:
                    heartX, heartY = bos_konum_bul(islands, 75, playerX, playerY)
                    heart_active = True
                    heart_spawn_timer = 0

            if heart_active:
                draw_bonus_heart(heartX, heartY)
                dist_heart = (((playerX + BOYUT // 2) - (heartX + 37)) ** 2 + ((playerY + BOYUT // 2) - (heartY + 37)) ** 2) ** 0.5
                if dist_heart < BOYUT * 0.7:
                    canlar = min(MAX_CAN, canlar + 1)
                    heart_active = False

            if pygame.mouse.get_pressed()[0]:
                touch_x, touch_y = pygame.mouse.get_pos()
                dx = touch_x - (playerX + BOYUT // 2)
                dy = touch_y - (playerY + BOYUT // 2)

                if abs(dx) > 5 or abs(dy) > 5:
                    if abs(dx) >= abs(dy):
                        playerImg = playerImgR if dx > 0 else playerImgL
                    else:
                        playerImg = playerImgD if dy > 0 else playerImgU

                hedefX = max(0, min(touch_x - (BOYUT // 2), WIDTH - BOYUT))
                hedefY = max(0, min(touch_y - (BOYUT // 2), HEIGHT - BOYUT))

                test_rect_x = pygame.Rect(hedefX, playerY, BOYUT, BOYUT).inflate(-28, -28)
                if not any(test_rect_x.colliderect(ada_rect.inflate(-28, -28)) for ada_rect, _ in islands):
                    playerX = hedefX

                test_rect_y = pygame.Rect(playerX, hedefY, BOYUT, BOYUT).inflate(-28, -28)
                if not any(test_rect_y.colliderect(ada_rect.inflate(-28, -28)) for ada_rect, _ in islands):
                    playerY = hedefY

            call_player(playerImg, playerX, playerY, koruma_suresi)
            call_treasure(treasureImg, treasureX, treasureY)

            for i in range(num_of_enemies):
                eski_x = enemyX[i]
                enemyX[i] += enemyX_change[i]
                enemy_rect_x = pygame.Rect(enemyX[i], enemyY[i], BOYUT, BOYUT).inflate(-26, -26)
                if enemyX[i] >= WIDTH - BOYUT or enemyX[i] <= 0 or any(enemy_rect_x.colliderect(ada_rect.inflate(-26, -26)) for ada_rect, _ in islands):
                    enemyX[i] = eski_x
                    enemyX_change[i] = -enemyX_change[i]

                eski_y = enemyY[i]
                enemyY[i] += enemyY_change[i]
                enemy_rect_y = pygame.Rect(enemyX[i], enemyY[i], BOYUT, BOYUT).inflate(-26, -26)
                if enemyY[i] >= HEIGHT - BOYUT or enemyY[i] <= 0 or any(enemy_rect_y.colliderect(ada_rect.inflate(-26, -26)) for ada_rect, _ in islands):
                    enemyY[i] = eski_y
                    enemyY_change[i] = -enemyY_change[i]

                enemy(enemyX[i], enemyY[i], i)

                dist_enemy = (((playerX - enemyX[i]) ** 2) + ((playerY - enemyY[i]) ** 2)) ** 0.5
                if dist_enemy < BOYUT * 0.65 and koruma_suresi == 0:
                    canlar -= 1
                    koruma_suresi = 90
                    if canlar <= 0:
                        is_game_over = True

            dist_treasure = (((playerX - treasureX) ** 2) + ((playerY - treasureY) ** 2)) ** 0.5
            if dist_treasure < BOYUT * 0.7:
                score_value += 1
                seviye_1_gecis = max(1, ayar_hedef_skor // 2)

                if score_value == seviye_1_gecis and current_level == 1:
                    seviye_2_baslat()
                elif score_value >= ayar_hedef_skor:
                    is_game_won = True
                else:
                    treasureX, treasureY = bos_konum_bul(islands, BOYUT)

                    if score_value % ayar_hizlanma_adimi == 0:
                        for i in range(num_of_enemies):
                            if enemyX_change[i] > 0:
                                enemyX_change[i] += 1
                            else:
                                enemyX_change[i] -= 1

                            if enemyY_change[i] > 0:
                                enemyY_change[i] += 1
                            else:
                                enemyY_change[i] -= 1

                        seviye_ici_artis = (score_value - (seviye_1_gecis if current_level == 2 else 0)) // ayar_hizlanma_adimi
                        guncel_hiz = BASLANGIC_HIZI + max(1, seviye_ici_artis)
                        kraken_ekle(guncel_hiz)
                        num_of_enemies += 1

            if level_banner_timer > 0:
                level_banner_timer -= 1
                lv_text = big_font.render("SEVİYE 2! Büyük Ada!", True, (255, 255, 255))
                lv_rect = lv_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                draw_rounded_box(lv_rect.inflate(60, 30), (39, 174, 96), alpha=220, border_color=(255, 255, 255), radius=18)
                screen.blit(lv_text, lv_rect)

        elif is_game_won:
            end_screen("Tebrikler! Oyunu Kazandınız!", (39, 174, 96))
        elif is_game_over:
            end_screen("Oyun Bitti!", (192, 57, 43))

        show_hud(score_value, canlar, current_level)

    pygame.display.update()
    clock.tick(60)

pygame.quit()
