document.addEventListener('click', function(e) {
    var menu = document.getElementById('userMenu');
    var toggle = document.getElementById('userToggle');
    if (menu && toggle) {
        if (toggle.contains(e.target)) {
            menu.classList.toggle('open');
        } else if (e.target.closest('.navbar-overlay') || !menu.contains(e.target)) {
            menu.classList.remove('open');
        }
    }

    var notifMenu = document.getElementById('notifMenu');
    var notifToggle = document.getElementById('notifToggle');
    if (notifMenu && notifToggle) {
        if (notifToggle.contains(e.target)) {
            notifMenu.classList.toggle('open');
        } else if (e.target.closest('.navbar-overlay') || !notifMenu.contains(e.target)) {
            notifMenu.classList.remove('open');
        }
    }

    var search = document.getElementById('navbarSearch');
    if (search && search.contains(e.target) && window.innerWidth <= 768) {
        search.classList.add('expanded');
        setTimeout(function() { search.querySelector('input').focus(); }, 100);
    } else if (search) {
        search.classList.remove('expanded');
    }
});

document.addEventListener('click', function(e) {
    var markBtn = e.target.closest('#markReadBtn');
    if (!markBtn) return;
    e.preventDefault();
    fetch('/notifications/read/', {
        method: 'POST',
        headers: { 'X-CSRFToken': document.cookie.split('; ').find(function(c) { return c.startsWith('csrftoken='); }).split('=')[1] }
    }).then(function() {
        document.querySelectorAll('.notif-unread').forEach(function(el) {
            el.classList.remove('notif-unread');
            el.classList.add('notif-read');
        });
        var badge = document.getElementById('notifBadge');
        if (badge) badge.remove();
    });
});
