(() => {
  const elem = id => document.getElementById(id);
  function filterSlate() {
    const day = elem('day').value;
    const search = elem('game-search').value.trim().toLowerCase();
    let count = 0;
    document.querySelectorAll('.date-group').forEach(group => {
      let perDay = 0;
      group.querySelectorAll('.game').forEach(game => {
        game.hidden = (day && day !== group.dataset.day) || !game.dataset.search.includes(search);
        if (!game.hidden) perDay++;
      });
      group.hidden = !perDay;
      count += perDay;
    });
    elem('game-empty').hidden = count !== 0;
    elem('announce').textContent = count + ' matchups shown.';
  }
  function filterCirca() {
    const top = elem('rank-filter').value === 'top';
    const search = elem('contest-search').value.trim().toLowerCase();
    let count = 0;
    document.querySelectorAll('.contest-game').forEach(game => {
      game.hidden = (top && Number(game.dataset.rank) > 5) || !game.dataset.search.includes(search);
      if (!game.hidden) count++;
    });
    elem('contest-empty').hidden = count !== 0;
    elem('announce').textContent = (2 * count) + ' contest sides shown.';
  }
  elem('day').addEventListener('change', filterSlate);
  elem('game-search').addEventListener('input', filterSlate);
  elem('rank-filter').addEventListener('change', filterCirca);
  elem('contest-search').addEventListener('input', filterCirca);
  elem('weights').addEventListener('change', event => {
    document.querySelectorAll('[data-weight]').forEach(row => { row.hidden = row.dataset.weight !== event.target.value; });
    elem('announce').textContent = 'Seven model objectives shown for the selected weighting.';
  });
  const share = elem('share');
  share.hidden = false;
  share.addEventListener('click', async () => {
    const url = location.origin + location.pathname + location.hash;
    try {
      if (navigator.share) { await navigator.share({ title: document.title, url }); return; }
      await navigator.clipboard.writeText(url);
      share.textContent = 'Link copied';
    } catch (error) {
      if (error.name !== 'AbortError') window.prompt('Copy this page link', url);
    }
  });
})();

(() => {
  const picker = document.getElementById('market-matchup');
  if (!picker) return;
  picker.addEventListener('change', () => {
    for (const table of document.querySelectorAll('[data-market-game]')) {
      table.hidden = table.dataset.marketGame !== picker.value;
    }
    document.getElementById('announce').textContent = 'Market comparisons updated for ' + picker.selectedOptions[0].textContent;
  });
})();
