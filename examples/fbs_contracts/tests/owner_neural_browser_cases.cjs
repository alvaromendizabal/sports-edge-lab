'use strict';
const assert=require('node:assert/strict');
exports.run=async page=>{
  await page.locator('[data-period="previous"]').click();
  for(const family of ['v041_pytorch','v041_tensorflow','v041_neural_fixed_equal_blend']){
    await page.selectOption('#model-view',family);
    assert.match(await page.locator('#result-status').innerText(),/^63 games · 7 observed complete · 63 development projections$/);
    assert.match(await page.locator('#game-rows').innerText(),/Owner neural reconstruction/);
    assert.match((await page.locator('#coverage-accounting').innerText()).replace(/\s+/g,' '),/63 all family targets/);
  }
  await page.selectOption('#model-view','v041_pytorch');
  await page.locator('#game-rows button').first().click();
  assert.equal(await page.locator('#dialog-model a').getAttribute('href'),'owner-neural-study.json');
  assert.match(await page.locator('#dialog-model').innerText(),/2026-11-07T/);
  assert.equal(await page.locator('#game-model-comparison tr').count(),26);
  await page.keyboard.press('Escape');
  await page.selectOption('#development-study','v041');
  for(const cohort of ['2024','2025','2026','previous_week','current_week']){
    await page.selectOption('#development-cohort',cohort);
    assert.equal(await page.locator('#development-rows tr').count(),11);
    assert.match(await page.locator('#development-rows').innerText(),/PyTorch/);
    assert.match(await page.locator('#development-rows').innerText(),/TensorFlow/);
  }
  await page.selectOption('#development-cohort','2026');
  assert.match(await page.locator('#metric-deltas').innerText(),/Different or unverified game cohort/);
  await page.selectOption('#development-target','margin');
  assert.doesNotMatch(await page.locator('#metric-deltas').innerText(),/Different or unverified game cohort/);
  await page.selectOption('#development-target','cover');
  assert.equal(await page.locator('#export-metrics').isDisabled(),true);
  assert.match(await page.locator('#development-status').innerText(),/No authenticated exact-line cover cohort/);
  await page.selectOption('#development-target','winner');
  await page.selectOption('#development-study','v039');
  await page.selectOption('#model-view','fixed_equal_blend');
  await page.locator('[data-period="all"]').click();
};
