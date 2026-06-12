(function () {
    const filters = document.querySelectorAll('.mock-result-filter');
    const items = document.querySelectorAll('.mock-result-item[data-result-type]');
    if (!filters.length) return;

    filters.forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.dataset.filter;
            filters.forEach(b => b.classList.toggle('is-active', b === btn));
            items.forEach(item => {
                const type = item.dataset.resultType;
                const show = filter === 'all' || type === filter;
                item.hidden = !show;
                item.style.display = show ? '' : 'none';
            });
        });
    });

    const ring = document.querySelector('.mock-result-score-ring');
    if (ring) {
        requestAnimationFrame(() => ring.classList.add('is-animated'));
    }
})();
