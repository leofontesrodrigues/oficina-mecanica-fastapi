document.addEventListener("DOMContentLoaded", () => {
    const somenteDigitos = (valor) => (valor || "").replace(/\D/g, "");

    const formatarCep = (valor) => {
        const digits = somenteDigitos(valor).slice(0, 8);
        if (digits.length <= 5) return digits;
        return `${digits.slice(0, 5)}-${digits.slice(5)}`;
    };

    const encontrarEscopo = (cepInput) => {
        return (
            cepInput.closest(".modal-content")
            || cepInput.closest("form")
            || document
        );
    };

    const buscarCampo = (escopo, classe, name) => {
        return (
            escopo.querySelector(`input.${classe}`)
            || escopo.querySelector(`input[name="${name}"]`)
        );
    };

    const preencherEndereco = async (cepInput) => {
        const escopo = encontrarEscopo(cepInput);
        if (!escopo) return;

        const cep = somenteDigitos(cepInput.value);
        if (cep.length !== 8) return;

        try {
            const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
            if (!response.ok) return;

            const data = await response.json();
            if (data.erro) return;

            const endereco = buscarCampo(escopo, "endereco", "endereco");
            const bairro = buscarCampo(escopo, "bairro", "bairro");
            const cidade = buscarCampo(escopo, "cidade", "cidade");
            const uf = buscarCampo(escopo, "uf", "uf");

            if (endereco && data.logradouro) endereco.value = data.logradouro;
            if (bairro && data.bairro) bairro.value = data.bairro;
            if (cidade && data.localidade) cidade.value = data.localidade;
            if (uf && data.uf) uf.value = data.uf;
        } catch (_) {
            // sem bloqueio do fluxo em caso de falha na API
        }
    };

    document.querySelectorAll("input.cep").forEach((input) => {
        input.value = formatarCep(input.value);

        input.addEventListener("input", () => {
            input.value = formatarCep(input.value);
        });

        input.addEventListener("keypress", (e) => {
            if (!/[0-9]/.test(e.key)) e.preventDefault();
        });

        input.addEventListener("blur", () => {
            preencherEndereco(input);
        });

        input.addEventListener("change", () => {
            preencherEndereco(input);
        });

        input.addEventListener("keydown", (e) => {
            if (e.key === "Tab") {
                preencherEndereco(input);
            }
        });
    });

    document.querySelectorAll("input.uf").forEach((input) => {
        input.addEventListener("input", () => {
            input.value = (input.value || "").replace(/[^a-zA-Z]/g, "").slice(0, 2).toUpperCase();
        });
    });
});
