#!/usr/bin/env python3
"""
Gera a imagem 1080x1080 de um artigo (para Facebook, Instagram e og:image),
no mesmo estilo das imagens "Artigo" da campanha: foto com véu verde,
etiqueta da categoria, título e resumo, rodapé com telefone.

Uso como módulo:  gerar(slug, categoria_label, titulo, resumo) -> caminho
Uso directo:      python3 scripts/imagem_artigo.py <slug>   (lê artigos.json)
Requer: Pillow (pip install pillow)
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SOC = ROOT / "social"
FOTOS = sorted((SOC / "fotos").glob("foto_*.jpg"))
OUT = ROOT / "img" / "artigos"

GREEN_DEEP = (15, 48, 32)
GREEN = (27, 79, 53)
CREAM = (245, 240, 232)
SAGE = (168, 213, 181)
W = H = 1080
FOOT = 96
TEL = "210 303 361"


def lora(size, weight="Bold"):
    f = ImageFont.truetype(str(SOC / "fonts" / "Lora-Variable.ttf"), size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def poppins(size, style="Bold"):
    return ImageFont.truetype(str(SOC / "fonts" / f"Poppins-{style}.ttf"), size)


def measure(d, t, f):
    b = d.textbbox((0, 0), t, font=f)
    return b[2] - b[0]


def wrap(d, text, font, maxw):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if measure(d, t, font) > maxw and line:
            out.append(line)
            line = w
        else:
            line = t
    if line:
        out.append(line)
    return out


def plan(d, text, maxw, max_lines, hi, lo, ratio, weight):
    size = hi
    while size > lo:
        f = lora(size, weight)
        if len(wrap(d, text, f, maxw)) <= max_lines:
            break
        size -= 2
    f = lora(size, weight)
    lines = wrap(d, text, f, maxw)
    if len(lines) > max_lines:  # corta com reticências se mesmo assim não couber
        lines = lines[:max_lines]
        while lines[-1] and measure(d, lines[-1] + "…", f) > maxw:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "…"
    lh = int(size * ratio)
    return f, lines, lh, len(lines) * lh


def put(d, x, y, f, lines, lh, fill):
    for i, l in enumerate(lines):
        d.text((x, y + i * lh), l, font=f, fill=fill)
    return y + len(lines) * lh


def gerar(slug, cat_label, titulo, resumo):
    # roda as fotos por ordem, para artigos seguidos não repetirem a mesma foto
    feitas = [f for f in OUT.glob("*.jpg") if f.stem != slug] if OUT.exists() else []
    idx = len(feitas) % len(FOTOS)
    img = Image.open(FOTOS[idx]).convert("RGB").resize((W, H))
    veu = Image.new("RGB", (W, H), GREEN_DEEP)
    mask = Image.new("L", (W, H))
    md = ImageDraw.Draw(mask)
    for y in range(H):
        a = 0.18 if y < 420 else min(0.90, 0.18 + 0.72 * (y - 420) / 360)
        md.line([(0, y), (W, y)], fill=int(a * 255))
    img = Image.composite(veu, img, mask)
    d = ImageDraw.Draw(img)

    # etiqueta
    tag = f"NOVO ARTIGO · {cat_label.upper()}"
    ft = poppins(22)
    h = 22 * 2 + 16
    d.rounded_rectangle((48, 44, 48 + measure(d, tag, ft) + 56, 44 + h), radius=h // 2, fill=CREAM)
    d.text((48 + 28, 44 + (h - 22 * 1.45) / 2), tag, font=ft, fill=GREEN)

    # título + resumo
    fT, lT, hT, aT = plan(d, titulo, 984, 3, 62, 40, 1.20, "Bold")
    fR, lR, hR, aR = plan(d, resumo, 984, 3, 30, 22, 1.42, "Regular")
    top = H - FOOT - 56 - (aT + 24 + aR)
    y = put(d, 48, top, fT, lT, hT, CREAM)
    put(d, 48, y + 24, fR, lR, hR, (198, 222, 206))

    # rodapé
    d.rectangle([0, H - FOOT, W, H], fill=GREEN_DEEP)
    fb, fi = lora(31, "Bold"), lora(31, "SemiBold")
    d.text((48, H - FOOT + 30), "Saúde", font=fb, fill=CREAM)
    d.text((48 + measure(d, "Saúde", fb) + 11, H - FOOT + 30), "Auditiva", font=fi, fill=SAGE)
    fp, fs = poppins(27), poppins(16, "Medium")
    d.text((W - 48 - measure(d, TEL, fp), H - FOOT + 22), TEL, font=fp, fill=CREAM)
    d.text((W - 48 - measure(d, "saudeauditiva.pt", fs), H - FOOT + 58), "saudeauditiva.pt", font=fs, fill=SAGE)

    OUT.mkdir(parents=True, exist_ok=True)
    destino = OUT / f"{slug}.jpg"
    img.save(destino, quality=88, optimize=True)
    return destino


if __name__ == "__main__":
    CATS = {"perda-auditiva": "Perda Auditiva", "sinais-alerta": "Sinais de Alerta",
            "prevencao": "Prevenção", "familia": "Família", "aparelhos": "Aparelhos"}
    arts = {a["slug"]: a for a in json.loads((ROOT / "artigos.json").read_text(encoding="utf-8"))}
    a = arts[sys.argv[1]]
    print(gerar(a["slug"], CATS[a["categoria"]], a["titulo"], a["resumo"]))
