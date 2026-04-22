# Guia de Configuração — Saúde Auditiva Automation

Este documento leva-te do zero até ter o sistema de geração automática e publicação em redes sociais a funcionar. Segue pela ordem que aqui está — cada passo depende do anterior.

**Tempo estimado total:** 2 a 4 horas, distribuídas ao longo de 1–2 dias (porque alguns passos envolvem aprovações da Meta que não são instantâneas).

---

## Antes de começar

Preciso que tenhas:

- [ ] Acesso à conta de GitHub onde está o repositório `duartevassalo-byte/Saude-Auditiva`
- [ ] Acesso à conta Meta Business que administra a página Facebook e a conta Instagram da marca
- [ ] Um cartão de crédito para adicionar saldo à conta Anthropic (~20-30€ para começar)
- [ ] 2-4 horas livres sem interrupções grandes

---

## Parte 1 — Pôr o site online (fundação)

**1.1** Descomprime o zip que te entreguei.

**1.2** No teu repositório GitHub, apaga os ficheiros antigos e faz upload dos novos (excepto a pasta `scripts/`, `pending/`, `data/` e `.github/` nesta primeira fase — vamos adicionar depois). Para já queremos só o site a funcionar, sem automação.

Ficheiros a colocar na raiz do repo:
- `index.html`, `sobre.html`, `contacto.html`, `privacidade.html`, `termos.html`
- `styles.css`, `script.js`, `partials.js`
- `artigos.json`, `sitemap.xml`, `robots.txt`
- `CNAME`, `.nojekyll`, `README.md`
- Pasta `categoria/` com todos os seus ficheiros
- Pasta `admin/` com o `index.html`
- Pasta `artigos/` (vazia por agora; vai ser preenchida automaticamente)

**1.3** Commit e push para `main`.

**1.4** Em `Settings → Pages`, confirma:
- Source: `Deploy from a branch`
- Branch: `main` / `/ (root)`
- Custom domain: `saudeauditiva.pt`

Aguarda 1-2 minutos. Verifica em `https://saudeauditiva.pt` que o site novo está lá. Se algo estiver partido, pára e corrige antes de continuar.

**Checkpoint:** site novo visível em `saudeauditiva.pt`. Painel admin em `https://saudeauditiva.pt/admin/` deve pedir password (tenta `admin2026` — vais mudar já a seguir).

---

## Parte 2 — Mudar a password do painel admin

**Muito importante fazer isto agora**, antes de adicionar mais coisas.

**2.1** Escolhe uma password forte (mínimo 12 caracteres, inclui letras, números e símbolos). Anota-a num gestor de passwords.

**2.2** Gera o hash SHA-256 da tua password:

**No Mac/Linux:**
```bash
echo -n "tua-password-aqui" | sha256sum
```

**No Windows (PowerShell):**
```powershell
$stringToHash = "tua-password-aqui"
$stringAsStream = [System.IO.MemoryStream]::new()
$writer = [System.IO.StreamWriter]::new($stringAsStream)
$writer.write($stringToHash)
$writer.Flush()
$stringAsStream.Position = 0
(Get-FileHash -InputStream $stringAsStream -Algorithm SHA256).Hash.ToLower()
```

**Alternativa online (seguro porque é só hash):** https://emn178.github.io/online-tools/sha256.html

**2.3** Copia o hash (longa string hex de 64 caracteres).

**2.4** No GitHub, vai a `admin/index.html`, clica no ícone do lápis (editar), e procura a linha:
```javascript
const PASSWORD_HASH = "6051fc84a7a0d74c225fb18a496b09952da5642e60723ecae543298edd7d82d6";
```

Substitui o valor pela tua hash. Commit.

**2.5** Aguarda 1 minuto e testa em `https://saudeauditiva.pt/admin/` — agora a password antiga deve falhar e a nova deve funcionar.

---

## Parte 3 — API da Anthropic (gerador de artigos)

**3.1** Vai a https://console.anthropic.com e cria conta (ou faz login se já tens).

**3.2** Em `Billing` (no menu), adiciona um método de pagamento e põe **30€ de crédito inicial**. Isto chega para ~3-6 meses a 1 artigo/dia.

**3.3** Em `API Keys`, clica em `Create Key`. Nomeia-a `saude-auditiva-prod`. Copia-a imediatamente (começa por `sk-ant-`). Guarda num sítio seguro — não vais poder ver de novo.

**3.4** Deixa esta tab aberta. Vais precisar da chave daqui a pouco.

---

## Parte 4 — API Unsplash (imagens de capa, opcional mas recomendado)

**4.1** Vai a https://unsplash.com/developers e faz login (ou cria conta gratuita).

**4.2** Clica em `Your apps → New Application`. Aceita os termos.

**4.3** Dá nome à app (`Saúde Auditiva`) e descrição breve. Cria.

**4.4** Copia o `Access Key` (na página da app). Guarda.

O plano gratuito do Unsplash dá 50 pedidos por hora — muito mais do que precisas.

---

## Parte 5 — Meta App para Facebook e Instagram (a parte mais longa)

Esta é a parte que leva mais tempo. **Prepara-te para 1-2 horas**, e nota que algumas aprovações podem não ser imediatas.

### 5.1 — Preparação

Antes de começar, confirma:
- [ ] A tua página Facebook do Saúde Auditiva existe e tu és admin
- [ ] A tua conta Instagram é do tipo **Business** ou **Creator** (não pessoal)
- [ ] A conta Instagram está **ligada à página Facebook** (em Instagram → Configurações → Conta → Contas ligadas)

Se algum destes não estiver correcto, pára aqui e resolve primeiro. O resto não funciona sem isto.

### 5.2 — Criar app no Meta for Developers

**a)** Vai a https://developers.facebook.com e faz login com a conta que administra a página.

**b)** Clica em `My Apps → Create App`.

**c)** Escolhe `Other` como tipo de app quando perguntar.

**d)** Escolhe `Business` como tipo de uso.

**e)** Dá nome à app: `Saude Auditiva Publisher`. Email de contacto: o teu. Business Account: escolhe a tua conta Meta Business.

**f)** A app é criada. Guarda o `App ID` e o `App Secret` (em `Settings → Basic`).

### 5.3 — Adicionar produtos necessários

No dashboard da app:

**a)** Adiciona o produto `Facebook Login for Business`. Só precisas de clicar "Set up".

**b)** Adiciona o produto `Instagram`. Clica "Set up".

### 5.4 — Obter o Page ID

**a)** Vai à tua página Facebook → `About` (Sobre).

**b)** Procura `Page ID` (no fundo da página ou em "Transparência da página"). Copia o número.

### 5.5 — Obter o Instagram User ID

**a)** No Graph API Explorer (https://developers.facebook.com/tools/explorer/), seleciona a tua app no dropdown "Meta App".

**b)** Em "User or Page", escolhe a tua página Facebook.

**c)** Clica em `Get Token → Get Page Access Token`. Aceita todas as permissões pedidas.

**d)** No campo da query, cola:
```
me?fields=instagram_business_account{id,username}
```

**e)** Clica `Submit`. Vais ver algo como:
```json
{
  "instagram_business_account": {
    "id": "17841400008460056",
    "username": "saudeauditivapt"
  }
}
```

**f)** Copia o `id` — é o teu **Instagram User ID**.

### 5.6 — Obter Page Access Token de longa duração

Os tokens de curta duração expiram em 1-2 horas. Queremos um que dure ~60 dias.

**a)** Ainda no Graph API Explorer, com o Page Access Token (do passo 5.5.c), clica em `i` junto ao token e depois em `Open in Access Token Tool`.

**b)** Na Access Token Tool, clica em `Extend Access Token`. Isto converte-o em token de longa duração.

**c)** Copia o novo token. Guarda-o num sítio seguro.

**Importante:** estes tokens têm que ser renovados periodicamente (a cada ~60 dias). Vou explicar como mais à frente.

### 5.7 — Permissões necessárias

Quando pediste o token, confirma que tem estas permissões:
- `pages_show_list`
- `pages_read_engagement`
- `pages_manage_posts`
- `instagram_basic`
- `instagram_content_publish`
- `business_management`

Se faltar alguma, volta ao Explorer, clica em `Get Token` e adiciona-as.

### 5.8 — App Review (pode ser necessária)

Para publicação em produção, a Meta pode requerer que submetas a app para revisão. **Para começar, tokens de utilizador autenticados funcionam em modo "Development" da app sem precisar de revisão, mas só a conta do admin pode usar as APIs.**

Como és tu o admin e só publicas na tua própria página, isto chega. Se no futuro quiseres que um colega possa disparar publicação, aí sim precisarás de submeter para App Review.

---

## Parte 6 — Adicionar secrets ao GitHub

Todas as chaves que obtiveste acima têm de ser guardadas no GitHub de forma que os workflows as possam usar, mas não sejam visíveis a ninguém que olhe para o código.

**6.1** Vai ao repositório no GitHub → `Settings → Secrets and variables → Actions`.

**6.2** Clica em `New repository secret`. Adiciona um de cada vez:

| Nome do Secret | Valor |
|---|---|
| `ANTHROPIC_API_KEY` | a chave que começa por `sk-ant-` |
| `UNSPLASH_ACCESS_KEY` | a Access Key do Unsplash |
| `META_PAGE_ID` | o Page ID numérico |
| `META_PAGE_ACCESS_TOKEN` | o Page Access Token de longa duração |
| `META_IG_USER_ID` | o Instagram User ID numérico |

**6.3** Verifica que todos estão lá, com as chaves corretas (os valores ficam ocultos, é normal).

---

## Parte 7 — Adicionar os scripts e workflows

Agora que os secrets existem, podemos adicionar o código que os usa.

**7.1** No repositório, faz upload das pastas:
- `.github/` (contém os workflows)
- `scripts/` (contém os Python scripts)
- `data/` (contém `topicos.json`)
- `templates/` (se houver)

**7.2** Cria uma pasta vazia `pending/` na raiz com um ficheiro `.gitkeep` dentro (para o Git a "ver").

**7.3** Commit e push.

---

## Parte 8 — Primeiro teste (em modo simulação)

Antes de publicar a sério, testa em `dry-run`.

**8.1** No GitHub, vai a `Actions`.

**8.2** Clica em `Geração diária de artigo` na barra lateral.

**8.3** Clica em `Run workflow`. Preenche:
- `topic_id`: deixa vazio (ou tenta `pa-001` para forçar um específico)
- `dry_run`: **true** ✅

**8.4** Clica em `Run workflow` (o verde).

**8.5** Aguarda 1-2 minutos. Abre a run que aparece em execução. Vê os logs.

**Se tudo correr bem:** vais ver "Artigo gerado: ...", "Verificação: aprovado=true", e logs de um ficheiro que seria escrito (mas não foi, porque é dry-run).

**Se falhar:** lê o erro. Os mais comuns:
- `ANTHROPIC_API_KEY não definida` → o secret não foi adicionado ou está com nome errado
- `Anthropic HTTP 401` → chave inválida, gera outra
- `Anthropic HTTP 529` → overloaded, tenta outra vez em alguns minutos

---

## Parte 9 — Primeira publicação real

**9.1** Repete o passo 8 mas com `dry_run: false` (ou deixa em branco, que é o default).

**9.2** Aguarda o workflow. Se tudo correr bem:
- O repositório tem um novo commit automático com um artigo em `artigos/*.html`
- O `artigos.json` foi actualizado
- O Facebook e Instagram têm posts novos (verifica nas tuas páginas)

**9.3** Vai ao site: `https://saudeauditiva.pt` — o novo artigo deve aparecer nas listas.

**9.4** Vai ao painel admin: `https://saudeauditiva.pt/admin/` — o artigo deve estar lá nas estatísticas.

---

## Parte 10 — Activar o agendamento diário

Depois de confirmares que uma publicação manual corre bem, o workflow `.github/workflows/daily-article.yml` vai disparar automaticamente todos os dias às 08:30 UTC (09:30 Lisboa no horário de inverno, 10:30 no horário de verão).

Para mudar a hora, edita a linha `- cron: "30 8 * * *"` no workflow. O formato cron é: `minutos horas dia-mês mês dia-semana`. Sempre em UTC.

---

## Manutenção regular

### Tokens da Meta expiram

Os Page Access Tokens de longa duração duram cerca de 60 dias. Antes de expirarem, vais perder a capacidade de publicar em Facebook/Instagram.

**Como detectar:** o painel admin mostra posts falhados. Os logs do workflow mostram `HTTP 401` nas chamadas a `graph.facebook.com`.

**Como renovar:** repete os passos 5.5 e 5.6 (gerar novo token de longa duração) e actualiza o secret `META_PAGE_ACCESS_TOKEN` no GitHub.

Podes automatizar a renovação (a Meta tem fluxo de refresh), mas inicialmente é mais simples fazer manualmente a cada 2 meses.

### Crédito Anthropic

Quando o saldo estiver a esgotar, a Anthropic avisa por email. 1 artigo/dia com verificação gasta cerca de 5-10€/mês.

### Monitorização

Recomendo ver o painel admin uma vez por semana no início. Procurar:
- Artigos em `pending/` que precisam de revisão manual (texto que o verificador não aprovou)
- Posts sociais em fila que não foram publicados
- Erros nos logs

Ao fim de um mês de funcionamento estável, podes passar a verificar com menos frequência.

---

## Que secrets NÃO partilhar jamais

Depois de tudo configurado, estes valores NUNCA devem aparecer em:
- Commits ao Git
- Issues ou pull requests
- Conversas com qualquer ferramenta externa (incluindo IAs)
- Screenshots públicos

Se suspeitares de fuga:
- `ANTHROPIC_API_KEY`: revoga em console.anthropic.com → API Keys → Revoke. Gera nova. Actualiza secret.
- `META_PAGE_ACCESS_TOKEN`: vai a `Security Settings` da app Meta → invalidate token. Gera novo. Actualiza secret.

---

## Onde pedir ajuda se algo correr mal

- **Site não carrega:** verificar GitHub Pages Settings. Deve dizer "Your site is live at saudeauditiva.pt".
- **Workflow falha:** abrir a run no GitHub Actions, ler os logs. 90% dos erros são secrets mal configurados ou tokens expirados.
- **Artigo mal formatado:** problema no prompt do `generate_article.py` — editar o prompt e testar em dry-run.
- **Post de Instagram falha mas Facebook vai:** quase sempre é ausência de imagem (Unsplash falhou), ou IG Business Account mal ligado à página Facebook.

Para tudo o resto, pode-se voltar a mim com logs concretos e ajudo a diagnosticar.
