"""
Gera a imagem de um post para o Instagram (@islamic.siraj).

Formato: 1080x1350 (4:5), texto em árabe no alto e tradução em português embaixo.

Uso:
  # Versículo: o texto árabe vem sempre de dados/quran.json (nunca digitado à mão)
  python gerar_post.py ayah --ref 2:286 --pt "Allah não impõe a nenhuma alma..." --out post.png

  # Hadith, dua ou reflexão: texto árabe e fonte informados
  python gerar_post.py hadith --ar "..." --pt "..." --fonte "Sahih al-Bukhari, 1" --out post.png
  python gerar_post.py dua --ar "..." --pt "..." --fonte "Alcorão 2:201" --out post.png
  python gerar_post.py reflexao --pt "..." [--ar "..."] --out post.png
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, features

BASE = Path(__file__).resolve().parent
FONTS = BASE / "fonts"
QURAN = BASE / "dados" / "quran.json"

W, H = 1080, 1350
MARGEM = 110

FUNDO_TOPO = (10, 42, 38)
FUNDO_BASE = (4, 20, 18)
DOURADO = (212, 175, 96)
TEXTO = (244, 238, 224)
TEXTO_SUAVE = (190, 182, 160)

ROTULOS = {
    "ayah": ("آية", "VERSÍCULO DO ALCORÃO"),
    "hadith": ("حديث", "HADITH"),
    "dua": ("دعاء", "SÚPLICA"),
    "reflexao": ("تذكرة", "LEMBRETE"),
}

ASSINATURA = "@islamic.siraj"


def fonte(nome, tamanho):
    return ImageFont.truetype(str(FONTS / nome), tamanho, layout_engine=ImageFont.Layout.RAQM)


def ayah(ref):
    surata, versiculo = (int(x) for x in ref.split(":"))
    capitulos = json.loads(QURAN.read_text(encoding="utf-8"))
    cap = capitulos[surata - 1]
    assert cap["id"] == surata
    verso = cap["verses"][versiculo - 1]
    assert verso["id"] == versiculo
    return verso["text"], cap["name"], cap["transliteration"]


def quebrar(draw, texto, fnt, largura, **kw):
    """Quebra o texto em linhas que caibam na largura dada."""
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = f"{atual} {palavra}".strip()
        if draw.textlength(teste, font=fnt, **kw) <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def bloco(draw, texto, nome_fonte, tamanhos, largura, altura_max, entrelinha, **kw):
    """Escolhe o maior tamanho de fonte em que o bloco caiba na altura disponível."""
    for tam in tamanhos:
        fnt = fonte(nome_fonte, tam)
        linhas = quebrar(draw, texto, fnt, largura, **kw)
        altura = int(len(linhas) * tam * entrelinha)
        if altura <= altura_max:
            return fnt, linhas, tam, altura
    raise SystemExit(f"Texto longo demais para caber na imagem ({len(texto.split())} palavras). Escolha um texto mais curto.")


def desenhar_linhas(draw, linhas, fnt, tam, y, entrelinha, cor, **kw):
    for linha in linhas:
        largura = draw.textlength(linha, font=fnt, **kw)
        draw.text(((W - largura) / 2, y), linha, font=fnt, fill=cor, **kw)
        y += int(tam * entrelinha)
    return y


def ornamento(draw, y):
    cx = W // 2
    draw.line([(cx - 170, y), (cx - 22, y)], fill=DOURADO, width=2)
    draw.line([(cx + 22, y), (cx + 170, y)], fill=DOURADO, width=2)
    r = 9
    draw.polygon([(cx, y - r), (cx + r, y), (cx, y + r), (cx - r, y)], outline=DOURADO, width=2)


def gerar(tipo, ar, pt, fonte_ref, saida):
    img = Image.new("RGB", (W, H), FUNDO_BASE)
    draw = ImageDraw.Draw(img)

    # Gradiente vertical do fundo
    for y in range(H):
        t = y / H
        cor = tuple(int(FUNDO_TOPO[i] * (1 - t) + FUNDO_BASE[i] * t) for i in range(3))
        draw.line([(0, y), (W, y)], fill=cor)

    # Moldura dupla
    draw.rectangle([40, 40, W - 40, H - 40], outline=DOURADO, width=2)
    draw.rectangle([52, 52, W - 52, H - 52], outline=(*DOURADO, 90), width=1)

    ar_kw = dict(direction="rtl", language="ar")
    largura = W - 2 * MARGEM

    # Cabeçalho
    rot_ar, rot_pt = ROTULOS[tipo]
    f_rot_ar = fonte("Amiri-arabic-Bold.ttf", 54)
    lw = draw.textlength(rot_ar, font=f_rot_ar, **ar_kw)
    draw.text(((W - lw) / 2, 95), rot_ar, font=f_rot_ar, fill=DOURADO, **ar_kw)
    f_rot_pt = fonte("Amiri-latin-Bold.ttf", 26)
    rot_pt_esp = " ".join(rot_pt)  # espaçamento entre letras
    lw = draw.textlength(rot_pt_esp, font=f_rot_pt)
    draw.text(((W - lw) / 2, 180), rot_pt_esp, font=f_rot_pt, fill=TEXTO_SUAVE)

    topo, rodape = 250, H - 200
    espaco = rodape - topo

    # Mede os blocos
    blocos = []
    if ar:
        ar_alvo = espaco * (0.55 if pt else 1.0)
        f_ar, l_ar, t_ar, h_ar = bloco(draw, ar, "Amiri-arabic-Regular.ttf", range(64, 33, -2), largura, ar_alvo, 1.75, **ar_kw)
        blocos.append(("ar", f_ar, l_ar, t_ar, h_ar))
    if pt:
        usado = sum(b[4] for b in blocos) + (70 if blocos else 0)
        f_pt, l_pt, t_pt, h_pt = bloco(draw, pt, "Amiri-latin-Regular.ttf", range(44, 25, -2), largura - 40, espaco - usado - 60, 1.4)
        blocos.append(("pt", f_pt, l_pt, t_pt, h_pt))
    if fonte_ref:
        f_ref = fonte("Amiri-latin-Bold.ttf", 28)
        blocos.append(("ref", f_ref, [f"— {fonte_ref}"], 28, 50))

    total = sum(b[4] for b in blocos) + (70 if ar and pt else 0) + (30 if fonte_ref else 0)
    y = topo + (espaco - total) // 2

    for tipo_b, fnt, linhas, tam, alt in blocos:
        if tipo_b == "ar":
            y = desenhar_linhas(draw, linhas, fnt, tam, y, 1.75, TEXTO, **ar_kw)
            if pt:
                ornamento(draw, y + 30)
                y += 70
        elif tipo_b == "pt":
            y = desenhar_linhas(draw, linhas, fnt, tam, y, 1.4, TEXTO)
        else:
            y += 30
            desenhar_linhas(draw, linhas, fnt, tam, y, 1.0, DOURADO)

    # Assinatura
    ornamento(draw, H - 150)
    f_ass = fonte("Amiri-latin-Regular.ttf", 30)
    lw = draw.textlength(ASSINATURA, font=f_ass)
    draw.text(((W - lw) / 2, H - 125), ASSINATURA, font=f_ass, fill=TEXTO_SUAVE)

    img.save(saida, "JPEG", quality=93)
    print(saida)


def main():
    if not features.check("raqm"):
        sys.exit("Pillow sem suporte a raqm: o árabe sairia sem ligaduras. Instale libraqm.")

    p = argparse.ArgumentParser()
    p.add_argument("tipo", choices=ROTULOS)
    p.add_argument("--ref", help="surata:versículo (só para ayah)")
    p.add_argument("--ar", help="texto árabe (hadith, dua, reflexão)")
    p.add_argument("--pt", help="tradução / texto em português")
    p.add_argument("--fonte", help="fonte exibida no rodapé do texto")
    p.add_argument("--out", required=True)
    a = p.parse_args()

    ar, fonte_ref = a.ar, a.fonte
    if a.tipo == "ayah":
        if not a.ref:
            sys.exit("ayah exige --ref surata:versículo")
        ar, nome_ar, nome_lat = ayah(a.ref)
        fonte_ref = fonte_ref or f"Alcorão, {nome_lat} {a.ref}"
    if not (ar or a.pt):
        sys.exit("Informe --ar e/ou --pt")

    gerar(a.tipo, ar, a.pt, fonte_ref, a.out)


if __name__ == "__main__":
    main()
