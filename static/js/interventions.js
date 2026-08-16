// Learning Support Queue Filter & Action Script
function filterSupportQueue(filterTier) {
  const rows = document.querySelectorAll('.support-queue-row');
  rows.forEach(row => {
    if (filterTier === 'ALL' || row.dataset.priority === filterTier) {
      row.style.display = '';
    } else {
      row.style.display = 'none';
    }
  });
}
