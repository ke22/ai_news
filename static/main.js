(function () {
  var lang = localStorage.getItem('lang') || 'en';

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
  }

  document.addEventListener('DOMContentLoaded', function () {
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
