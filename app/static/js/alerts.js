document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('hidden.bs.modal', () => {
            modal.querySelectorAll('form').forEach(form => {
                form.classList.remove('was-validated');
                form.reset();
            });
        });
    });

});