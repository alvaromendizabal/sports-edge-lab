/* Later weather forecasts are display context, never model inputs or pick adjustments. */
(() => {
  'use strict';
  const script = document.currentScript;
  const weatherUrl = new URL('weather.json', script.src);
  const modelIssue = '2026-11-27T23:06:11.996730+00:00';
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const clock = value => value && Number.isFinite(Date.parse(value))
    ? new Date(value).toLocaleString('en-US', {timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}) + ' PT'
    : 'unavailable';
  const degrees = value => finite(value) ? Math.round(value * 9 / 5 + 32) + '°F' : 'Temperature unavailable';
  const speed = value => finite(value) ? Math.round(value * 2.2369362921) + ' mph' : 'unavailable';
  const human = value => value && typeof value === 'object' ? human(value.status) : value ? String(value).replaceAll('_', ' ') : 'unknown';
  const cards = [...document.querySelectorAll('article[data-state="upcoming"]')];
  const slots = new Map();
  for (const card of cards) {
    const panel = element('details', undefined, 'venue-weather');
    panel.dataset.weatherGame = card.dataset.gameId;
    panel.append(element('summary', 'Venue forecast · loading'));
    card.append(panel); slots.set(card.dataset.gameId, panel);
  }
  const unavailable = (panel, message) => {
    panel.replaceChildren(element('summary', 'Venue forecast · unavailable'), element('p', message));
    panel.dataset.weatherStatus = 'UNAVAILABLE';
  };
  fetch(weatherUrl, {cache:'no-cache'}).then(response => {
    if (!response.ok) throw new Error('Weather forecast source unavailable');
    return response.json();
  }).then(data => {
    if (data.model_application !== 'NOT_APPLIED_TO_N211_PICKS' || !Array.isArray(data.games)) throw new Error('Unqualified weather display');
    const observations = new Map(data.games.map(game => [game.game_id, game]));
    for (const [id, panel] of slots) {
      const game = observations.get(id);
      if (!game) { unavailable(panel, 'No weather forecast is available for this venue. The saved model picks are unchanged.'); continue; }
      const samples = Array.isArray(game.samples) ? game.samples : [];
      const kickoff = samples.find(sample => sample.offset_hours === 0);
      const venue = game.venue || {};
      const type = String(venue.structural_roof || '').toLowerCase();
      const roofInfo = venue.roof_status || {};
      const announced = roofInfo.source_url && (roofInfo.announced_utc || roofInfo.announcement_utc);
      const roofState = announced && ['open','closed'].includes(roofInfo.status) ? roofInfo.status : 'unknown';
      const venueLabel = type === 'fixed_closed' ? 'Enclosed stadium · fixed roof'
        : type === 'fixed_open' ? 'Open-air stadium'
        : type === 'retractable' ? 'Retractable roof · status ' + roofState
        : type.includes('canopy') ? 'Open-air canopy' : 'Roof type unknown';
      const exposure = type === 'fixed_closed' ? 'Enclosed stadium · outdoor forecast'
        : type === 'retractable' ? 'Retractable roof · ' + roofState + ' · outdoor forecast'
        : venueLabel + (type === 'fixed_open' || type.includes('canopy') ? ' forecast' : ' · outdoor forecast');
      const headline = kickoff ? degrees(kickoff.temperature_c) + ' · wind ' + speed(kickoff.wind_mps) : 'forecast unavailable';
      panel.replaceChildren(element('summary', exposure + ' · ' + headline));
      panel.dataset.weatherStatus = game.status || 'UNAVAILABLE';
      panel.append(element('p', [venue.name || 'Venue', venueLabel].join(' · '), 'weather-venue'));
      panel.append(element('p', (game.status === 'AVAILABLE' ? 'Forecast captured ' + clock(game.captured_utc || data.captured_utc) + ' · forecast updated ' + clock(game.forecast_issued_utc) : 'Forecast check ' + clock(data.captured_utc) + ' · source unavailable') + '.', 'weather-clock'));
      panel.append(element('p', 'Later forecast capture; not used in the frozen N211 picks issued ' + clock(modelIssue) + '. No probabilities have been adjusted.', 'weather-separation'));
      if (game.status !== 'AVAILABLE') panel.append(element('p', 'Forecast coverage: ' + human(game.status) + '. Missing forecast fields remain unavailable.'));
      const wrapper = element('div', undefined, 'weather-table-wrap');
      const table = element('table'); table.setAttribute('aria-label', 'Venue forecast through the game');
      const head = element('thead'), labels = element('tr');
      for (const label of ['Game window', 'Temperature', 'Wind / gust', 'Precipitation']) labels.append(element('th', label));
      head.append(labels); table.append(head);
      const body = element('tbody');
      for (const offset of [0, 2, 4]) {
        const sample = samples.find(row => row.offset_hours === offset) || {};
        const row = element('tr'); row.dataset.weatherOffset = String(offset);
        const window = element('td', offset === 0 ? 'Kickoff' : '+' + offset + ' hours');
        window.append(element('small', clock(sample.valid_utc)));
        row.append(window, element('td', degrees(sample.temperature_c)), element('td', speed(sample.wind_mps) + ' / ' + speed(sample.gust_mps)));
        const probability = finite(sample.precip_probability) && sample.precip_probability >= 0 && sample.precip_probability <= 1
          ? Math.round(100 * sample.precip_probability) + '% chance' : 'Chance unavailable';
        const rain = finite(sample.precip_mm) ? (sample.precip_mm / 25.4).toFixed(2) + ' in precipitation' : 'Amount unavailable';
        const snow = finite(sample.snow_mm) ? (sample.snow_mm / 25.4).toFixed(2) + ' in snow' : 'Snow unavailable';
        const cell = element('td', probability); cell.append(element('small', rain), element('small', snow)); row.append(cell); body.append(row);
      }
      table.append(body); wrapper.append(table); panel.append(wrapper);
      const context = type.includes('canopy')
        ? 'Approximate outdoor stadium-grid forecast. The canopy covers the field, but no wind attenuation inside the bowl is assumed.'
        : type === 'fixed_closed'
          ? 'This enclosed stadium has a fixed roof. The figures are outside ambient forecasts, not indoor playing conditions or on-field measurements.'
          : type === 'retractable'
            ? 'Approximate outdoor stadium-grid forecast, not on-field measurements or an estimate of indoor conditions. Roof status: ' + roofState + '.'
            : 'Approximate outdoor stadium-grid forecast, not on-field measurements. Conditions and later forecasts may differ.';
      panel.append(element('p', context, 'weather-context'));
      if (typeof game.venue_source_url === 'string' && game.venue_source_url.startsWith('https://')) {
        const venueLink = element('a', 'Venue / roof source');venueLink.href=game.venue_source_url;venueLink.target='_blank';venueLink.rel='noopener noreferrer';panel.append(venueLink, document.createTextNode(' · '));
      }
      if (typeof game.source_url === 'string' && game.source_url.startsWith('https://')) {
        const link = element('a', 'Open the weather source');link.href=game.source_url;link.target='_blank';link.rel='noopener noreferrer';panel.append(link);
      }
    }
    document.documentElement.dataset.weatherLoaded = 'true';
  }).catch(() => {
    for (const panel of slots.values()) unavailable(panel, 'The weather forecast could not be loaded. Saved model picks are unchanged.');
    document.documentElement.dataset.weatherLoaded = 'unavailable';
  });
})();
