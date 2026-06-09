document.addEventListener('click', function(e) {
    var menu = document.getElementById('userMenu');
    var toggle = document.getElementById('userToggle');
    if (!menu || !toggle) return;
    if (toggle.contains(e.target)) {
        menu.classList.toggle('open');
    } else if (e.target.closest('.navbar-overlay') || !menu.contains(e.target)) {
        menu.classList.remove('open');
    }
});
