#!/usr/bin/env python3
"""
Publica um artigo no site Saúde Auditiva a partir de um ficheiro JSON.

Usa o mesmo layout dos artigos escritos à mão (artigos/zumbido-acufenos.html
serve de molde), actualiza artigos.json, sitemap.xml e data/history.json.

Uso:
  python3 scripts/publicar_artigo.py caminho/para/artigo.json [--data AAAA-MM-DD]

Formato do JSON:
{
  "topic_id": "pa-004",                 (opcional, id de data/topicos.json)
  "slug": "perda-auditiva-unilateral",  (opcional; gerado a partir do título)
  "titulo": "Título do artigo",
  "categoria": "perda-auditiva | sinais-alerta | prevencao | familia | aparelhos",
  "resumo": "1-2 frases para o cartão e meta description (máx ~200 caracteres)",
  "dek": "subtítulo jornalístico",
  "corpo_html": "<p>...</p><h2>...</h2>...",
  "social": {
    "facebook": "texto do post de Facebook (sem link; o link é acrescentado)",
    "instagram": "legenda do Instagram (sem hashtags)",
    "hashtags": ["#saudeauditiva", "..."]
  }
}

Gera também img/artigos/<slug>.jpg (imagem para as redes e og:image).
Os posts no Facebook e Instagram são publicados pelo Apps Script
"Saúde Auditiva — Publicação Facebook" (função publicarArtigoMeta),
que lê artigos.json e publica os artigos com "social" ainda não publicados.
"""
import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import imagem_artigo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MOLDE = ROOT / "artigos" / "zumbido-acufenos.html"
MOLDE_SLUG = "zumbido-acufenos"

CATS = {
    "perda-auditiva": "Perda Auditiva",
    "sinais-alerta": "Sinais de Alerta",
    "prevencao": "Prevenção",
    "familia": "Família",
    "aparelhos": "Aparelhos",
}
RELACIONADAS = {
    "perda-auditiva": ["perda-auditiva", "sinais-alerta", "aparelhos"],
    "sinais-alerta": ["sinais-alerta", "perda-auditiva", "prevencao"],
    "prevencao": ["prevencao", "perda-auditiva", "sinais-alerta"],
    "familia": ["familia", "sinais-alerta", "aparelhos"],
    "aparelhos": ["aparelhos", "perda-auditiva", "familia"],
}
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def slugify(t):
    t = unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"[^\w\s-]", "", t).strip().lower()
    return re.sub(r"[-\s]+", "-", t)[:70].strip("-")


def tempo_leitura(html):
    palavras = len(re.sub(r"<[^>]+>", " ", html).split())
    return f"{max(2, round(palavras / 200))} min"


def sub1(padrao, novo, texto):
    res, n = re.subn(padrao, lambda m: novo, texto, count=1, flags=re.S)
    if n != 1:
        sys.exit(f"Molde mudou: não encontrei {padrao!r}")
    return res


def render(a, data):
    html = MOLDE.read_text(encoding="utf-8")
    cat, label = a["categoria"], CATS[a["categoria"]]
    d = datetime.strptime(data, "%Y-%m-%d")
    meta = f"{a['tempo_leitura']} de leitura · Publicado em {d.day} de {MESES[d.month-1]} de {d.year}"
    crumb = a.get("crumb") or a["titulo"]
    if len(crumb) > 40:
        crumb = crumb[:40].rsplit(" ", 1)[0] + "…"
    nav = "\n".join(
        f'            <a href="../categoria/{c}.html">{CATS[c]}</a>' for c in RELACIONADAS[cat])

    html = sub1(r"<title>.*?</title>", f"<title>{escape(a['titulo'])} — Saúde Auditiva</title>", html)
    html = sub1(r'<meta name="description" content="[^"]*">',
                f'<meta name="description" content="{escape(a["resumo"])}">\n'
                f'<link rel="canonical" href="https://saudeauditiva.pt/artigos/{a["slug"]}.html">\n'
                f'<meta property="og:type" content="article">\n'
                f'<meta property="og:title" content="{escape(a["titulo"])}">\n'
                f'<meta property="og:description" content="{escape(a["resumo"])}">\n'
                f'<meta property="og:url" content="https://saudeauditiva.pt/artigos/{a["slug"]}.html">\n'
                f'<meta property="og:locale" content="pt_PT">\n'
                f'<meta property="og:image" content="https://saudeauditiva.pt/img/artigos/{a["slug"]}.jpg">\n'
                f'<meta property="og:image:width" content="1080">\n'
                f'<meta property="og:image:height" content="1080">\n'
                f'<meta name="twitter:card" content="summary_large_image">', html)
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["titulo"],
          "description": a["resumo"], "datePublished": data, "inLanguage": "pt-PT",
          "articleSection": label,
          "author": {"@type": "Organization", "name": "Redacção Saúde Auditiva"},
          "publisher": {"@type": "Organization", "name": "Saúde Auditiva"},
          "mainEntityOfPage": f"https://saudeauditiva.pt/artigos/{a['slug']}.html"}
    html = sub1(r'(<link rel="stylesheet" href="\.\./styles\.css">)',
                '<link rel="stylesheet" href="../styles.css">\n<script type="application/ld+json">'
                + json.dumps(ld, ensure_ascii=False) + "</script>", html)
    html = sub1(r'<body data-page="[^"]*">', f'<body data-page="{cat}">', html)
    html = sub1(r'(<nav class="article-breadcrumb"[^>]*>).*?</nav>',
                '<nav class="article-breadcrumb" aria-label="Breadcrumb">\n'
                '            <a href="../index.html">Início</a> ·\n'
                f'            <a href="../categoria/{cat}.html">{label}</a> ·\n'
                f'            <span>{escape(crumb)}</span>\n          </nav>', html)
    html = sub1(r'<header class="article-header">.*?</header>',
                '<header class="article-header">\n'
                f'            <span class="kicker">{label}</span>\n'
                f'            <h1>{escape(a["titulo"])}</h1>\n'
                f'            <p class="dek">{escape(a["dek"])}</p>\n'
                f'            <div class="article-meta">{meta}</div>\n          </header>', html)
    html = sub1(r'(<div class="article-prose">).*?(</div>\s*</div>\s*<aside class="sidebar">)',
                '<div class="article-prose">\n\n' + a["corpo_html"].strip() + '\n\n          '
                '</div>\n\n        </div>\n\n        <aside class="sidebar">', html)
    html = sub1(r'(<div class="nav-cats">\s*<h5>Temas relacionados</h5>).*?(</div>)',
                '<div class="nav-cats">\n            <h5>Temas relacionados</h5>\n' + nav + '\n          </div>', html)
    html = html.replace(MOLDE_SLUG, a["slug"])
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ficheiro")
    ap.add_argument("--data", help="Data de publicação AAAA-MM-DD (por defeito, hoje)")
    args = ap.parse_args()

    a = json.loads(Path(args.ficheiro).read_text(encoding="utf-8"))
    for k in ("titulo", "categoria", "resumo", "dek", "corpo_html"):
        if not a.get(k):
            sys.exit(f"Falta o campo '{k}'")
    soc = a.get("social") or {}
    if not (soc.get("facebook") and soc.get("instagram") and soc.get("hashtags")):
        sys.exit("Falta o bloco 'social' (facebook, instagram, hashtags)")
    if a["categoria"] not in CATS:
        sys.exit(f"Categoria inválida: {a['categoria']}")
    a["slug"] = a.get("slug") or slugify(a["titulo"])
    a["tempo_leitura"] = tempo_leitura(a["corpo_html"])
    data = args.data or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    destino = ROOT / "artigos" / f"{a['slug']}.html"
    if destino.exists():
        sys.exit(f"Já existe: {destino.name}")
    imagem_artigo.gerar(a["slug"], CATS[a["categoria"]], a["titulo"], a["resumo"])
    destino.write_text(render(a, data), encoding="utf-8")

    lista_p = ROOT / "artigos.json"
    lista = json.loads(lista_p.read_text(encoding="utf-8"))
    lista.insert(0, {"slug": a["slug"], "titulo": a["titulo"], "categoria": a["categoria"],
                     "resumo": a["resumo"], "data": data, "tempo_leitura": a["tempo_leitura"],
                     "autor": "Redacção Saúde Auditiva",
                     "imagem": f"https://saudeauditiva.pt/img/artigos/{a['slug']}.jpg",
                     "social": {"facebook": soc["facebook"].strip(),
                                "instagram": soc["instagram"].strip(),
                                "hashtags": soc["hashtags"]}})
    lista_p.write_text(json.dumps(lista, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sm = ROOT / "sitemap.xml"
    s = sm.read_text(encoding="utf-8")
    url = f"https://saudeauditiva.pt/artigos/{a['slug']}.html"
    if url not in s:
        s = s.replace("</urlset>", f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{data}</lastmod>\n"
                      "    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n</urlset>")
        sm.write_text(s, encoding="utf-8")

    hist_p = ROOT / "data" / "history.json"
    hist = json.loads(hist_p.read_text(encoding="utf-8")) if hist_p.exists() else []
    hist.append({"topic_id": a.get("topic_id", ""), "slug": a["slug"], "titulo": a["titulo"],
                 "published_at": data})
    hist_p.write_text(json.dumps(hist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"OK artigos/{a['slug']}.html ({a['tempo_leitura']})")


if __name__ == "__main__":
    main()
