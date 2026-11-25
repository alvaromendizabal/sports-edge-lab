'use strict';
const day = document.getElementById('day');
const role = document.getElementById('role');
const venue = document.getElementById('venue');

function showSelection(selector, key, value, allowAll = false) {
  document.querySelectorAll(selector).forEach(item => {
    item.hidden = !(allowAll && value === 'all') && item.dataset[key] !== value;
  });
}

day.addEventListener('change', () => showSelection('[data-day]', 'day', day.value, true));
role.addEventListener('change', () => showSelection('[data-role]', 'role', role.value));
venue.addEventListener('change', () => showSelection('[data-venue]', 'venue', venue.value));
