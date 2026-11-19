/* Botão de tema claro/escuro.
   O tema inicial é aplicado por um script no <head> (antes da página
   aparecer); aqui fica só o clique do botão e o rótulo dele. */
(function () {
    var CHAVE = 'sua-festa-tema';

    function temaAtual() {
        return document.documentElement.getAttribute('data-bs-theme') || 'light';
    }

    function atualizarBotao(botao) {
        var escuro = temaAtual() === 'dark';
        botao.textContent = escuro ? '☀' : '☾';
        botao.setAttribute(
            'aria-label',
            escuro ? 'Mudar para o tema claro' : 'Mudar para o tema escuro'
        );
        botao.setAttribute('title', botao.getAttribute('aria-label'));
    }

    document.addEventListener('DOMContentLoaded', function () {
        var botao = document.getElementById('botao-tema');
        if (!botao) {
            return;
        }
        atualizarBotao(botao);
        botao.addEventListener('click', function () {
            var novo = temaAtual() === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', novo);
            try {
                localStorage.setItem(CHAVE, novo);
            } catch (e) {
                /* sem localStorage: o tema só vale nesta página */
            }
            atualizarBotao(botao);
        });
    });
})();
