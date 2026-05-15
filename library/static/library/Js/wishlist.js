document.addEventListener("DOMContentLoaded", function () {
    const deleteButtons = document.querySelectorAll('.btn-remove');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault(); // পেজ রিলোড হওয়া বন্ধ করবে
            
            if (!confirm('Remove this book?')) return;

            const url = this.getAttribute('href');
            const card = this.closest('.wishlist-card'); // আপনার কার্ডের ক্লাস নাম

            // ব্যাকেন্ডে রিকোয়েস্ট পাঠানো
            fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                // কার্ডটি হালকা হয়ে ভ্যানিশ হওয়ার অ্যানিমেশন
                card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                
                setTimeout(() => {
                    card.remove();
                    // যদি সব বই ডিলিট হয়ে যায় তবে পেজ রিলোড দিবে খালি উইশলিস্ট দেখানোর জন্য
                    if (document.querySelectorAll('.wishlist-card').length === 0) {
                        location.reload();
                    }
                }, 400);
            })
            .catch(error => console.error('Error:', error));
        });
    });
});