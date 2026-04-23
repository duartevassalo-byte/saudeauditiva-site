/* =========================================================
   Partials: topbar, site-header, modal, site-footer
   Injectado via partials.js — evita duplicação entre páginas
   ========================================================= */

(function(){
  const root = document.currentScript ? document.currentScript.dataset.root || '' : '';
  // root = "" para raiz, "../" para páginas em subpastas

  const topbarHTML = `
    <div class="topbar">
      <div class="container">
        <div class="badges">
          <span>✓ Informação editorial independente</span>
          <span>✓ Fontes científicas citadas</span>
          <span>🔒 Dados confidenciais · RGPD</span>
        </div>
        <div>
          📞 Prefere ligar? <a href="tel:+351210303361">210 303 361</a> · Gratuito · Seg–Sex 9h–18h
        </div>
      </div>
    </div>
  `;

  const headerHTML = `
    <header class="site-header">
      <div class="container">
        <a href="${root}index.html" class="brand">
          Saúde <em>Auditiva</em>
          <small>Portal informativo · Portugal</small>
        </a>
        <button class="nav-toggle" aria-label="Abrir menu" aria-expanded="false">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="7" x2="21" y2="7"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="17" x2="21" y2="17"/>
          </svg>
        </button>
        <nav class="nav-primary" id="nav-primary">
          <a href="${root}index.html" data-nav="home">Início</a>
          <a href="${root}categoria/perda-auditiva.html" data-nav="perda-auditiva">Perda Auditiva</a>
          <a href="${root}categoria/sinais-alerta.html" data-nav="sinais-alerta">Sinais de Alerta</a>
          <a href="${root}categoria/prevencao.html" data-nav="prevencao">Prevenção</a>
          <a href="${root}categoria/familia.html" data-nav="familia">Família</a>
          <a href="${root}categoria/aparelhos.html" data-nav="aparelhos">Aparelhos</a>
          <a href="#" class="cta-nav" data-open-booking>Consulta gratuita</a>
        </nav>
      </div>
    </header>
  `;

  const footerHTML = `
    <footer class="site-footer">
      <div class="container">
        <div class="footer-grid">
          <div>
            <div class="brand">Saúde <em>Auditiva</em><small>Portal informativo · Portugal</small></div>
            <p>Portal editorial independente sobre saúde auditiva em Portugal. Conteúdo informativo com base em evidência científica. Não substitui aconselhamento médico ou audiológico profissional.</p>
          </div>
          <div>
            <h5>Categorias</h5>
            <ul>
              <li><a href="${root}categoria/perda-auditiva.html">Perda Auditiva</a></li>
              <li><a href="${root}categoria/sinais-alerta.html">Sinais de Alerta</a></li>
              <li><a href="${root}categoria/prevencao.html">Prevenção</a></li>
              <li><a href="${root}categoria/familia.html">Família</a></li>
              <li><a href="${root}categoria/aparelhos.html">Aparelhos</a></li>
            </ul>
          </div>
          <div>
            <h5>Portal</h5>
            <ul>
              <li><a href="${root}sobre.html">Sobre Nós</a></li>
              <li><a href="${root}contacto.html">Contacto</a></li>
              <li><a href="#" data-open-booking>Consulta gratuita</a></li>
            </ul>
          </div>
          <div>
            <h5>Legal</h5>
            <ul>
              <li><a href="${root}privacidade.html">Política de Privacidade</a></li>
              <li><a href="${root}termos.html">Termos de Uso</a></li>
            </ul>
          </div>
        </div>
        <div class="footer-bottom">
          <div>© <span id="current-year"></span> Saúde Auditiva</div>
          <div class="legal-list">
            <a href="${root}privacidade.html">Privacidade</a>
            <a href="${root}termos.html">Termos</a>
            <a href="${root}legal.html">Informação legal</a>
            <a href="${root}contacto.html">Contacto</a>
          </div>
        </div>
      </div>
    </footer>
  `;

  const modalHTML = `
    <div class="modal-overlay" id="modal-booking" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div class="modal">
        <button class="close-btn" aria-label="Fechar">×</button>
        <h3 id="modal-title">Marcar consulta auditiva gratuita</h3>
        <p class="subtitle">Ligamos nós para confirmar a data e hora. Avaliação completa em cerca de 30 minutos, sem compromisso.</p>
        <form class="consulta-form" id="modal-form">
          <div class="form-group">
            <label for="m-nome">Nome completo</label>
            <input type="text" id="m-nome" name="nome" required autocomplete="name">
          </div>
          <div class="form-group">
            <label for="m-tel">Telemóvel</label>
            <input type="tel" id="m-tel" name="telefone" required autocomplete="tel" pattern="[0-9 +]{9,15}">
          </div>
          <div class="form-group">
            <label for="m-horario">Melhor horário para contacto</label>
            <select id="m-horario" name="horario" required>
              <option value="">Selecione uma opção</option>
              <option>Manhã (9h – 12h)</option>
              <option>Tarde (12h – 17h)</option>
              <option>Final do dia (17h – 19h)</option>
              <option>Qualquer hora</option>
            </select>
          </div>
          <button type="submit" class="btn btn-primary btn-block btn-lg">Confirmar pedido de consulta →</button>
          <p class="form-hint">🔒 Dados confidenciais · usados apenas para marcar a sua consulta. Ver <a href="${root}privacidade.html">Política de Privacidade</a>.</p>
        </form>
        <div class="form-success">
          <strong>✓ Pedido recebido</strong>
          <p>A nossa equipa vai contactá-lo em breve para confirmar a data da consulta.</p>
        </div>
      </div>
    </div>
  `;

  // Inject
  const tb = document.getElementById('slot-topbar');
  if (tb) tb.outerHTML = topbarHTML;
  const hd = document.getElementById('slot-header');
  if (hd) hd.outerHTML = headerHTML;
  const ft = document.getElementById('slot-footer');
  if (ft) ft.outerHTML = footerHTML;
  const md = document.getElementById('slot-modal');
  if (md) md.outerHTML = modalHTML;

  // Mark active nav (via <body data-page="...">)
  const activePage = document.body.dataset.page;
  if (activePage) {
    document.querySelectorAll('.nav-primary a').forEach(a => {
      if (a.dataset.nav === activePage) a.classList.add('active');
    });
  }
})();
