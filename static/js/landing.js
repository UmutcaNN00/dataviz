// ═══════════════════════════════════════════════════════════
// DATAVIZ RESEARCH — LANDING INTERACTION ENGINE
// ═══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {

  // 1. SCROLL PROGRESS BAR
  window.addEventListener('scroll', () => {
    const winScroll = document.documentElement.scrollTop;
    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const scrolled = (winScroll / height) * 100;
    const bar = document.getElementById('scrollProgress');
    if (bar) bar.style.width = scrolled + '%';
  });

  // 2. HERO INTERACTIVE HYPOTHESIS TABS
  const heroTabs = document.getElementById('heroTabs');
  const heroDynamicBody = document.getElementById('heroDynamicBody');

  const tabContents = {
    anova: {
      metrics: [
        { label: 'F-İstatistiği (F-Value)', val: '14.825', cls: 'highlight-blue', badge: '✓ Gruplar Arası Anlamlı' },
        { label: 'P-Değeri (Asymptotic Sig.)', val: '0.00012', cls: 'highlight-green', badge: 'p < 0.01 (İleri Düzey)' }
      ],
      svg: `
        <svg width="100%" height="95" viewBox="0 0 340 95" class="mock-svg">
          <line x1="40" y1="48" x2="130" y2="48" stroke="#38bdf8" stroke-width="2"/>
          <rect x="60" y="24" width="50" height="48" fill="rgba(56,189,248,0.18)" stroke="#38bdf8" stroke-width="2" rx="4"/>
          <line x1="85" y1="24" x2="85" y2="72" stroke="#f59e0b" stroke-width="2.5"/>

          <line x1="200" y1="48" x2="300" y2="48" stroke="#818cf8" stroke-width="2"/>
          <rect x="225" y="18" width="55" height="60" fill="rgba(129,140,248,0.18)" stroke="#818cf8" stroke-width="2" rx="4"/>
          <line x1="255" y1="18" x2="255" y2="78" stroke="#f59e0b" stroke-width="2.5"/>
        </svg>
      `,
      caption: 'Gruplar Arası Kutu (Box Plot) Yayılımı & Medyan Çizgisi',
      verdict: '<strong>Akademik Yorum:</strong> H₀ Hipotezi Reddedildi. Gruplar arasında %99 güven düzeyinde istatistiksel açıdan anlamlı bir varyans farkı saptanmıştır.'
    },
    regression: {
      metrics: [
        { label: 'Belirlilik Katsayısı (R²)', val: '0.891', cls: 'highlight-gold', badge: '✓ %89.1 Açıklanan Varyans' },
        { label: 'Model Denklemi', val: 'y = 2.41x + 15.3', cls: 'highlight-blue', badge: 'Korelasyon: r = 0.944' }
      ],
      svg: `
        <svg width="100%" height="95" viewBox="0 0 340 95" class="mock-svg">
          <line x1="30" y1="75" x2="310" y2="20" stroke="#f43f5e" stroke-width="2.5"/>
          <polygon points="30,70 310,12 310,28 30,85" fill="rgba(244,63,94,0.15)"/>
          <circle cx="60" cy="70" r="4" fill="#38bdf8"/>
          <circle cx="110" cy="58" r="4" fill="#38bdf8"/>
          <circle cx="170" cy="45" r="4" fill="#38bdf8"/>
          <circle cx="230" cy="35" r="4" fill="#38bdf8"/>
          <circle cx="280" cy="25" r="4" fill="#38bdf8"/>
        </svg>
      `,
      caption: 'Doğrusal Regresyon Eğrisi & %95 Güven Aralığı Bandı',
      verdict: '<strong>Akademik Yorum:</strong> Bağımsız değişken, hedef metrikteki değişimin %89.1\'ini doğrusal olarak açıklamaktadır (p < 0.001).'
    },
    ttest: {
      metrics: [
        { label: 'T-İstatistiği (t)', val: '3.412', cls: 'highlight-indigo', badge: 'Serbestlik Derecesi (df): 98' },
        { label: 'Çift Yönlü P-Değeri', val: '0.0009', cls: 'highlight-green', badge: 'p < 0.01 Düzeyinde Anlamlı' }
      ],
      svg: `
        <svg width="100%" height="95" viewBox="0 0 340 95" class="mock-svg">
          <path d="M 30 80 Q 90 80 120 20 Q 150 80 210 80" fill="rgba(56,189,248,0.15)" stroke="#38bdf8" stroke-width="2"/>
          <path d="M 130 80 Q 190 80 220 25 Q 250 80 310 80" fill="rgba(129,140,248,0.15)" stroke="#818cf8" stroke-width="2"/>
          <line x1="120" y1="20" x2="120" y2="80" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4"/>
          <line x1="220" y1="25" x2="220" y2="80" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4"/>
        </svg>
      `,
      caption: 'İki Bağımsız Örneklem T-Dağılımı Çakışma Analizi',
      verdict: '<strong>Akademik Yorum:</strong> İki grup ortalaması arasındaki fark istatistiksel açıdan anlamlıdır. Ortalamalar şans eseri farklılaşmamıştır.'
    },
    corr: {
      metrics: [
        { label: 'Pearson Katsayısı (r)', val: '+0.884', cls: 'highlight-green', badge: 'Kuvvetli Pozitif Doğrusal İlişki' },
        { label: 'Anlamlılık (2-tailed)', val: '0.0000', cls: 'highlight-blue', badge: 'p < 0.001 Seviyesi' }
      ],
      svg: `
        <svg width="100%" height="95" viewBox="0 0 340 95" class="mock-svg">
          <rect x="50" y="15" width="60" height="60" fill="rgba(56,189,248,0.8)" rx="4"/>
          <text x="80" y="50" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle">1.00</text>
          
          <rect x="140" y="15" width="60" height="60" fill="rgba(56,189,248,0.5)" rx="4"/>
          <text x="170" y="50" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle">0.88</text>
          
          <rect x="230" y="15" width="60" height="60" fill="rgba(56,189,248,0.2)" rx="4"/>
          <text x="260" y="50" fill="#fff" font-size="12" font-weight="bold" text-anchor="middle">0.34</text>
        </svg>
      `,
      caption: 'Pearson Korelasyon Matrisi (Korelasyon Isı Haritası)',
      verdict: '<strong>Akademik Yorum:</strong> İncelenen iki değişken arasında çok yüksek pozitif yönlü ilişki bulunmaktadır.'
    }
  };

  if (heroTabs && heroDynamicBody) {
    heroTabs.addEventListener('click', (e) => {
      const btn = e.target.closest('.c-tab');
      if (!btn) return;
      heroTabs.querySelectorAll('.c-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const tabKey = btn.dataset.tab;
      const data = tabContents[tabKey];
      if (!data) return;

      heroDynamicBody.innerHTML = `
        <div class="metrics-row">
          <div class="metric-box">
            <span class="m-label">${data.metrics[0].label}</span>
            <span class="m-val ${data.metrics[0].cls}">${data.metrics[0].val}</span>
            <span class="m-badge">${data.metrics[0].badge}</span>
          </div>
          <div class="metric-box">
            <span class="m-label">${data.metrics[1].label}</span>
            <span class="m-val ${data.metrics[1].cls}">${data.metrics[1].val}</span>
            <span class="m-badge">${data.metrics[1].badge}</span>
          </div>
        </div>

        <div class="chart-box-mock">
          ${data.svg}
          <div class="chart-caption">${data.caption}</div>
        </div>

        <div class="academic-verdict">
          ${data.verdict}
        </div>
      `;
    });
  }

  // 3. ANIMATED NUMBER COUNTERS (INTERSECTION OBSERVER)
  const counters = document.querySelectorAll('.counter-num');
  let counted = false;

  const countObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !counted) {
        counted = true;
        counters.forEach(counter => {
          const target = +counter.getAttribute('data-target');
          const duration = 1200;
          const stepTime = 20;
          const steps = duration / stepTime;
          const inc = target / steps;
          let current = 0;

          const timer = setInterval(() => {
            current += inc;
            if (current >= target) {
              counter.textContent = target;
              clearInterval(timer);
            } else {
              counter.textContent = Math.ceil(current);
            }
          }, stepTime);
        });
      }
    });
  }, { threshold: 0.3 });

  const countersSection = document.getElementById('counters');
  if (countersSection) countObserver.observe(countersSection);

});
