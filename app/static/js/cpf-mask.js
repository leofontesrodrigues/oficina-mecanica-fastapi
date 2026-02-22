document.addEventListener("DOMContentLoaded", () => {
    const formatarCpf = (valor) => {
        let cpf = (valor || "").replace(/\D/g, "").slice(0, 11);
        cpf = cpf.replace(/(\d{3})(\d)/, "$1.$2");
        cpf = cpf.replace(/(\d{3})(\d)/, "$1.$2");
        cpf = cpf.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
        return cpf;
    };

    document.querySelectorAll(".cpf").forEach((input) => {
        input.value = formatarCpf(input.value);

        input.addEventListener("input", () => {
            input.value = formatarCpf(input.value);
        });

        input.addEventListener("keypress", (e) => {
            if (!/[0-9]/.test(e.key)) {
                e.preventDefault();
            }
        });
    });
});
