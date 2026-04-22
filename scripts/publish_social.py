#!/usr/bin/env python3
"""
Publica no Facebook e Instagram os posts preparados por generate_article.py.

Lê data/pending_social.json e para cada entrada:
  1. Publica no Facebook (página) com link + texto
  2. Publica no Instagram com imagem + caption + hashtags
  3. Regista em data/social_history.json
  4. Remove da fila pendente

Variáveis de ambiente necessárias:
  META_PAGE_ID            — ID da página Facebook
  META_PAGE_ACCESS_TOKEN  — token de longa duração da página (com scopes: pages_manage_posts, pages_read_engagement)
  META_IG_USER_ID         — ID da conta Instagram (IG User, não Business Account ID)

Instagram requer URL pública da imagem (não base64). Por isso, se o artigo não tem imagem, o post de Instagram é saltado (Instagram exige sempre media).

Uso:
  python3 scripts/publish_social.py [--dry-run]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, parse, error

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LOGS_DIR = ROOT / "logs"
PENDING_FILE = DATA / "pending_social.json"
HISTORY_FILE = DATA / "social_history.json"

GRAPH_VERSION = "v25.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

for d in (DATA, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

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

def http_post(url: str, data: dict) -> dict:
    body = parse.urlencode(data).encode("utf-8")
    req = request.Request(url, data=body, method="POST")
    try:
        with request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}") from e

def http_get(url: str) -> dict:
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}") from e

# ─────────────────────── Facebook ───────────────────────

def publish_facebook(page_id: str, token: str, message: str, link: str) -> dict:
    """Publica um post com link na página."""
    url = f"{GRAPH_BASE}/{page_id}/feed"
    return http_post(url, {
        "message": message,
        "link": link,
        "access_token": token
    })

# ─────────────────────── Instagram ───────────────────────

def publish_instagram(ig_user_id: str, token: str, caption: str, image_url: str) -> dict:
    """Fluxo Instagram em dois passos: criar container, depois publicar."""
    # Passo 1: criar media container
    container_url = f"{GRAPH_BASE}/{ig_user_id}/media"
    container = http_post(container_url, {
        "image_url": image_url,
        "caption": caption,
        "access_token": token
    })
    if "id" not in container:
        raise RuntimeError(f"Falha a criar container: {container}")
    container_id = container["id"]

    # Passo 2: aguardar processamento (IG às vezes demora alguns segundos)
    for attempt in range(10):
        status = http_get(f"{GRAPH_BASE}/{container_id}?fields=status_code&access_token={parse.quote(token)}")
        code = status.get("status_code", "")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"Container com erro: {status}")
        time.sleep(3)
    else:
        raise RuntimeError("Container não ficou pronto em 30s.")

    # Passo 3: publicar
    publish_url = f"{GRAPH_BASE}/{ig_user_id}/media_publish"
    return http_post(publish_url, {
        "creation_id": container_id,
        "access_token": token
    })

# ─────────────────────── Main ───────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    page_id = os.environ.get("META_PAGE_ID")
    page_token = os.environ.get("META_PAGE_ACCESS_TOKEN")
    ig_user = os.environ.get("META_IG_USER_ID")

    if not page_id or not page_token:
        log("META_PAGE_ID ou META_PAGE_ACCESS_TOKEN em falta — a saltar Facebook.", "WARN")
    if not ig_user:
        log("META_IG_USER_ID em falta — a saltar Instagram.", "WARN")

    pending = load_json(PENDING_FILE, [])
    if not pending:
        log("Nada na fila de publicação social.")
        return

    remaining = []
    history = load_json(HISTORY_FILE, [])

    for item in pending:
        log(f"A publicar: {item['titulo']}")
        record = {
            "slug": item["slug"],
            "url": item["url"],
            "titulo": item["titulo"],
            "attempted_at": datetime.now(timezone.utc).isoformat(),
            "facebook": None,
            "instagram": None,
        }

        # Facebook
        if page_id and page_token:
            try:
                msg_fb = f"{item['facebook']}\n\n{item['url']}"
                if args.dry_run:
                    log(f"[dry-run] Facebook: {msg_fb[:80]}...")
                    record["facebook"] = {"status": "dry_run"}
                else:
                    res = publish_facebook(page_id, page_token, msg_fb, item["url"])
                    record["facebook"] = {"status": "ok", "id": res.get("id", "")}
                    log(f"Facebook publicado: {res.get('id', '?')}")
            except Exception as ex:
                log(f"Facebook falhou: {ex}", "ERROR")
                record["facebook"] = {"status": "error", "message": str(ex)}

        # Instagram (requer imagem)
        if ig_user and page_token:
            if not item.get("cover_url"):
                log("Sem cover_url — a saltar Instagram.", "WARN")
                record["instagram"] = {"status": "skipped_no_image"}
            else:
                caption = f"{item['instagram']}\n\n{' '.join(item['hashtags'])}"
                try:
                    if args.dry_run:
                        log(f"[dry-run] Instagram: {caption[:80]}...")
                        record["instagram"] = {"status": "dry_run"}
                    else:
                        res = publish_instagram(ig_user, page_token, caption, item["cover_url"])
                        record["instagram"] = {"status": "ok", "id": res.get("id", "")}
                        log(f"Instagram publicado: {res.get('id', '?')}")
                except Exception as ex:
                    log(f"Instagram falhou: {ex}", "ERROR")
                    record["instagram"] = {"status": "error", "message": str(ex)}

        history.append(record)

        # Se alguma das redes falhou de forma recuperável, mantemos em fila
        fb_ok = not record["facebook"] or record["facebook"].get("status") in ("ok", "dry_run")
        ig_ok = not record["instagram"] or record["instagram"].get("status") in ("ok", "dry_run", "skipped_no_image")
        if not (fb_ok and ig_ok):
            log(f"A manter em fila para próxima tentativa: {item['slug']}", "WARN")
            remaining.append(item)

    if not args.dry_run:
        save_json(PENDING_FILE, remaining)
        save_json(HISTORY_FILE, history)

    log(f"Concluído. {len(pending) - len(remaining)} publicado(s), {len(remaining)} em fila.")

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        log(f"ERRO FATAL: {ex}", "ERROR")
        sys.exit(1)
