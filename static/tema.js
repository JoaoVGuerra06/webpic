// tema.js — aplica e alterna modo claro/escuro
(function () {
    const KEY = "sus-tema";

    function aplicar(tema) {
        document.documentElement.setAttribute("data-theme", tema);
        document.querySelectorAll(".btn-tema").forEach(function (btn) {
            btn.textContent = tema === "dark" ? "☀️ Modo claro" : "🌙 Modo escuro";
        });
    }

    // aplica imediatamente (antes do paint) para evitar flash
    var temaInicial = localStorage.getItem(KEY) || "light";
    aplicar(temaInicial);

    // expõe função para os botões chamarem
    window.alternarTema = function () {
        var atual = document.documentElement.getAttribute("data-theme") || "light";
        var novo = atual === "dark" ? "light" : "dark";
        localStorage.setItem(KEY, novo);
        aplicar(novo);
    };
})();
