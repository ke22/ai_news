(function () {
  var PROD_ORIGIN = 'https://agent-console.ke2211975.workers.dev';
  var LOCAL_ORIGIN = 'http://localhost:3100';
  var EMBED_PATH = '/embed';
  var LOAD_TIMEOUT_MS = 8000;

  // When AI News is served locally, frame the local agent-console dev server so
  // changes can be tested before deploying. Production pages always use the
  // deployed console, and messages are still posted to exactly one origin.
  function consoleOrigin() {
    var host = location.hostname;
    if (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0') {
      return LOCAL_ORIGIN;
    }
    return PROD_ORIGIN;
  }

  var EMBED_ORIGIN = consoleOrigin();

  var lang = localStorage.getItem('lang') || 'en';
  var assistant = null; // created only on report pages (marker present)

  function applyLang(l) {
    document.querySelectorAll('.lang-en').forEach(function (el) {
      el.style.display = l === 'en' ? '' : 'none';
    });
    document.querySelectorAll('.lang-zh').forEach(function (el) {
      el.style.display = l === 'zh' ? '' : 'none';
    });
    document.querySelectorAll('.lang-btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.lang === l);
    });
    if (assistant) {
      assistant.setLanguage(l);
    }
  }

  // Builds the floating Deep Research assistant. The iframe is created lazily on
  // first open and stays mounted for the page lifetime so closing/minimizing the
  // panel never interrupts an active SSE research session.
  function createAssistant() {
    var iframe = null;
    var loaded = false;
    var loadTimer = null;
    var currentLang = lang;

    var launcher = document.createElement('button');
    launcher.type = 'button';
    launcher.className = 'assistant-launcher';
    launcher.setAttribute('aria-label', 'Open Deep Research assistant');
    launcher.setAttribute('aria-haspopup', 'dialog');
    launcher.textContent = 'Deep Research';

    var panel = document.createElement('div');
    panel.className = 'assistant-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'false');
    panel.setAttribute('aria-label', 'Deep Research assistant');
    panel.hidden = true;

    var header = document.createElement('div');
    header.className = 'assistant-header';

    var title = document.createElement('span');
    title.className = 'assistant-title';
    title.textContent = 'Deep Research';

    var external = document.createElement('a');
    external.className = 'assistant-btn assistant-external';
    external.href = EMBED_ORIGIN + EMBED_PATH;
    external.target = '_blank';
    external.rel = 'noopener';
    external.setAttribute('aria-label', 'Open Deep Research in a new tab');
    external.textContent = '↗';

    var minimize = document.createElement('button');
    minimize.type = 'button';
    minimize.className = 'assistant-btn assistant-minimize';
    minimize.setAttribute('aria-label', 'Minimize Deep Research assistant');
    minimize.textContent = '–';

    var close = document.createElement('button');
    close.type = 'button';
    close.className = 'assistant-btn assistant-close';
    close.setAttribute('aria-label', 'Close Deep Research assistant');
    close.textContent = '×';

    header.appendChild(title);
    header.appendChild(external);
    header.appendChild(minimize);
    header.appendChild(close);

    var body = document.createElement('div');
    body.className = 'assistant-body';

    var fallback = document.createElement('div');
    fallback.className = 'assistant-fallback';
    fallback.hidden = true;
    var fallbackLink = document.createElement('a');
    fallbackLink.href = EMBED_ORIGIN + EMBED_PATH;
    fallbackLink.target = '_blank';
    fallbackLink.rel = 'noopener';
    fallbackLink.textContent = 'Open the full Deep Research console →';
    fallback.appendChild(fallbackLink);
    body.appendChild(fallback);

    panel.appendChild(header);
    panel.appendChild(body);

    document.body.appendChild(launcher);
    document.body.appendChild(panel);

    function sendLanguage() {
      if (iframe && loaded && iframe.contentWindow) {
        iframe.contentWindow.postMessage(
          { type: 'ai-news:language', language: currentLang },
          EMBED_ORIGIN
        );
      }
    }

    function ensureIframe() {
      if (iframe) {
        return;
      }
      iframe = document.createElement('iframe');
      iframe.className = 'assistant-iframe';
      iframe.title = 'Deep Research console';
      iframe.setAttribute(
        'sandbox',
        'allow-scripts allow-forms allow-same-origin allow-downloads allow-popups'
      );
      iframe.src = EMBED_ORIGIN + EMBED_PATH + '?lang=' + currentLang;
      iframe.addEventListener('load', function () {
        loaded = true;
        if (loadTimer) {
          clearTimeout(loadTimer);
          loadTimer = null;
        }
        fallback.hidden = true;
        sendLanguage();
      });
      body.insertBefore(iframe, fallback);
      loadTimer = setTimeout(function () {
        if (!loaded) {
          fallback.hidden = false;
        }
      }, LOAD_TIMEOUT_MS);
    }

    function open() {
      ensureIframe();
      panel.hidden = false;
      launcher.setAttribute('aria-expanded', 'true');
      close.focus();
    }

    function hide() {
      panel.hidden = true;
      launcher.setAttribute('aria-expanded', 'false');
      launcher.focus();
    }

    launcher.addEventListener('click', function () {
      if (panel.hidden) {
        open();
      } else {
        hide();
      }
    });
    minimize.addEventListener('click', hide);
    close.addEventListener('click', hide);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.hidden) {
        hide();
      }
    });

    return {
      setLanguage: function (l) {
        currentLang = l;
        sendLanguage();
      },
    };
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (document.querySelector('[data-research-assistant]')) {
      assistant = createAssistant();
    }
    applyLang(lang);
    document.querySelectorAll('.lang-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        lang = btn.dataset.lang;
        localStorage.setItem('lang', lang);
        applyLang(lang);
      });
    });
  });
}());
