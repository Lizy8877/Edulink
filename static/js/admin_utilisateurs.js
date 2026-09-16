/* admin_utilisateurs.js — filtrage et affichage conditionnel des champs */

function filterTable() {
    const search       = document.getElementById('filter-search').value.toLowerCase().trim();
    const roleFilter   = document.getElementById('filter-role').value;
    const classeFilter = document.getElementById('filter-classe').value;

    const rows    = document.querySelectorAll('#users-table tbody tr[data-nom]');
    const empty   = document.getElementById('empty-filter');
    const counter = document.getElementById('user-count');

    let visible = 0;

    rows.forEach(function(row) {
        const nom    = row.dataset.nom    || '';
        const compte = row.dataset.compte || '';
        const role   = row.dataset.role   || '';
        const classe = row.dataset.classe || '';

        const matchSearch = !search || nom.includes(search) || compte.includes(search);
        const matchRole   = !roleFilter || role === roleFilter;
        const matchClasse = !classeFilter ||
            (classeFilter === '__aucune__' ? classe === '' : classe === classeFilter);

        const show = matchSearch && matchRole && matchClasse;
        row.style.display = show ? '' : 'none';
        if (show) visible++;
    });

    counter.textContent = visible + ' utilisateur(s)';
    empty.style.display = visible === 0 ? 'block' : 'none';
}

function resetFilters() {
    document.getElementById('filter-search').value = '';
    document.getElementById('filter-role').value   = '';
    document.getElementById('filter-classe').value = '';
    filterTable();
}

function toggleFields() {
    const select       = document.getElementById('role_select');
    const roleName     = select.options[select.selectedIndex].getAttribute('data-name');
    const matiereGroup = document.getElementById('matiere_group');
    const matiereInput = document.getElementById('matiere_input');
    const classeGroup  = document.getElementById('classe_group');

    matiereGroup.style.display = 'none';
    matiereInput.required      = false;
    classeGroup.style.display  = 'none';

    if (roleName === 'Professeur') {
        matiereGroup.style.display = 'block';
        matiereInput.required      = true;
    } else if (roleName === 'Eleve') {
        classeGroup.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    /* Filtre texte en temps réel */
    var searchInput = document.getElementById('filter-search');
    if (searchInput) searchInput.addEventListener('input', filterTable);

    /* Filtres select */
    var filterRole = document.getElementById('filter-role');
    if (filterRole) filterRole.addEventListener('change', filterTable);

    var filterClasse = document.getElementById('filter-classe');
    if (filterClasse) filterClasse.addEventListener('change', filterTable);

    /* Bouton reset */
    var btnReset = document.getElementById('btn-reset-filters');
    if (btnReset) btnReset.addEventListener('click', resetFilters);

    /* Rôle select → affichage conditionnel matière/classe */
    var roleSelect = document.getElementById('role_select');
    if (roleSelect) roleSelect.addEventListener('change', toggleFields);

    /* Select de changement de classe dans le tableau (submit auto) */
    document.querySelectorAll('.auto-submit-select').forEach(function(sel) {
        sel.addEventListener('change', function() { this.form.submit(); });
    });
});
