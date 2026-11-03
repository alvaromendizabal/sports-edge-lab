/* Offline aggregate explorer. No requests, dependencies, forecasts or training. */
'use strict';
(() => {
  const payload = JSON.parse(document.getElementById('fbs-payload').textContent);
  const data = payload.latest;
  const byId = Object.fromEntries(data.models.map(m => [m.id, m]));
  const metadata = {
    winner_logloss: ['Log loss', 'lower', 'Natural-log probability loss; lower is better.'],
    winner_brier: ['Brier score', 'lower', 'Mean squared probability error; lower is better.'],
    winner_accuracy: ['Accuracy', 'higher', 'Fraction correct at a fixed 0.5 probability threshold; higher is better.'],
    winner_ece: ['Calibration error (ECE)', 'lower', 'Ten fixed probability bins; descriptive calibration, not independent selection evidence.'],
    winner_mcc: ['Matthews correlation', 'higher', 'Binary prediction/label correlation; higher is better.'],
    margin_mae: ['Mean absolute error', 'lower', 'Average absolute margin error in points; lower is better.'],
    margin_rmse: ['Root mean squared error', 'lower', 'Margin error in points with larger errors weighted more heavily; lower is better.'],
    margin_bias: ['Signed bias', 'zero', 'Predicted minus observed margin; closer to zero is better.'],
    total_mae: ['Mean absolute error', 'lower', 'Average absolute total-points error; lower is better.'],
    total_rmse: ['Root mean squared error', 'lower', 'Total-points error with larger errors weighted more heavily; lower is better.'],
    total_bias: ['Signed bias', 'zero', 'Predicted minus observed total; closer to zero is better.'],
  };
  const season = document.getElementById('study-season');
  const target = document.getElementById('target');
  const metric = document.getElementById('metric');
  const reference = document.getElementById('reference');
  const body = document.querySelector('#comparison-table tbody');
  const chart = document.getElementById('delta-chart');
  const escape = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number = (value, places=6) => Number(value).toFixed(places);
  const signed = value => (value > 0 ? '+' : '') + number(value);
  const status = (value, base, direction) => {
    const change = direction === 'zero' ? Math.abs(value) - Math.abs(base) : value - base;
    if (Math.abs(change) < 1e-12) return ['equal', 'Equal'];
    const improves = direction === 'higher' ? change > 0 : change < 0;
    return improves ? ['improved', 'Lower error / stronger score'] : ['worse', 'Higher error / weaker score'];
  };
  function updateMetricOptions() {
    const previous = metric.value;
    const options = Object.keys(metadata).filter(key => key.startsWith(target.value + '_'));
    metric.innerHTML = options.map(key => `<option value="${key}">${escape(metadata[key][0])}</option>`).join('');
    if (options.includes(previous)) metric.value = previous;
  }
  function render() {
    const rows = data.panels.filter(r => r.season === Number(season.value));
    const key = metric.value, [label, direction, description] = metadata[key];
    const base = rows.find(r => r.model === reference.value);
    if (!base || rows.length !== data.models.length || rows.some(r => r.cohort_sha256 !== base.cohort_sha256 || r.games !== base.games)) {
      throw Error('Comparison cohort integrity failed');
    }
    const baseValue = base.metrics[key];
    const deltas = rows.map(r => r.metrics[key] - baseValue);
    const extent = Math.max(...deltas.map(Math.abs), 1e-12);
    body.innerHTML = rows.map(r => {
      const value = r.metrics[key], delta = value - baseValue;
      const [cls, explanation] = status(value, baseValue, direction);
      const isReference = r.model === reference.value;
      return `<tr data-model="${r.model}" class="${r.model === 'registered-challenger' ? 'challenger' : ''} ${isReference ? 'reference' : ''}"><th scope="row">${escape(byId[r.model].label)}${isReference ? ' · ref.' : ''}</th><td>${r.games}</td><td class="metric-value">${number(value)}</td><td class="delta-text ${cls}">${isReference ? '—' : signed(delta)}</td><td class="sr-only">${isReference ? 'Reference' : explanation}</td></tr>`;
    }).join('');
    chart.innerHTML = rows.map((r, i) => {
      const delta = deltas[i], width = Math.abs(delta) / extent * 47;
      const cls = status(r.metrics[key], baseValue, direction)[0];
      return `<div class="delta-row"><span class="name">${escape(byId[r.model].label)}</span><span class="delta-track"><span class="delta-bar ${cls}" style="left:${delta < 0 ? 50-width : 50}%;width:${width}%"></span></span><span class="delta-number">${delta === 0 ? 'ref.' : signed(delta)}</span></div>`;
    }).join('');
    document.getElementById('comparison-title').textContent = `${season.value} · ${target.options[target.selectedIndex].text} · ${label}`;
    document.getElementById('metric-description').textContent = description;
    document.getElementById('metric-heading').textContent = label;
    document.getElementById('table-caption').textContent = `Seven fixed comparisons on the same ${base.games} historical games. Delta = selected score minus ${byId[base.model].label}.`;
    document.getElementById('chart-caption').textContent = `Difference from ${byId[base.model].label}`;
    document.getElementById('cohort-short').textContent = `Cohort ${base.cohort_sha256.slice(0,16)}…`;
    document.getElementById('selection-status').textContent = `${season.value}: ${base.games} paired games; seven comparisons; ${label}. ${description} Exposed historical evidence only.`;
  }
  target.addEventListener('change', () => {updateMetricOptions(); render();});
  [season, metric, reference].forEach(control => control.addEventListener('change', render));
  document.getElementById('reset-comparison').addEventListener('click', () => {
    season.value = '2025'; target.value = 'winner'; updateMetricOptions();
    metric.value = 'winner_logloss'; reference.value = 'previous-study'; render();
  });
  document.getElementById('download-csv').addEventListener('click', () => {
    const key = metric.value, rows = data.panels.filter(r => r.season === Number(season.value));
    const base = rows.find(r => r.model === reference.value).metrics[key];
    const quote = value => '"' + String(value).replace(/"/g, '""') + '"';
    const lines = [['release','season','public_model','games','metric','value','reference','delta','cohort_sha256','evidence_use'],
      ...rows.map(r => ['V024',r.season,byId[r.model].label,r.games,key,r.metrics[key],byId[reference.value].label,r.metrics[key]-base,r.cohort_sha256,'exposed historical aggregate'])];
    const blob = new Blob([lines.map(row => row.map(quote).join(',')).join('\n')+'\n'], {type:'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = `fbs-v024-${season.value}-${key}.csv`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  document.querySelectorAll('[data-demo]').forEach(button => button.addEventListener('click', () => {
    document.querySelectorAll('[data-demo]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    const result = payload.cohort_demo[button.dataset.demo];
    document.getElementById('demo-state').textContent = result.status;
    document.getElementById('demo-reason').textContent = result.reason;
    document.getElementById('demo-table').hidden = result.status !== 'PAIRED';
  }));
  updateMetricOptions(); render();
})();
