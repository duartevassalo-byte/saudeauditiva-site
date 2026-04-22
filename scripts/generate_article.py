#!/usr/bin/env python3
"""
Gerador de artigos para Saúde Auditiva.

Fluxo:
  1. Carregar tópicos e histórico
  2. Escolher tópico não usado nos últimos 90 dias
  3. Gerar artigo via Claude API
  4. Verificação factual via segundo prompt
  5. Se verificado → publicar (HTML + update artigos.json)
  6. Se não verificado → fila pending/ para revisão manual
  7. Gerar resumos para redes sociais
  8. Escrever logs

Variáveis de ambiente necessárias:
  ANTHROPIC_API_KEY — chave da API da Anthropic
  UNSPLASH_ACCESS_KEY — chave do Unsplash (opcional; fallback a placeholder)

Uso:
  python3 scripts/generate_article.py [--topic-id ID] [--dry-run]
"""

import argparse
import json
import os
import re
import sys
import hashlib
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib import request, parse, error

# ─────────────────────── Configuração ───────────────────────

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ARTIGOS_DIR = ROOT / "artigos"
PENDING_DIR = ROOT / "pending"
LOGS_DIR = ROOT / "logs"
ARTIGOS_JSON = ROOT / "artigos.json"
TOPICOS_JSON = DATA / "topicos.json"
HISTORY_JSON = DATA / "history.json"

for d in (DATA, ARTIGOS_DIR, PENDING_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

MODEL = "claude-sonnet-4-6"  # Modelo atual (Abril 2026). Para maior qualidade, mudar para "claude-opus-4-7" — mas cobra mais.
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# ─────────────────────── Utilitários ───────────────────────

def slugify(text: str) -> str:
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text[:80]

def log(msg: str, level: str = "INFO"):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{stamp}] {level}: {msg}"
    print(line, flush=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (LOGS_DIR / f"{today}.log").open("a", encoding="utf-8").write(line + "\n")

def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ─────────────────────── Anthropic API ───────────────────────

def call_claude(system: str, user: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY não definida no ambiente.")
    body = json.dumps({
        "model": MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [{"role": "user", "content": user}]
    }).encode("utf-8")
    req = request.Request(
        ANTHROPIC_URL,
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST"
    )
    try:
        with request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return "".join(block["text"] for block in data["content"] if block["type"] == "text")
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Anthropic HTTP {e.code}: {body}") from e

# ─────────────────────── Escolher tópico ───────────────────────

def pick_topic(specific_id: str | None = None) -> dict:
    data = load_json(TOPICOS_JSON, {"topicos": []})
    history = load_json(HISTORY_JSON, [])

    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    recent = {h["topic_id"] for h in history if h.get("published_at", "") > cutoff}

    topics = data["topicos"]
    if specific_id:
        for t in topics:
            if t["id"] == specific_id:
                return t
        raise ValueError(f"Tópico {specific_id} não encontrado.")

    # Pseudo-aleatório determinístico baseado no dia (dá previsibilidade e teste)
    today_seed = datetime.now(timezone.utc).strftime("%Y%m%d")
    eligible = [t for t in topics if t["id"] not in recent]
    if not eligible:
        log("Todos os tópicos foram usados nos últimos 90 dias — a reutilizar o mais antigo.", "WARN")
        eligible = sorted(topics, key=lambda t: next((h["published_at"] for h in history if h["topic_id"] == t["id"]), ""))

    idx = int(hashlib.sha256(today_seed.encode()).hexdigest(), 16) % len(eligible)
    return eligible[idx]

# ─────────────────────── Prompts ───────────────────────

SYSTEM_GENERATE = """És um jornalista especializado em saúde, escrevendo para um portal editorial português (Saúde Auditiva).

Regras OBRIGATÓRIAS:
- Português europeu (não brasileiro). Usa "facto" não "fato", "actualizado" não "atualizado", "electrónico" não "eletrônico", "tu/você" conforme contexto.
- Tom editorial sóbrio, informativo, não-comercial. Sem exageros. Sem linguagem de marketing.
- Baseia-te em evidência científica. Quando citares um dado, diz a fonte (OMS, Lancet, etc.).
- Se não tens certeza de um número específico, não inventes — diz "estudos indicam" ou omite.
- NUNCA dês conselho clínico específico. Usa linguagem como "pode ser", "em geral", "costuma".
- No final, recomenda consultar um profissional.
- NÃO uses listas com bullets excessivos. Prefere parágrafos de prosa.
- Comprimento: 700 a 1100 palavras.

Formato de saída OBRIGATÓRIO — JSON válido, nada mais:
{
  "titulo": "título final (máx 12 palavras, SEO-friendly)",
  "resumo": "dois frases que resumem (máx 200 caracteres)",
  "dek": "frase de subtítulo jornalístico (máx 220 caracteres)",
  "corpo_html": "corpo do artigo em HTML simples usando <p>, <h2>, <h3>, <ul><li>, <strong>, <em>. Inclui 3-5 secções com <h2>.",
  "keywords": ["3 a 6 palavras-chave relevantes"],
  "fontes_citadas": ["lista de fontes específicas mencionadas no texto: OMS, Lancet 2020, etc."]
}"""

SYSTEM_VERIFY = """És um verificador factual rigoroso de textos jornalísticos sobre saúde.

O teu trabalho é examinar um artigo e identificar:
1. Estatísticas ou números específicos — são plausíveis?
2. Citações de estudos ou organizações — são factualmente verdadeiras ou inventadas?
3. Afirmações clínicas que possam induzir em erro ou ser perigosas.
4. Afirmações sem fonte que deveriam ter uma.

Sê exigente mas justo: afirmações gerais e prudentes ("estudos indicam que...") são aceitáveis. Afirmações específicas ("um estudo de 2021 na Universidade X mostrou que 47,3% dos pacientes...") que não são verificáveis ou parecem inventadas devem ser sinalizadas.

Formato de saída OBRIGATÓRIO — JSON válido:
{
  "aprovado": true | false,
  "confianca": 0 a 100,
  "problemas": [
    {"tipo": "numero_suspeito|estudo_suspeito|afirmacao_clinica_perigosa|fonte_em_falta", "trecho": "parte do texto", "motivo": "explicação"}
  ],
  "nota_geral": "avaliação breve"
}

Aprova se confianca >= 75 E não houver problemas de tipo 'afirmacao_clinica_perigosa' ou 'estudo_suspeito'."""

SYSTEM_SOCIAL = """És um gestor de conteúdo de redes sociais de um portal sério de saúde em Portugal.

Gera posts para Facebook e Instagram. Regras:
- Português europeu, tom sóbrio, informativo, nada clickbait.
- Facebook: 2-4 parágrafos curtos, pode incluir pergunta retórica no fim. Até ~500 caracteres.
- Instagram: caption até ~300 caracteres + 5-8 hashtags relevantes. Linguagem acessível mas não infantil.
- NUNCA afirmes diagnósticos. Remete para o artigo para saber mais.
- Inclui chamada implícita à acção ("lê mais", "saber como") mas sem exclamações.

Formato de saída OBRIGATÓRIO — JSON:
{
  "facebook": "texto completo do post do Facebook",
  "instagram": "caption do Instagram (sem hashtags)",
  "hashtags": ["5 a 8 hashtags começadas por #"]
}"""

# ─────────────────────── Geração ───────────────────────

def generate_article(topic: dict) -> dict:
    user_prompt = f"""Gera um artigo sobre:

Tópico: {topic['titulo_base']}
Categoria: {topic['categoria']}
Ângulo editorial: {topic['angulo']}
Palavras-chave SEO: {', '.join(topic.get('palavras_chave', []))}
Público principal: {topic.get('publico', 'geral')}
Tom: {topic.get('tom', 'informativo')}

Escreve o artigo e devolve-o no formato JSON especificado."""
    raw = call_claude(SYSTEM_GENERATE, user_prompt, max_tokens=6000, temperature=0.7)
    return parse_json_safe(raw, "geração do artigo")

def verify_article(article: dict) -> dict:
    # Extrai texto plano para verificação
    text = f"TÍTULO: {article['titulo']}\n\nRESUMO: {article['resumo']}\n\nCORPO:\n{strip_html(article['corpo_html'])}"
    user_prompt = f"Verifica factualmente o seguinte artigo:\n\n{text}"
    raw = call_claude(SYSTEM_VERIFY, user_prompt, max_tokens=2000, temperature=0.2)
    return parse_json_safe(raw, "verificação factual")

def generate_social(article: dict, url: str) -> dict:
    user_prompt = f"""Artigo publicado:
TÍTULO: {article['titulo']}
RESUMO: {article['resumo']}
URL: {url}

Gera posts adaptados para Facebook e Instagram."""
    raw = call_claude(SYSTEM_SOCIAL, user_prompt, max_tokens=1500, temperature=0.6)
    return parse_json_safe(raw, "geração de posts")

# ─────────────────────── Helpers ───────────────────────

def parse_json_safe(raw: str, context: str) -> dict:
    # Remover possíveis code fences
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Tentar extrair primeiro bloco JSON
        m = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise RuntimeError(f"Resposta não-JSON válida em {context}: {raw[:300]}...")

def strip_html(html: str) -> str:
    return re.sub(r'<[^>]+>', ' ', html).replace('&nbsp;', ' ')

def estimate_reading_time(html: str) -> str:
    words = len(strip_html(html).split())
    minutes = max(1, round(words / 200))
    return f"{minutes} min"

# ─────────────────────── Imagens (Unsplash + fallback) ───────────────────────

def fetch_cover_image(keywords: list, slug: str) -> dict:
    """Tenta buscar imagem no Unsplash; se falhar, devolve placeholder neutro."""
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if key:
        try:
            query = " ".join(keywords[:2]) or "hearing"
            qs = parse.urlencode({"query": query, "orientation": "landscape", "per_page": 1, "content_filter": "high"})
            req = request.Request(
                f"https://api.unsplash.com/search/photos?{qs}",
                headers={"Authorization": f"Client-ID {key}"}
            )
            with request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            if data.get("results"):
                r = data["results"][0]
                return {
                    "url": r["urls"]["regular"],
                    "alt": r.get("alt_description") or "Imagem ilustrativa",
                    "credit": f'Foto de {r["user"]["name"]} no Unsplash',
                    "credit_url": r["user"]["links"]["html"]
                }
        except Exception as e:
            log(f"Unsplash falhou: {e}", "WARN")

    # Fallback: placeholder SVG neutro com as cores do site
    return {
        "url": "",
        "alt": "",
        "credit": "",
        "credit_url": "",
        "is_placeholder": True
    }

# ─────────────────────── Render HTML do artigo ───────────────────────

def render_article_html(article: dict, topic: dict, cover: dict, publish_date: str, reading_time: str) -> str:
    from html import escape as e
    cat_labels = {
        "perda-auditiva": "Perda Auditiva",
        "sinais-alerta": "Sinais de Alerta",
        "prevencao": "Prevenção",
        "familia": "Família",
        "aparelhos": "Aparelhos"
    }
    cat_label = cat_labels.get(topic["categoria"], topic["categoria"])

    cover_block = ""
    if cover.get("url"):
        cover_block = f"""
          <figure class="cover-figure">
            <img src="{e(cover['url'])}" alt="{e(cover['alt'])}">
            <figcaption>{e(cover['credit'])}</figcaption>
          </figure>"""

    disclaimer = """
      <aside class="ai-disclaimer">
        <strong>Nota editorial</strong>
        <p>Este artigo foi produzido com recurso a inteligência artificial, revisto contra fontes científicas reconhecidas e publicado sob responsabilidade editorial da Penguin Style Lda. Não substitui aconselhamento médico ou audiológico profissional. Para qualquer decisão clínica, consulte um especialista.</p>
      </aside>"""

    return f"""<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{e(article['titulo'])} — Saúde Auditiva</title>
  <meta name="description" content="{e(article['resumo'])}">
  <meta property="og:title" content="{e(article['titulo'])}">
  <meta property="og:description" content="{e(article['resumo'])}">
  <meta property="og:type" content="article">
  <meta property="og:locale" content="pt_PT">
  {f'<meta property="og:image" content="{e(cover["url"])}">' if cover.get('url') else ''}
  <meta name="keywords" content="{e(', '.join(article.get('keywords', [])))}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Libre+Franklin:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../styles.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": {json.dumps(article['titulo'], ensure_ascii=False)},
    "description": {json.dumps(article['resumo'], ensure_ascii=False)},
    "datePublished": "{publish_date}",
    "author": {{"@type": "Organization", "name": "Saúde Auditiva"}},
    "publisher": {{"@type": "Organization", "name": "Penguin Style Lda"}},
    "articleSection": "{cat_label}"
  }}
  </script>
</head>
<body data-page="{topic['categoria']}">

  <div id="slot-topbar"></div>
  <div id="slot-header"></div>

  <main>
    <article class="article-full">
      <div class="container container-narrow">
        <div class="breadcrumb article-breadcrumb">
          <a href="../index.html">Início</a> ·
          <a href="../categoria/{topic['categoria']}.html">{cat_label}</a> ·
          <span>Artigo</span>
        </div>

        <header class="article-header">
          <span class="kicker">{cat_label}</span>
          <h1>{e(article['titulo'])}</h1>
          <p class="dek">{e(article.get('dek', article['resumo']))}</p>
          <div class="article-meta">
            <span>Saúde Auditiva</span> · <span>{publish_date}</span> · <span>{reading_time} de leitura</span>
          </div>
        </header>
        {cover_block}

        <div class="article-prose prose">
          {article['corpo_html']}
        </div>

        {disclaimer}

        <aside class="article-cta">
          <h3>Avaliação auditiva gratuita</h3>
          <p>Se este artigo levantou dúvidas sobre a sua audição, uma consulta de avaliação gratuita — sem compromisso — pode esclarecer em 30 minutos.</p>
          <a href="#" class="btn btn-primary" data-open-booking>Marcar consulta →</a>
        </aside>
      </div>
    </article>
  </main>

  <div id="slot-footer"></div>
  <div id="slot-modal"></div>

  <script src="../partials.js" data-root="../"></script>
  <script src="../script.js"></script>
</body>
</html>
"""

# ─────────────────────── Fluxo principal ───────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic-id", help="Forçar um tópico específico")
    ap.add_argument("--dry-run", action="store_true", help="Não escreve ficheiros nem actualiza histórico")
    args = ap.parse_args()

    log("Iniciando geração de artigo.")
    topic = pick_topic(args.topic_id)
    log(f"Tópico escolhido: {topic['id']} — {topic['titulo_base']}")

    log("A gerar artigo…")
    article = generate_article(topic)
    log(f"Artigo gerado: {article['titulo']} ({len(strip_html(article['corpo_html']).split())} palavras)")

    log("A verificar factualmente…")
    verification = verify_article(article)
    log(f"Verificação: aprovado={verification['aprovado']} confiança={verification['confianca']}")

    slug = slugify(article['titulo'])
    publish_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Decidir destino
    if verification["aprovado"]:
        log("APROVADO — a publicar.")
        cover = fetch_cover_image(article.get("keywords", []), slug)
        article_path = ARTIGOS_DIR / f"{slug}.html"
        html = render_article_html(article, topic, cover, publish_date, estimate_reading_time(article['corpo_html']))

        if args.dry_run:
            log(f"[dry-run] seria escrito {article_path}")
        else:
            article_path.write_text(html, encoding="utf-8")

            # Actualizar artigos.json
            artigos = load_json(ARTIGOS_JSON, [])
            # Remover eventual entrada anterior com mesmo slug
            artigos = [a for a in artigos if a.get("slug") != slug]
            artigos.insert(0, {
                "slug": slug,
                "titulo": article["titulo"],
                "categoria": topic["categoria"],
                "resumo": article["resumo"],
                "data": publish_date,
                "tempo_leitura": estimate_reading_time(article['corpo_html']),
                "autor": "Saúde Auditiva",
                "generated": True
            })
            save_json(ARTIGOS_JSON, artigos)

            # Actualizar histórico
            history = load_json(HISTORY_JSON, [])
            history.append({
                "topic_id": topic["id"],
                "slug": slug,
                "titulo": article["titulo"],
                "published_at": datetime.now(timezone.utc).isoformat(),
                "verification_confidence": verification["confianca"],
                "keywords": article.get("keywords", []),
                "cover": cover
            })
            save_json(HISTORY_JSON, history)

            # Gerar posts para redes sociais (passados ao passo seguinte do workflow via ficheiro)
            url = f"https://saudeauditiva.pt/artigos/{slug}.html"
            try:
                social = generate_social(article, url)
                social_file = DATA / "pending_social.json"
                pending = load_json(social_file, [])
                pending.append({
                    "slug": slug,
                    "url": url,
                    "titulo": article["titulo"],
                    "facebook": social["facebook"],
                    "instagram": social["instagram"],
                    "hashtags": social["hashtags"],
                    "cover_url": cover.get("url", ""),
                    "generated_at": datetime.now(timezone.utc).isoformat()
                })
                save_json(social_file, pending)
                log(f"Posts sociais preparados: {social_file}")
            except Exception as ex:
                log(f"Falha a gerar posts sociais (artigo publicado na mesma): {ex}", "WARN")

            log(f"Artigo publicado: artigos/{slug}.html")
    else:
        log("NÃO APROVADO — a arquivar para revisão manual.", "WARN")
        if not args.dry_run:
            pending_path = PENDING_DIR / f"{publish_date}-{slug}.json"
            pending_path.write_text(json.dumps({
                "topic": topic,
                "article": article,
                "verification": verification,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            log(f"Guardado em {pending_path}")

    log("Concluído.")

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        log(f"ERRO FATAL: {ex}", "ERROR")
        sys.exit(1)
