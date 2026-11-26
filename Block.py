from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from PIL import Image
import random
import math

app = Ursina(fullscreen=True)

# --- AYARLAR (Performans için görüş mesafesi düşürüldü) ---
CHUNK_BOYUTU = 8
GORUS_MESAFESI = 1  # Donmaları önlemek için 1 yapıldı

# --- VERİ YAPILARI ---
dunya_verisi = {}
aktif_nesneler = {}
uretilen_chunklar = set()
yuklu_chunklar = set()
chunk_bloklari = {}
son_oyuncu_chunk = None
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
    1: "Cimen",
    2: "Tas",
    3: "Tugla",
    4: "Tahta",
    5: "Kum",
    6: "Cam",
    7: "Su (Sol Tik: Kurut)",
    8: "Altin",
    9: "Obsidyen"
}

bilgi_metni = Text(
    text="Blok: Cimen | 1-9: Sec | Sol Tik: Kir | Sag Tik: Koy | R: Konum Sifirla",
    position=(-0.85, 0.46),
    scale=1.0,
    color=color.white,
    background=True
)
nisangah = Text(text="+", origin=(0, 0), scale=1.5, color=color.white)

hotbar_kutulari = []
for i in range(1, 10):
    x_pos = (i - 5) * 0.085
    cerceve = Entity(parent=camera.ui, model='quad', scale=(0.075, 0.075), position=(x_pos, -0.43), color=color.dark_gray)
    ikon = Entity(parent=cerceve, model='quad', scale=(0.82, 0.82), texture=blok_dokulari.get(i), z=-0.1)
    Text(parent=cerceve, text=str(i), position=(-0.4, 0.4), scale=8, color=color.white, z=-0.2)
    hotbar_kutulari.append(cerceve)

el_modeli = Entity(
    parent=camera.ui,
    model='cube',
    texture=blok_dokulari.get(1),
    scale=(0.18, 0.18, 0.18),
    position=(0.55, -0.38),
    rotation=(20, -35, 10)
)

def arayuz_metni_guncelle():
    bilgi_metni.text = f"Blok: {blok_isimleri.get(secili_blok)} | Aktif Blok: {len(aktif_nesneler)} | R: Sifirla"

def hotbar_guncelle():
    for idx, kutu in enumerate(hotbar_kutulari):
        if idx + 1 == secili_blok:
            kutu.color = color.gold
            kutu.scale = (0.085, 0.085)
        else:
            kutu.color = color.dark_gray
            kutu.scale = (0.075, 0.075)
    el_modeli.texture = blok_dokulari.get(secili_blok)
    arayuz_metni_guncelle()

def pozisyon_anahtari(pos):
    x, y, z = pos
    return (round(x), round(y), round(z))

def chunk_koordinati(x, z):
    return (math.floor(x / CHUNK_BOYUTU), math.floor(z / CHUNK_BOYUTU))

def seffaf_mi(pos):
    if pos not in dunya_verisi:
        return True
    return dunya_verisi.get(pos).get('tur') in (6, 7, 11)

def blok_gorunur_mu(pos):
    x, y, z = pos
    komsular = [
        (x + 1, y, z), (x - 1, y, z),
        (x, y + 1, z), (x, y - 1, z),
        (x, y, z + 1), (x, y, z - 1)
    ]
    for k in komsular:
        if seffaf_mi(k):
            return True
    return False

def nesne_guncelle(pos):
    if pos not in dunya_verisi:
        if pos in aktif_nesneler:
            destroy(aktif_nesneler.pop(pos))
        return

    x, y, z = pos
    cx, cz = chunk_koordinati(x, z)
    if (cx, cz) not in yuklu_chunklar:
        if pos in aktif_nesneler:
            destroy(aktif_nesneler.pop(pos))
        return

    if blok_gorunur_mu(pos):
        if pos not in aktif_nesneler:
            veri = dunya_verisi.get(pos)
            aktif_nesneler[pos] = Voxel(
                position=pos,
                blok_turu=veri.get('tur'),
                su_seviyesi=veri.get('su'),
                kaynak_mi=veri.get('kaynak')
            )
    else:
        if pos in aktif_nesneler:
            destroy(aktif_nesneler.pop(pos))

def komsulari_guncelle(pos):
    x, y, z = pos
    for k in [(x+1, y, z), (x-1, y, z), (x, y+1, z), (x, y-1, z), (x, y, z+1), (x, y, z-1)]:
        nesne_guncelle(k)

def blok_verisi_ekle(position, blok_turu=1, su_seviyesi=4, kaynak_mi=True, aninda_ciz=True):
    anahtar = pozisyon_anahtari(position)
    if anahtar in dunya_verisi:
        if dunya_verisi.get(anahtar).get('tur') == 7 and blok_turu != 7:
            blok_kaldir(anahtar)
        else:
            return None

    dunya_verisi[anahtar] = {'tur': blok_turu, 'su': su_seviyesi, 'kaynak': kaynak_mi}
    
    cx, cz = chunk_koordinati(anahtar[0], anahtar[2])
    if (cx, cz) not in chunk_bloklari:
        chunk_bloklari[(cx, cz)] = set()
    chunk_bloklari[(cx, cz)].add(anahtar)

    if aninda_ciz:
        nesne_guncelle(anahtar)
        komsulari_guncelle(anahtar)
        arayuz_metni_guncelle()
    return anahtar

def blok_kaldir(pos):
    anahtar = pozisyon_anahtari(pos)
    if anahtar not in dunya_verisi:
        return
    
    dunya_verisi.pop(anahtar, None)
    cx, cz = chunk_koordinati(anahtar[0], anahtar[2])
    if (cx, cz) in chunk_bloklari:
        chunk_bloklari[(cx, cz)].discard(anahtar)

    if anahtar in aktif_nesneler:
        destroy(aktif_nesneler.pop(anahtar))
    komsulari_guncelle(anahtar)
    arayuz_metni_guncelle()

class Voxel(Button):
    def __init__(self, position=(0, 0, 0), blok_turu=1, su_seviyesi=4, kaynak_mi=True):
        self.blok_turu = blok_turu
        self.su_seviyesi = su_seviyesi
        self.kaynak_mi = kaynak_mi
        # Su bloğunun içinden düşmemek için collider eklendi (isterse kapatılabilir ama düşmeyi önler)
        collider_tipi = 'box' if blok_turu == 7 else 'box'
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            origin_y=0.5,
            texture=blok_dokulari.get(blok_turu),
            color=color.white,
            highlight_color=color.lime,
            collider=collider_tipi
        )

    def input(self, key):
        if self.hovered:
            if key == 'right mouse down':
                yeni_pos = self.position + mouse.normal
                blok_verisi_ekle(yeni_pos, blok_turu=secili_blok, kaynak_mi=True)
                el_modeli.animate_rotation((45, -35, 10), duration=0.08)
                invoke(setattr, el_modeli, 'rotation', (20, -35, 10), delay=0.08)
            elif key == 'left mouse down':
                anahtar = pozisyon_anahtari(self.position)
                blok_kaldir(anahtar)
                el_modeli.animate_rotation((45, -35, 10), duration=0.08)
                invoke(setattr, el_modeli, 'rotation', (20, -35, 10), delay=0.08)

def agac_dik_veri(x, y, z):
    for h in range(1, 5):
        blok_verisi_ekle((x, y + h, z), blok_turu=10, aninda_ciz=False)
    for dy in range(3, 6):
        genislik = 2 if dy < 5 else 1
        for dx in range(-genislik, genislik + 1):
            for dz in range(-genislik, genislik + 1):
                if abs(dx) == genislik and abs(dz) == genislik and dy == 4:
                    continue
                blok_verisi_ekle((x + dx, y + dy, z + dz), blok_turu=11, aninda_ciz=False)

def chunk_arazi_uret(cx, cz):
    if (cx, cz) in uretilen_chunklar:
        return
    uretilen_chunklar.add((cx, cz))
    baslangic_x = cx * CHUNK_BOYUTU
    baslangic_z = cz * CHUNK_BOYUTU
    for x in range(baslangic_x, baslangic_x + CHUNK_BOYUTU):
        for z in range(baslangic_z, baslangic_z + CHUNK_BOYUTU):
            yukseklik = round(math.sin(x * 0.15) * 2 + math.cos(z * 0.15) * 2)
            for y in range(-4, yukseklik + 1):
                if y == yukseklik:
                    tur = 5 if yukseklik <= -1 else 1
                elif y >= yukseklik - 2:
                    tur = 5 if yukseklik <= -1 else 1
                else:
                    tur = 2
                blok_verisi_ekle((x, y, z), blok_turu=tur, aninda_ciz=False)
            if yukseklik < -1:
                for sy in range(yukseklik + 1, 0):
                    blok_verisi_ekle((x, sy, z), blok_turu=7, su_seviyesi=4, kaynak_mi=True, aninda_ciz=False)
            if yukseklik >= 0 and random.random() < 0.025:
                if abs(x - baslangic_x) > 1 and abs(z - baslangic_z) > 1:
                    agac_dik_veri(x, yukseklik, z)

def chunk_gorunurluk_guncelle(merkez_cx, merkez_cz):
    global yuklu_chunklar
    yeni_yuklu = set()
    for dx in range(-GORUS_MESAFESI, GORUS_MESAFESI + 1):
        for dz in range(-GORUS_MESAFESI, GORUS_MESAFESI + 1):
            cx, cz = merkez_cx + dx, merkez_cz + dz
            yeni_yuklu.add((cx, cz))
            chunk_arazi_uret(cx, cz)
            
    cikarilacaklar = yuklu_chunklar - yeni_yuklu
    yuklu_chunklar = yeni_yuklu

    for pos in list(aktif_nesneler.keys()):
        cx, cz = chunk_koordinati(pos[0], pos[2])
        if (cx, cz) in cikarilacaklar:
            destroy(aktif_nesneler.pop(pos))

    for (cx, cz) in yeni_yuklu:
        if (cx, cz) in chunk_bloklari:
            for pos in chunk_bloklari[(cx, cz)]:
                nesne_guncelle(pos)
                
    arayuz_metni_guncelle()

gokyuzu = Sky(color=color.rgb(135, 206, 235))
gunes = DirectionalLight(shadows=False)
gunes.look_at(Vec3(1, -1, 1))

oyuncu = FirstPersonController(position=(0, 8, 0), speed=6)
oyuncu.cursor.visible = False

chunk_gorunurluk_guncelle(0, 0)
hotbar_guncelle()

def input(key):
    global secili_blok
    if key in [str(i) for i in range(1, 10)]:
        secili_blok = int(key)
        hotbar_guncelle()
    elif key == 'scroll up':
        secili_blok = 9 if secili_blok == 1 else secili_blok - 1
        hotbar_guncelle()
    elif key == 'scroll down':
        secili_blok = 1 if secili_blok == 9 else secili_blok + 1
        hotbar_guncelle()
    elif key == 'r':
        oyuncu.position = (0, 8, 0)
    elif key == 'escape':
        application.quit()

def update():
    global son_oyuncu_chunk, zaman
    zaman += time.dt
    mevcut_chunk = chunk_koordinati(oyuncu.x, oyuncu.z)
    if mevcut_chunk != son_oyuncu_chunk:
        son_oyuncu_chunk = mevcut_chunk
        chunk_gorunurluk_guncelle(mevcut_chunk[0], mevcut_chunk[1])
    
    # Haritanın altına düşerse güvenli konuma geri ışınla
    if oyuncu.y < -15:
        oyuncu.position = (0, 10, 0)
        oyuncu.y = 10

app.run()
