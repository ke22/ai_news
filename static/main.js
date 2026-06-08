(function () {
  function setLang(lang) {
    document.querySelectorAll('.en').forEach(function (el) {
      el.style.display = lang === 'en' ? '' : 'none';
    });
    document.querySelectorAll('.zh').forEach(function (el) {
      el.style.display = lang === 'zh' ? '' : 'none';
    });
    document.querySelectorAll('.lang-btn').forEach(function (btn) {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
    });
    try { localStorage.setItem('ainews_lang', lang); } catch (e) {}
  }

  window.setLang = setLang;

  document.addEventListener('DOMContentLoaded', function () {
    var stored;
    try { stored = localStorage.getItem('ainews_lang'); } catch (e) {}
    setLang(stored || 'en');
  });
}());
