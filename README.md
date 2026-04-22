# Saúde Auditiva

Portal editorial independente sobre saúde auditiva em Portugal, com sistema automático de geração e publicação de artigos.

**Em produção:** [saudeauditiva.pt](https://saudeauditiva.pt)
**Operado por:** Penguin Style Lda · NIPC 515167657

---

## Estrutura do projeto

```
/
├── Site público (servido pelo GitHub Pages)
│   ├── index.html, sobre.html, contacto.html, privacidade.html, termos.html
│   ├── categoria/*.html            # Páginas de cada categoria
│   ├── artigos/*.html              # Artigos individuais (gerados automaticamente)
│   ├── styles.css, script.js, partials.js
│   ├── artigos.json                # Índice de artigos (atualizado pelo bot)
│   ├── sitemap.xml, robots.txt, CNAME, .nojekyll
│
├── Painel de administração
│   └── admin/index.html            # Protegido por password
│
├── Automação
│   ├── .github/workflows/
│   │   ├── daily-article.yml       # Agendamento diário + disparo manual
│   │   └── retry-social.yml        # Retry de publicação social
│   ├── scripts/
│   │   ├── generate_article.py     # Gera artigo, verifica, publica
│   │   └── publish_social.py       # Publica em Facebook + Instagram
│   ├── data/
│   │   ├── topicos.json            # Lista mestra de tópicos a escrever sobre
│   │   ├── history.json            # Histórico de tópicos já escritos
│   │   ├── pending_social.json     # Fila de posts para publicar
│   │   └── social_history.json     # Histórico de publicações sociais
│   ├── pending/                    # Artigos não aprovados (revisão manual)
│   └── logs/                       # Logs de execução
│
└── Documentação
    ├── README.md                   # Este ficheiro
    └── SETUP.md                    # Guia de configuração passo a passo
```

---

## Arquitetura

```
                    GitHub Actions (cron: 08:30 UTC diário)
                              │
                              ▼
                    ┌─────────────────────────────┐
                    │   generate_article.py       │
                    │   1. Escolhe tópico         │
                    │   2. Gera (Claude API)      │
                    │   3. Verifica (Claude API)  │
                    │   4. Busca imagem (Unsplash)│
                    │   5. Escreve HTML + JSON    │
                    │   6. Prepara posts sociais  │
                    └──────────────┬──────────────┘
                                   │
                          Aprovado │ Não aprovado
                                   │         │
                                   ▼         ▼
                    ┌──────────────────┐  ┌────────────────┐
                    │ Commit ao repo   │  │ Arquiva em     │
                    │ (artigo + index) │  │ pending/ para  │
                    └────────┬─────────┘  │ revisão manual │
                             │            └────────────────┘
                             ▼
                    ┌─────────────────────────────┐
                    │   publish_social.py          │
                    │   - Facebook (Graph API)    │
                    │   - Instagram (Graph API)   │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    Posts publicados nas redes sociais
                    Site público actualizado em saudeauditiva.pt
```

---

## Como começar

Se é a primeira vez que abres este projeto, lê o **[SETUP.md](SETUP.md)** — é um guia passo a passo completo, com tempos estimados e pontos de verificação.

Não saltes passos. A ordem importa.

---

## Quotidiano: como funciona

Depois de configurado, o sistema funciona sozinho:

**Todos os dias às 08:30 UTC** o GitHub Actions:
1. Escolhe um tópico não usado nos últimos 90 dias
2. Gera um artigo (~900 palavras, português europeu)
3. Verifica-o factualmente (segundo modelo IA)
4. Se aprovado, publica. Se não, arquiva para revisão manual.
5. Busca uma imagem de capa (Unsplash)
6. Cria posts adaptados para Facebook e Instagram
7. Publica nas redes sociais
8. Commit automático ao repositório

**Três vezes por dia** (12:00, 16:00 e 20:00 UTC) há um retry de publicação social, caso a Meta tenha falhado à primeira.

**Sempre** podes ir ao painel admin em `/admin/` para ver o estado.

---

## Intervir manualmente

### Forçar publicação agora

GitHub → Actions → `Geração diária de artigo` → `Run workflow`.

### Forçar um tópico específico

Mesmo sítio, mas preenche o campo `topic_id` (ex: `pa-005`). A lista de tópicos está em `data/topicos.json`.

### Ver o que está na fila de revisão manual

Os artigos que o verificador factual rejeitou ficam em `pending/`. Abre o ficheiro JSON respectivo, vê o que foi escrito e o motivo da rejeição, e decide o que fazer (editar à mão e publicar, ou descartar).

### Editar o artigo fixo da homepage

Fica em `index.html`, secção `<section class="featured-article">`. Edita o HTML directamente.

### Adicionar tópicos novos

Edita `data/topicos.json`. Cada entrada segue este esquema:

```json
{
  "id": "identificador único",
  "titulo_base": "título orientador",
  "categoria": "perda-auditiva | sinais-alerta | prevencao | familia | aparelhos",
  "angulo": "perspectiva específica",
  "palavras_chave": ["palavras-chave SEO"],
  "publico": "a quem se dirige",
  "tom": "informativo | urgente | tranquilizador | pedagógico"
}
```

---

## Manutenção

### O que precisa da tua atenção

- **Tokens da Meta expiram a cada ~60 dias.** Ver secção "Manutenção regular" no SETUP.md.
- **Crédito Anthropic esgota-se.** A Anthropic avisa por email antes de chegar a zero.
- **Revisões manuais em `pending/`.** Vê uma vez por semana no início.

### O que NÃO precisa da tua atenção

- Site estático (zero manutenção)
- GitHub Actions (self-healing; se falhar, tenta outra vez)
- `history.json`, `artigos.json` (geridos pelo bot)

---

## Tom editorial e limites

- **Português europeu** (sempre; os prompts obrigam a isso)
- **Sem conselho clínico específico** (os prompts impedem)
- **Sem nomes inventados** (o conteúdo é assinado como "Saúde Auditiva")
- **Disclaimer de IA em cada artigo** (cumpre AI Act)
- **Sem recomendações de marcas específicas** de aparelhos
- **Fontes científicas citadas** quando aplicável

---

## Contacto

- Questões técnicas: abrir issue no GitHub
- Questões editoriais: editorial@saudeauditiva.pt
- Questões de privacidade: privacidade@saudeauditiva.pt
- Questões gerais: geral@saudeauditiva.pt

---

## Licença e propriedade

© Penguin Style Lda. Todos os direitos reservados.

O código deste repositório é propriedade da Penguin Style Lda e não está licenciado para uso ou redistribuição por terceiros sem autorização escrita.

O conteúdo editorial publicado em `saudeauditiva.pt` segue os termos indicados em [termos.html](termos.html).
