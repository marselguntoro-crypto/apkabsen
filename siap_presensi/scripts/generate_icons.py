"""
Script Generator Asset Ikon Resmi SIAP.
Menghasilkan SIAP.png (256x256) dan SIAP.ico (Multi-resolusi Windows Icon).
Format .ico memuat resolusi: 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
ICONS_DIR = BASE_DIR / "assets" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

PNG_PATH = ICONS_DIR / "SIAP.png"
ICO_PATH = ICONS_DIR / "SIAP.ico"


def create_siap_icon():
    # Buat kanvas 256x256 RGBA dengan antialiasing supersampling 4x (1024x1024)
    canvas_size = 1024
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Warna
    navy_dark = (15, 23, 42, 255)       # #0f172a
    blue_primary = (29, 78, 216, 255)   # #1d4ed8
    blue_light = (59, 130, 246, 255)    # #3b82f6
    emerald_accent = (16, 185, 129, 255) # #10b981
    white = (255, 255, 255, 255)

    # 1. Background rounded rectangle (Shield / Card)
    pad = 48
    radius = 220
    draw.rounded_rectangle(
        [pad, pad, canvas_size - pad, canvas_size - pad],
        radius=radius,
        fill=navy_dark,
        outline=blue_light,
        width=20,
    )

    # 2. Inner glow / decorative subtle arc
    draw.arc(
        [pad + 40, pad + 40, canvas_size - pad - 40, canvas_size - pad - 40],
        start=200,
        end=340,
        fill=blue_primary,
        width=16,
    )

    # 3. Clock / Biometric Gauge Motif
    center_x = canvas_size // 2
    center_y = canvas_size // 2 - 40
    outer_r = 280
    draw.ellipse(
        [center_x - outer_r, center_y - outer_r, center_x + outer_r, center_y + outer_r],
        outline=blue_primary,
        width=24,
    )
    inner_r = 240
    draw.ellipse(
        [center_x - inner_r, center_y - inner_r, center_x + inner_r, center_y + inner_r],
        fill=(30, 41, 59, 255),
    )

    # 4. Large Checkmark (Presensi Akurat & Disiplin)
    # Titik checkmark
    p1 = (center_x - 120, center_y + 10)
    p2 = (center_x - 30, center_y + 100)
    p3 = (center_x + 130, center_y - 80)
    draw.line([p1, p2, p3], fill=emerald_accent, width=44, joint="round")

    # 5. Teks "SIAP" di bagian bawah badge
    # Gambar badge pita teks "SIAP"
    text_box_y1 = canvas_size - 250
    text_box_y2 = canvas_size - 110
    draw.rounded_rectangle(
        [center_x - 260, text_box_y1, center_x + 260, text_box_y2],
        radius=40,
        fill=blue_primary,
        outline=white,
        width=8,
    )

    # Gambar huruf S I A P menggunakan poligon geometris agar tidak bergantung pada font ttf eksternal
    letter_color = white
    # S
    # Gambar huruf-huruf dengan garis tebal
    # S
    sx = center_x - 190
    draw.line([(sx + 50, text_box_y1 + 25), (sx + 10, text_box_y1 + 25), (sx + 10, text_box_y1 + 65), (sx + 50, text_box_y1 + 75), (sx + 50, text_box_y1 + 115), (sx + 10, text_box_y1 + 115)], fill=letter_color, width=18, joint="round")
    # I
    ix = center_x - 70
    draw.line([(ix + 20, text_box_y1 + 25), (ix + 20, text_box_y1 + 115)], fill=letter_color, width=18)
    draw.line([(ix, text_box_y1 + 25), (ix + 40, text_box_y1 + 25)], fill=letter_color, width=18)
    draw.line([(ix, text_box_y1 + 115), (ix + 40, text_box_y1 + 115)], fill=letter_color, width=18)
    # A
    ax = center_x + 30
    draw.line([(ax, text_box_y1 + 115), (ax + 25, text_box_y1 + 25), (ax + 50, text_box_y1 + 115)], fill=letter_color, width=18, joint="round")
    draw.line([(ax + 10, text_box_y1 + 78), (ax + 40, text_box_y1 + 78)], fill=letter_color, width=16)
    # P
    px = center_x + 140
    draw.line([(px + 10, text_box_y1 + 115), (px + 10, text_box_y1 + 25), (px + 45, text_box_y1 + 25), (px + 45, text_box_y1 + 70), (px + 10, text_box_y1 + 70)], fill=letter_color, width=18, joint="round")

    # Downsample ke ukuran 256x256 dengan filter Lanczos untuk kualitas kristal tinggi
    final_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    final_256.save(PNG_PATH, format="PNG")
    print(f"[SUKSES] Icon PNG tersimpan di: {PNG_PATH}")

    # Simpan sebagai Windows multi-resolution icon ICO
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    final_256.save(ICO_PATH, format="ICO", sizes=ico_sizes)
    print(f"[SUKSES] Icon ICO tersimpan di: {ICO_PATH}")


if __name__ == "__main__":
    create_siap_icon()
