from fastapi import FastAPI, Query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import textwrap

app = FastAPI(
    title="DAPP Bateman Meme API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(BASE_DIR, "template.jpg")

# Template: 864 x 1536
# White text areas are on the right side of each panel.
PANELS = [
    (402, 5, 859, 501),
    (402, 516, 859, 1016),
    (402, 1027, 859, 1529),
]

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def get_font(size: int):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def fit_text(draw, text, box_w, box_h):
    """Find a readable font size and wrap text to fit the white box."""
    text = text.strip()
    if not text:
        return "", get_font(30), 0, 0

    # Try from large to small.
    for size in range(64, 15, -2):
        font = get_font(size)
        # Approximate characters per line, then verify by pixel width.
        words = text.split()
        lines = []
        current = ""

        for word in words:
            candidate = word if not current else current + " " + word
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] - bbox[0] <= box_w:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        # Handle very long single words.
        fixed = []
        for line in lines:
            if draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0] <= box_w:
                fixed.append(line)
            else:
                chunks = textwrap.wrap(line, width=max(1, int(box_w / max(size * 0.55, 1))))
                fixed.extend(chunks)

        spacing = max(4, int(size * 0.16))
        heights = []
        widths = []
        for line in fixed:
            b = draw.textbbox((0, 0), line, font=font)
            widths.append(b[2] - b[0])
            heights.append(b[3] - b[1])

        total_h = sum(heights) + spacing * max(0, len(fixed) - 1)
        max_w = max(widths) if widths else 0

        if total_h <= box_h * 0.82 and max_w <= box_w * 0.88:
            return "\n".join(fixed), font, total_h, spacing

    font = get_font(16)
    return text, font, 20, 4


def draw_centered_text(draw, text, box):
    x1, y1, x2, y2 = box
    pad_x = 30
    pad_y = 25
    box_w = x2 - x1 - pad_x * 2
    box_h = y2 - y1 - pad_y * 2

    wrapped, font, total_h, spacing = fit_text(draw, text, box_w, box_h)
    lines = wrapped.split("\n") if wrapped else []

    y = y1 + (y2 - y1 - total_h) / 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = x1 + (x2 - x1 - w) / 2

        # Subtle black text, centered in the white panel.
        draw.text((x, y), line, font=font, fill=(20, 20, 20))
        y += h + spacing


@app.get("/")
def home():
    return {
        "status": True,
        "name": "DAPP Bateman Meme API",
        "usage": "/api/meme/bateman?teks1=...&teks2=...&teks3=...",
        "method": "GET"
    }


@app.get("/api/meme/bateman")
def bateman(
    teks1: str = Query("", description="Teks panel pertama"),
    teks2: str = Query("", description="Teks panel kedua"),
    teks3: str = Query("", description="Teks panel ketiga"),
):
    texts = [teks1, teks2, teks3]

    if not any(t.strip() for t in texts):
        return {
            "status": False,
            "error": "Isi minimal salah satu parameter: teks1, teks2, atau teks3"
        }

    if not os.path.exists(TEMPLATE):
        return {
            "status": False,
            "error": "Template tidak ditemukan"
        }

    image = Image.open(TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(image)

    for text, panel in zip(texts, PANELS):
        if text.strip():
            draw_centered_text(draw, text, panel)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return Response(
        content=output.getvalue(),
        media_type="image/png",
        headers={
            "Cache-Control": "no-store"
        }
    )
