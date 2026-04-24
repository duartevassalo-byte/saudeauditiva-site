/* =========================================================
   Saúde Auditiva — Script principal
   ========================================================= */

/* -------- Nav toggle (mobile) -------- */
(function(){
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.nav-primary');
  if (!toggle || !nav) return;
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
  });
})();

/* -------- Modal (booking) -------- */
(function(){
  const overlay = document.getElementById('modal-booking');
  if (!overlay) return;
  const closeBtn = overlay.querySelector('.close-btn');

  function open() {
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function close() {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  document.querySelectorAll('[data-open-booking]').forEach(el => {
    el.addEventListener('click', (e) => { e.preventDefault(); open(); });
  });
  if (closeBtn) closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('open')) close();
  });
})();

/* -------- Consultation form (inline & modal) -------- */
(function(){
  const FORMSPREE_ENDPOINT = 'https://formspree.io/f/mzdyknzg';

  document.querySelectorAll('form.consulta-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = form.querySelector('button[type="submit"]');
      const successBox = form.parentElement.querySelector('.form-success');
      const originalBtnHTML = submitBtn ? submitBtn.innerHTML : '';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> A enviar…';
      }

      try {
        // Recolher dados
        const formData = new FormData(form);
        formData.append('_subject', 'Nova consulta — saudeauditiva.pt');
        formData.append('origem', 'saudeauditiva.pt — ' + (form.id || 'modal'));
        formData.append('pagina', window.location.pathname);

        const res = await fetch(FORMSPREE_ENDPOINT, {
          method: 'POST',
          body: formData,
          headers: { 'Accept': 'application/json' }
        });

        if (res.ok) {
          form.style.display = 'none';
          if (successBox) successBox.classList.add('show');
        } else {
          throw new Error('Submissão falhou (' + res.status + ')');
        }
      } catch (err) {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalBtnHTML;
        }
        alert('Não foi possível enviar o pedido. Por favor tente novamente ou contacte-nos directamente para geral@saudeauditiva.pt.');
      }
    });
  });
})();

/* -------- Contact form -------- */
(function(){
  const FORMSPREE_ENDPOINT = 'https://formspree.io/f/mzdyknzg';
  const form = document.getElementById('contact-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    const successBox = document.getElementById('contact-success');
    const originalBtnHTML = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> A enviar…';
    }

    try {
      const formData = new FormData(form);
      formData.append('_subject', 'Mensagem de contacto — saudeauditiva.pt');
      formData.append('origem', 'saudeauditiva.pt — formulário contacto');

      const res = await fetch(FORMSPREE_ENDPOINT, {
        method: 'POST',
        body: formData,
        headers: { 'Accept': 'application/json' }
      });

      if (res.ok) {
        form.style.display = 'none';
        if (successBox) successBox.classList.add('show');
      } else {
        throw new Error('Submissão falhou (' + res.status + ')');
      }
    } catch (err) {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnHTML;
      }
      alert('Não foi possível enviar a mensagem. Por favor tente novamente ou contacte-nos directamente para geral@saudeauditiva.pt.');
    }
  });
})();

/* -------- Quiz (5 questions) -------- */
(function(){
  const quiz = document.getElementById('quiz');
  if (!quiz) return;

  const questions = [
    {
      q: "Pede às pessoas para repetirem o que disseram, mesmo em silêncio?",
      options: [
        { text: "Raramente",        score: 0 },
        { text: "Ocasionalmente",   score: 1 },
        { text: "Frequentemente",   score: 2 },
        { text: "Quase sempre",     score: 3 }
      ]
    },
    {
      q: "Acha que os outros falam baixo ou pronunciam mal as palavras?",
      options: [
        { text: "Não",                 score: 0 },
        { text: "Algumas vezes",       score: 1 },
        { text: "Com frequência",      score: 2 },
        { text: "É a principal queixa",score: 3 }
      ]
    },
    {
      q: "Tem dificuldade em seguir conversas em locais com ruído (restaurantes, festas)?",
      options: [
        { text: "Nenhuma dificuldade", score: 0 },
        { text: "Pouca",               score: 1 },
        { text: "Alguma",              score: 2 },
        { text: "Muita",               score: 3 }
      ]
    },
    {
      q: "Os familiares dizem que o volume da televisão está alto?",
      options: [
        { text: "Nunca",                score: 0 },
        { text: "Algumas vezes",        score: 1 },
        { text: "Muitas vezes",         score: 2 },
        { text: "É motivo de discussão",score: 3 }
      ]
    },
    {
      q: "Tem zumbidos, apitos ou ruídos persistentes nos ouvidos?",
      options: [
        { text: "Nunca",     score: 0 },
        { text: "Ocasionais",score: 1 },
        { text: "Frequentes",score: 2 },
        { text: "Constantes",score: 3 }
      ]
    }
  ];

  let current = 0;
  let score = 0;

  function render() {
    quiz.innerHTML = `
      <h3>Teste rápido de audição</h3>
      <p class="subtitle">5 perguntas · cerca de 2 minutos · resultado imediato</p>
      <div class="quiz-progress"><div class="quiz-progress-bar" id="quiz-bar"></div></div>
      <div id="quiz-body"></div>
    `;
    showQuestion();
  }

  function showQuestion() {
    const body = document.getElementById('quiz-body');
    const bar = document.getElementById('quiz-bar');
    bar.style.width = ((current) / questions.length * 100) + '%';
    const q = questions[current];
    body.innerHTML = `
      <div class="quiz-question active">
        <div class="q-num">Pergunta ${current + 1} de ${questions.length}</div>
        <h4>${q.q}</h4>
        <div class="quiz-options">
          ${q.options.map((opt, i) => `<button type="button" data-score="${opt.score}">${opt.text}</button>`).join('')}
        </div>
      </div>
    `;
    body.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        score += parseInt(btn.dataset.score, 10);
        current++;
        if (current >= questions.length) {
          showResult();
        } else {
          showQuestion();
        }
      });
    });
  }

  function showResult() {
    const bar = document.getElementById('quiz-bar');
    bar.style.width = '100%';
    const body = document.getElementById('quiz-body');
    const max = questions.length * 3;
    const pct = Math.round(score / max * 100);
    let title, text;
    if (score <= 3) {
      title = "Audição aparentemente saudável";
      text = "As suas respostas não indicam sinais significativos de perda auditiva. Mantenha hábitos de prevenção — como evitar exposição prolongada a ruído alto — e considere uma avaliação de rotina a cada 2 a 3 anos.";
    } else if (score <= 7) {
      title = "Possíveis sinais ligeiros";
      text = "Algumas das suas respostas indicam sinais que podem corresponder a uma perda auditiva ligeira. Uma avaliação profissional permite esclarecer se há ou não perda — e, em caso afirmativo, intervir precocemente.";
    } else if (score <= 11) {
      title = "Sinais moderados detectados";
      text = "As suas respostas sugerem sinais compatíveis com perda auditiva moderada. Recomendamos marcar uma avaliação auditiva gratuita para esclarecer a situação. O diagnóstico precoce faz uma diferença real.";
    } else {
      title = "Sinais significativos";
      text = "As suas respostas indicam sinais importantes que merecem atenção. Uma consulta com um audioprotesista é fortemente recomendada — quanto mais cedo for feita a avaliação, melhores são os resultados de qualquer intervenção.";
    }
    body.innerHTML = `
      <div class="quiz-result show">
        <div class="score-ring">${score}/${max}</div>
        <h4>${title}</h4>
        <p class="result-text">${text}</p>
        <a href="#" class="btn btn-primary btn-block" data-open-booking>Marcar consulta gratuita</a>
      </div>
    `;
    // Re-bind booking
    body.querySelectorAll('[data-open-booking]').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        const overlay = document.getElementById('modal-booking');
        if (overlay) {
          overlay.classList.add('open');
          document.body.style.overflow = 'hidden';
        }
      });
    });
  }

  render();
})();

/* -------- Render articles from artigos.json -------- */
(function(){
  const slots = document.querySelectorAll('[data-articles]');
  if (!slots.length) return;

  // Detectar root (igual ao partials.js): data-root no <script> ou auto-detectar por pathname
  const scriptEl = document.currentScript || document.querySelector('script[src$="script.js"]');
  const rootAttr = scriptEl && scriptEl.dataset ? scriptEl.dataset.root : '';
  // Se o script está em ../script.js, o root é "../" . Caso contrário é "".
  const ROOT = rootAttr || (scriptEl && scriptEl.src && scriptEl.src.includes('/categoria/') ? '../' :
               (scriptEl && scriptEl.src && scriptEl.src.includes('/artigos/') ? '../' : ''));

  const CATEGORIES = {
    "perda-auditiva":  { label: "Perda Auditiva",  slug: "perda-auditiva"  },
    "sinais-alerta":   { label: "Sinais de Alerta", slug: "sinais-alerta"  },
    "prevencao":       { label: "Prevenção",        slug: "prevencao"      },
    "familia":         { label: "Família",          slug: "familia"        },
    "aparelhos":       { label: "Aparelhos",        slug: "aparelhos"      }
  };

  function formatDate(d) {
    if (!d) return "";
    try {
      const date = new Date(d);
      return date.toLocaleDateString('pt-PT', { day: 'numeric', month: 'long', year: 'numeric' });
    } catch (e) { return d; }
  }

  function card(a) {
    const cat = CATEGORIES[a.categoria] || { label: a.categoria, slug: a.categoria };
    const href = a.slug ? `${ROOT}artigos/${a.slug}.html` : '#';
    return `
      <a href="${href}" class="article-card">
        <div class="card-meta">
          ${cat.label}
          ${a.tempo_leitura ? `<span class="dot">·</span>${a.tempo_leitura}` : ''}
        </div>
        <h4>${a.titulo || ''}</h4>
        <p>${a.resumo || ''}</p>
        <span class="read-more">Ler artigo →</span>
      </a>
    `;
  }

  async function loadArticles() {
    try {
      const res = await fetch('artigos.json', { cache: 'no-cache' });
      if (!res.ok) throw new Error('not found');
      return await res.json();
    } catch (e) {
      // Try one level up (for category pages)
      try {
        const res = await fetch('../artigos.json', { cache: 'no-cache' });
        if (!res.ok) throw new Error('not found');
        return await res.json();
      } catch (e2) { return []; }
    }
  }

  loadArticles().then(articles => {
    slots.forEach(slot => {
      const mode = slot.dataset.articles; // "recent" | "category:<slug>" | "home-grouped"
      const limit = parseInt(slot.dataset.limit, 10) || 6;

      if (mode === 'recent') {
        const list = [...articles]
          .sort((a,b) => new Date(b.data || 0) - new Date(a.data || 0))
          .slice(0, limit);
        if (!list.length) {
          slot.innerHTML = emptyState();
          return;
        }
        slot.innerHTML = list.map(card).join('');
      }

      else if (mode === 'home-grouped') {
        let html = '';
        Object.values(CATEGORIES).forEach(cat => {
          const list = articles.filter(a => a.categoria === cat.slug).slice(0, 3);
          if (!list.length) return;
          html += `
            <div class="category-block">
              <div class="category-head">
                <h3><span class="num">${cat.slug.replace('-', ' ').toUpperCase()}</span>${cat.label}</h3>
                <a href="${ROOT}categoria/${cat.slug}.html" class="see-more">Ver todos</a>
              </div>
              <div class="articles-grid">
                ${list.map(card).join('')}
              </div>
            </div>
          `;
        });
        slot.innerHTML = html || emptyState();
      }

      else if (mode.startsWith('category:')) {
        const catSlug = mode.split(':')[1];
        const list = articles.filter(a => a.categoria === catSlug)
                             .sort((a,b) => new Date(b.data || 0) - new Date(a.data || 0));
        if (!list.length) {
          slot.innerHTML = emptyState();
          return;
        }
        slot.innerHTML = list.map(card).join('');
      }
    });
  });

  function emptyState() {
    return `
      <div style="grid-column: 1/-1; text-align:center; padding:3rem 1rem; color:var(--ink-mute); border:1px dashed var(--rule);">
        <p style="margin:0; font-family:var(--serif); font-style:italic;">Os artigos aparecerão aqui assim que forem publicados.</p>
      </div>
    `;
  }
})();

/* -------- Year in footer -------- */
(function(){
  const yearEl = document.getElementById('current-year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();
})();
