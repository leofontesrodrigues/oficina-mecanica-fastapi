document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".telefone").forEach(input => {

        input.addEventListener("input", () => {
            let valor = input.value.replace(/\D/g, "");

            if (valor.length > 11) {
                valor = valor.slice(0, 11);
            }

            if (valor.length <= 10) {
                // (99) 9999-9999
                valor = valor.replace(
                    /(\d{2})(\d{4})(\d{0,4})/,
                    "($1) $2-$3"
                );
            } else {
                // (99) 99999-9999
                valor = valor.replace(
                    /(\d{2})(\d{5})(\d{0,4})/,
                    "($1) $2-$3"
                );
            }

            input.value = valor;
        });

        // 🔥 bloqueia letras
        input.addEventListener("keypress", e => {
            if (!/[0-9]/.test(e.key)) {
                e.preventDefault();
            }
        });
    });
});
