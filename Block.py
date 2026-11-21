from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from PIL import Image
import random
import math

app = Ursina()

dunya = {}
secili_blok = 1
zaman = 0

def doku_olustur(ana_renk, varyasyon=25, alfa=255, cizgi_tipi=None):
    img = Image.new('RGBA', (16, 16))
    piksel = img.load()
    r_ana, g_ana, b_ana = ana_renk

    for y in range(16):
        for x in range(16):
            fark = random.randint(-varyasyon, varyasyon)
            r = max(0, min(255, r_ana + fark))
            g = max(0, min(255, g_ana + fark))
            b = max(0, min(255, b_ana + fark))
            a = alfa

            if cizgi_tipi == 'tugla' and (y % 4 == 0 or (x + (y // 4) * 4) % 8 == 0):
                r, g, b = 190, 190, 190
            elif cizgi_tipi == 'tahta' and y % 4 == 0:
                r, g, b = max(0, r - 35), max(0, g - 35), max(0, b - 35)
            elif cizgi_tipi == 'kutuk' and (x % 3 == 0):
                r, g, b = max(0, r - 25), max(0, g - 25), max(0, b - 25)
            elif cizgi_tipi == 'yaprak' and random.random() < 0.25:
                a = 180
            elif cizgi_tipi == 'cam':
                if x == 0 or x == 15 or y == 0 or y == 15 or (x == y and 3 < x < 12):
                    r, g, b, a = 240, 250, 255, 220
                else:
                    a = 65

            piksel[x, y] = (r, g, b, a)

    tex = Texture(img)
    tex.filtering = None
    return tex

blok_dokulari = {
    1: doku_olustur((95, 185, 80), varyasyon=22),
    2: doku_olustur((135, 135, 135), varyasyon=25),
    3: doku_olustur((175, 75, 65), varyasyon=15, cizgi_tipi='tugla'),
    4: doku_olustur((155, 105, 55), varyasyon=15, cizgi_tipi='tahta'),
    5: doku_olustur((225, 210, 135), varyasyon=18),
    6: doku_olustur((200, 240, 255), varyasyon=5, cizgi_tipi='cam'),
    7: doku_olustur((35, 115, 225), varyasyon=20, alfa=180),
    8: doku_olustur((245, 200, 20), varyasyon=25),
    9: doku_olustur((40, 25, 55), varyasyon=15),
    10: doku_olustur((105, 70, 35), varyasyon=15, cizgi_tipi='kutuk'),
    11: doku_olustur((50, 140, 45), varyasyon=25, cizgi_tipi='yaprak')
}

blok_isimleri = {
    1: "Cimen", 2: "Tas", 3: "Tugla", 4: "Tahta", 5: "Kum",
    6: "Cam", 7: "Su (Sol Tik: Kurut)", 8: "Altin", 9: "Obsidyen"
}

bilgi_metni = Text(text="Blok: Cimen | 1-9: Sec | Sol Tik: Kir | Sag Tik: Koy | R: Konum Sifirla", position=(-0.85, 0.46), scale=1.0, color=color.white, background=True)
nisangah = Text(text="+", origin=(0, 0), scale=1.5, color=color.white)

hotbar_kutulari = []
for i in range(1, 10):
    x_pos = (i - 5) * 0.085
    cerceve = Entity(parent=camera.ui, model='quad', scale=(0.075, 0.075), position=(x_pos, -0.43), color=color.dark_gray)
    ikon = Entity(parent=cerceve, model='quad', scale=(0.82, 0.82), texture=blok_dokulari[i], z=-0.1)
    Text(parent=cerceve, text=str(i), position=(-0.4, 0.4), scale=8, color=color.white, z=-0.2)
    hotbar_kutulari.append(cerceve)

# DÜZELTİLEN SATIR: blok_dokulari[1] olarak tek doku verildi
el_modeli = Entity(parent=camera.ui, model='cube', texture=blok_dokulari[1], scale=(0.18, 0.18, 0.18), position=(0.55, -0.38), rotation=(20, -35, 10))

def hotbar_guncelle():
    for idx, kutu in enumerate(hotbar_kutulari):
        if idx + 1 == secili_blok:
            kutu.color = color.gold
            kutu.scale = (0.085, 0.085)
        else:
            kutu.color = color.dark_gray
            kutu.scale = (0.075, 0.075)
    el_modeli.texture = blok_dokulari[secili_blok]
    bilgi_metni.text = f"Blok: {blok_isimleri[secili_blok]} | 1-9: Sec | Sol Tik: Kir | Sag Tik: Koy | R: Konum Sifirla"

# DÜZELTİLEN SATIR: Koordinat indeksleri eklendi
def pozisyon_anahtari(pos):
    return (round(pos[0]), round(pos[1]), round(pos[2]))

def blok_olustur(position=(0, 0, 0), blok_turu=1, su_seviyesi=4, kaynak_mi=True):
    anahtar = pozisyon_anahtari(position)
    if anahtar in dunya:
        if dunya[anahtar].blok_turu == 7 and blok_turu != 7:
            destroy(dunya[anahtar])
            del dunya[anahtar]
        else:
            return None
    yeni_blok = Voxel(position=anahtar, blok_turu=blok_turu, su_seviyesi=su_seviyesi, kaynak_mi=kaynak_mi)
    dunya[anahtar] = yeni_blok
    return yeni_blok

class Voxel(Button):
    def __init__(self, position=(0, 0, 0), blok_turu=1, su_seviyesi=4, kaynak_mi=True):
        self.blok_turu = blok_turu
        self.su_seviyesi = su_seviyesi
        self.kaynak_mi = kaynak_mi
        collider_tipi = None if blok_turu == 7 else 'box'
        super().__init__(parent=scene, position=position, model='cube', origin_y=0.5, texture=blok_dokulari[blok_turu], color=color.white, highlight_color=color.lime, collider=collider_tipi)
        if self.blok_turu == 7:
            invoke(self.su_akis, delay=0.3)

    def su_akis(self):
        if self not in scene.entities:
            return
        x, y, z = round(self.x), round(self.y), round(self.z)

        if not self.kaynak_mi:
            ust_pos = (x, y + 1, z)
            ustten_besleniyor = ust_pos in dunya and dunya[ust_pos].blok_turu == 7
            yandan_besleniyor = False
            for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                k_pos = (x + dx, y, z + dz)
                if k_pos in dunya and dunya[k_pos].blok_turu == 7 and dunya[k_pos].su_seviyesi > self.su_seviyesi:
                    yandan_besleniyor = True
                    break

            if not ustten_besleniyor and not yandan_besleniyor:
                if (x, y, z) in dunya:
                    del dunya[(x, y, z)]
                destroy(self)
                cevre_su_kontrol((x, y, z))
                return

        alt_pos = (x, y - 1, z)
        if alt_pos not in dunya and y > -10:
            blok_olustur(position=alt_pos, blok_turu=7, su_seviyesi=4, kaynak_mi=False)
            return

        if alt_pos in dunya and dunya[alt_pos].blok_turu != 7 and self.su_seviyesi > 0:
            for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                yan_pos = (x + dx, y, z + dz)
                if yan_pos not in dunya:
                    blok_olustur(position=yan_pos, blok_turu=7, su_seviyesi=self.su_seviyesi - 1, kaynak_mi=False)

    def input(self, key):
        if self.hovered:
            if key == 'right mouse down':
                yeni_pos = self.position + mouse.normal
                blok_olustur(position=yeni_pos, blok_turu=secili_blok, kaynak_mi=True)
                el_modeli.animate_rotation((45, -35, 10), duration=0.08)
                invoke(setattr, el_modeli, 'rotation', (20, -35, 10), delay=0.08)

            elif key == 'left mouse down':
                anahtar = pozisyon_anahtari(self.position)
                # DÜZELTİLEN SATIR: İndeksler eklendi
                hedef_ust = (anahtar[0], anahtar[1] + 1, anahtar[2])
                if secili_blok == 7 and hedef_ust in dunya and dunya[hedef_ust].blok_turu == 7:
                    destroy(dunya[hedef_ust])
                    del dunya[hedef_ust]
                    cevre_su_kontrol(hedef_ust)
                    return

                if anahtar in dunya:
                    del dunya[anahtar]
                destroy(self)
                cevre_su_kontrol(anahtar)
                el_modeli.animate_rotation((45, -35, 10), duration=0.08)
                invoke(setattr, el_modeli, 'rotation', (20, -35, 10), delay=0.08)

def cevre_su_kontrol(pos):
    x, y, z = pos
    komsular = [(x, y+1, z), (x, y-1, z), (x+1, y, z), (x-1, y, z), (x, y, z+1), (x, y, z-1)]
    for k in komsular:
        if k in dunya and dunya[k].blok_turu == 7:
            invoke(dunya[k].su_akis, delay=0.25)

def agac_dik(x, y, z):
    for h in range(1, 5):
        blok_olustur((x, y + h, z), blok_turu=10)
    for dy in range(3, 6):
        genislik = 2 if dy < 5 else 1
        for dx in range(-genislik, genislik + 1):
            for dz in range(-genislik, genislik + 1):
                if abs(dx) == genislik and abs(dz) == genislik and dy == 4:
                    continue
                blok_olustur((x + dx, y + dy, z + dz), blok_turu=11)

gokyuzu = Sky()
oyuncu = FirstPersonController(position=(12, 8, 12), speed=6)
hotbar_guncelle()

for z in range(24):
    for x in range(24):
        yukseklik = int(math.sin(x * 0.25) * 1.5 + math.cos(z * 0.25) * 1.5)
        blok_olustur((x, yukseklik, z), blok_turu=1)
        blok_olustur((x, yukseklik - 1, z), blok_turu=2)
        blok_olustur((x, yukseklik - 2, z), blok_turu=2)
        if 3 < x < 20 and 3 < z < 20 and random.random() < 0.025:
            agac_dik(x, yukseklik, z)

def update():
    global secili_blok, zaman
    for tus in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
        if held_keys[tus] and secili_blok != int(tus):
            secili_blok = int(tus)
            hotbar_guncelle()

    zaman += time.dt * 0.05
    parlaklik = (math.sin(zaman) + 1) / 2
    gokyuzu.color = color.rgb(int(20 + 115 * parlaklik), int(25 + 175 * parlaklik), int(50 + 205 * parlaklik))

    if oyuncu.y < -15:
        oyuncu.position = (12, 10, 12)

def input(key):
    global secili_blok
    if key == 'escape':
        application.quit()
    elif key == 'r':
        oyuncu.position = (12, 10, 12)
    elif key == 'scroll up':
        secili_blok = 1 if secili_blok == 9 else secili_blok + 1
        hotbar_guncelle()
    elif key == 'scroll down':
        secili_blok = 9 if secili_blok == 1 else secili_blok - 1
        hotbar_guncelle()

app.run()
