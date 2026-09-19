'use strict';
const search = document.querySelector('[data-module-search]');
if (search) search.addEventListener('input', () => {
  const query = search.value.trim().toLocaleLowerCase();
  let visible = 0;
  document.querySelectorAll('[data-module-card]').forEach(card => {
    card.hidden = !card.dataset.search.includes(query);
    if (!card.hidden) visible += 1;
  });
  document.getElementById('search-count').textContent = `${visible} matching modules`;
});
const confidence = document.querySelector('[data-confidence]');
if (confidence) confidence.addEventListener('input', () => {
  document.getElementById('confidence-value').value = `${confidence.value}%`;
});
let dirty = false;
document.querySelectorAll('[data-dirty-form]').forEach(form => {
  form.addEventListener('input', () => { dirty = true; });
  form.addEventListener('submit', event => {
    dirty = false;
    if (event.submitter?.hasAttribute('data-submit-review')) {
      document.querySelector('[data-submit-status]').textContent = 'Evaluating and saving your research record. Local AI review, when enabled, may take up to 90 seconds.';
      event.submitter.setAttribute('aria-disabled', 'true');
    }
  });
});
window.addEventListener('beforeunload', event => {
  if (dirty) { event.preventDefault(); event.returnValue = ''; }
});
