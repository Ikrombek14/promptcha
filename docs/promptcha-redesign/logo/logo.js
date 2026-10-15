// Promptcha logo holatini almashtiradi: 'intro' | 'loading' | 'done' | null
export function pcPlay(el, state) {
  el.classList.remove('is-intro', 'is-loading', 'is-done');
  void el.getBoundingClientRect(); // animatsiyani boshidan boshlash uchun
  if (state) el.classList.add('is-' + state);
}

// Kirish animatsiyasi sessiyada faqat bir marta
export function pcIntroOnce(el) {
  let seen = false;
  try { seen = sessionStorage.getItem('pc-intro') === '1'; } catch (e) {}
  if (seen) return;
  pcPlay(el, 'intro');
  try { sessionStorage.setItem('pc-intro', '1'); } catch (e) {}
}

// Misol: prompt yaratish
// pcPlay(logo, 'loading');               // 300 ms dan keyin, agar javob hali kelmagan boʻlsa
// await fetch('/api/generate', ...);
// pcPlay(logo, 'done');
