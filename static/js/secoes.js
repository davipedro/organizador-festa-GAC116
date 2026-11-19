/* Atualiza só as seções do detalhe da festa (resumo, convidados e tarefas)
   quando um formulário marcado com data-atualiza-secao é enviado, em vez de
   recarregar a página inteira: a tela não pisca nem volta para o topo.

   É um aprimoramento: sem JavaScript (ou se algo falhar) o formulário é
   enviado normalmente e a página recarrega na seção certa. */
(function () {
    var SECOES = ['bloco-resumo', 'bloco-convidados', 'bloco-tarefas'];

    /* Avisos de sucesso e de informação somem sozinhos; os de erro e de
       alerta ficam até a pessoa fechar. */
    function agendarFechamento() {
        var avisos = document.querySelectorAll(
            '#mensagens .alert-success:not([data-agendado]), #mensagens .alert-info:not([data-agendado])'
        );
        avisos.forEach(function (aviso) {
            aviso.setAttribute('data-agendado', '1');
            setTimeout(function () {
                if (!document.body.contains(aviso)) {
                    return;
                }
                if (window.bootstrap && window.bootstrap.Alert) {
                    window.bootstrap.Alert.getOrCreateInstance(aviso).close();
                } else {
                    aviso.remove();
                }
            }, 5000);
        });
    }

    document.addEventListener('DOMContentLoaded', agendarFechamento);

    function trocarSecoes(novoDocumento) {
        SECOES.forEach(function (id) {
            var atual = document.getElementById(id);
            var nova = novoDocumento.getElementById(id);
            if (atual && nova) {
                atual.replaceWith(nova);
            }
        });
        var mensagens = document.getElementById('mensagens');
        var novas = novoDocumento.getElementById('mensagens');
        if (mensagens && novas) {
            mensagens.innerHTML = novas.innerHTML;
            agendarFechamento();
        }
    }

    function enviarNormalmente(form) {
        form.removeAttribute('data-atualiza-secao');
        form.submit();
    }

    document.addEventListener('submit', function (evento) {
        var form = evento.target;
        if (!form.matches || !form.matches('form[data-atualiza-secao]')) {
            return;
        }
        if (!window.fetch || !window.DOMParser || !window.FormData) {
            return;
        }
        evento.preventDefault();

        var botao = evento.submitter || form.querySelector('[type="submit"]');
        var idDoForm = form.id;
        var devolverFoco = form.hasAttribute('data-foco');
        if (botao) {
            botao.disabled = true;
        }

        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            credentials: 'same-origin',
        })
            .then(function (resposta) {
                // sucesso = a view redirecionou de volta para a página da festa
                if (!resposta.ok || !resposta.redirected) {
                    throw new Error('resposta inesperada');
                }
                return resposta.text();
            })
            .then(function (html) {
                var documento = new DOMParser().parseFromString(html, 'text/html');
                trocarSecoes(documento);
                if (devolverFoco && idDoForm) {
                    var novoForm = document.getElementById(idDoForm);
                    var campo = novoForm && novoForm.querySelector('input[type="text"]');
                    if (campo) {
                        campo.focus();
                    }
                }
            })
            .catch(function () {
                enviarNormalmente(form);
            });
    });
})();
