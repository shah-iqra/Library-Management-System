document.addEventListener('DOMContentLoaded', function () {

    // --- ১. ফিল্টার ড্রপডাউন মেনু হ্যান্ডলার ---
    const filterBtn = document.getElementById('filterBtn');
    const filterMenu = document.getElementById('filterMenu');

    if (filterBtn && filterMenu) {
        filterBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isVisible = filterMenu.style.display === 'block';
            filterMenu.style.display = isVisible ? 'none' : 'block';
        });

        document.addEventListener('click', function () {
            filterMenu.style.display = 'none';
        });

        filterMenu.addEventListener('click', function (e) {
            e.stopPropagation();
        });
    }

    // --- ২. filterTable ফাংশন ---
    window.filterTable = function (criteria) {
        const rows = document.querySelectorAll('.member-table tbody tr');
        rows.forEach(row => {
            const rowText = row.innerText.toLowerCase();
            const filterCriteria = criteria.toLowerCase();
            if (filterCriteria === 'all') {
                row.style.display = '';
            } else if (rowText.includes(filterCriteria)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        if (filterMenu) filterMenu.style.display = 'none';
    };

    // --- ৩. রিয়েল-টাইম সার্চ ---
    const searchInput = document.querySelector('.search-box input');
    if (searchInput) {
        searchInput.addEventListener('keyup', function () {
            const searchTerm = this.value.toLowerCase();
            document.querySelectorAll('.member-table tbody tr').forEach(row => {
                row.style.display = row.innerText.toLowerCase().includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // --- ৪. পাসওয়ার্ড শো/হাইড ---
    const toggleBtn = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    if (toggleBtn && passwordInput) {
        toggleBtn.addEventListener('click', function () {
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggleBtn.textContent = '🙈';
            } else {
                passwordInput.type = 'password';
                toggleBtn.textContent = '👁️';
            }
        });
    }

    // --- ৫. ডিলিট কনফার্মেশন ---
    document.querySelectorAll('.btn-icon.delete, .btn-delete').forEach(btn => {
        btn.addEventListener('click', function (e) {
            if (!confirm('আপনি কি নিশ্চিতভাবে এই মেম্বারটি ডিলিট করতে চান?')) {
                e.preventDefault();
            }
        });
    });

    // --- ৬. সাইডবার লিংক হাইলাইটার ---
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar a, .nav-item a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            const parent = link.closest('li');
            if (parent) parent.classList.add('active');
        }
    });

    // --- ৭. এক্সপোর্ট বাটন লগ ---
    const exportBtn = document.querySelector('.btn-export');
    if (exportBtn) {
        exportBtn.addEventListener('click', function () {
            console.log("Member list CSV export initialized...");
        });
    }

});