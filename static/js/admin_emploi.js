/* admin_emploi.js — soumission auto du select de classe */

document.addEventListener('DOMContentLoaded', function() {
    var sel = document.getElementById('classe-select');
    if (sel) sel.addEventListener('change', function() { this.form.submit(); });
});
