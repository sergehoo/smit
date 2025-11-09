// Validation en temps réel des mots de passe
$(document).ready(function() {
    function checkPasswordRequirements(password) {
        const requirements = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            number: /\d/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };

        return requirements;
    }

    function updateRequirementStatus(requirement, isValid) {
        const element = $(`.password-requirements li.${requirement}`);
        element.toggleClass('text-success', isValid);
        element.toggleClass('text-danger', !isValid);
    }

    $('input[name="new_password1"]').on('input', function() {
        const password = $(this).val();
        const requirements = checkPasswordRequirements(password);

        Object.keys(requirements).forEach(req => {
            updateRequirementStatus(req, requirements[req]);
        });
    });
});