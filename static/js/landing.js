
/* ── NAVBAR SCROLL & MENU ── */
const navbar = document.querySelector('.navbar');
const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
const navLinks = document.querySelector('.nav-links');

window.addEventListener('scroll', () => {
  if (window.scrollY > 20) navbar.classList.add('scrolled');
  else navbar.classList.remove('scrolled');
});

if (mobileMenuBtn) {
  mobileMenuBtn.addEventListener('click', () => {
    navLinks.classList.toggle('active');
  });
}

/* ── REVEAL ANIMATIONS ── */
const revealElements = document.querySelectorAll('[data-reveal], .reveal-up, .reveal-right');
const revealOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
const revealObserver = new IntersectionObserver((entries, observer) => {
  entries.forEach(entry => {
    if(entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, revealOptions);
revealElements.forEach(el => revealObserver.observe(el));

/* ── FAQ ACCORDION ── */
document.querySelectorAll('.faq-q').forEach(btn => {
  btn.addEventListener('click', () => {
    const item = btn.parentElement;
    const ans = item.querySelector('.faq-a');
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item').forEach(i => {
      i.classList.remove('open');
      i.querySelector('.faq-a').style.maxHeight = null;
      i.querySelector('.faq-q').setAttribute('aria-expanded', 'false');
    });
    if(!isOpen) {
      item.classList.add('open');
      ans.style.maxHeight = ans.scrollHeight + 'px';
      btn.setAttribute('aria-expanded', 'true');
    }
  });
});

/* ── HELP MODAL ── */
const helpModal = document.getElementById('helpModal');
const openHelpBtn = document.getElementById('openHelpModal');
const closeHelpBtn = document.getElementById('closeHelpModal');

function openModal(){ if(helpModal) { helpModal.classList.add('open'); document.body.style.overflow='hidden'; } }
function closeModal(){ if(helpModal) { helpModal.classList.remove('open'); document.body.style.overflow=''; } }

if(openHelpBtn)  openHelpBtn.addEventListener('click', openModal);
if(closeHelpBtn) closeHelpBtn.addEventListener('click', closeModal);
if(helpModal) helpModal.addEventListener('click', e => { if(e.target===helpModal) closeModal(); });
document.addEventListener('keydown', e => { if(e.key==='Escape') closeModal(); });

/* ── MODAL TABS ── */
document.querySelectorAll('.modal-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.modal-tab').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.modal-content').forEach(c=>c.classList.add('hidden'));
    tab.classList.add('active');
    const target = document.getElementById('mtab-'+tab.dataset.mtab);
    if(target) target.classList.remove('hidden');
  });
});

/* ── SCROLLYTELLING SYNC ── */
const scrollySteps = document.querySelectorAll('.scrolly-step');
const svIcon = document.getElementById('svIcon');
const svTitle = document.getElementById('svTitle');
const svDesc = document.getElementById('svDesc');
const stickyGlow = document.querySelector('.sticky-glow');

const scrollyData = [
  { icon: '🧹', title: 'Veri Temizliği', desc: 'Kirli veriler geçmişte kaldı.', glow: 'rgba(167,139,250,0.3)', hex: 0xa78bfa },
  { icon: '📊', title: 'Çoklu Pano', desc: 'Bütünleşik analiz deneyimi.', glow: 'rgba(249,115,22,0.3)', hex: 0xf97316 },
  { icon: '🤖', title: 'Yerel Yapay Zeka', desc: 'Güvenli, bulutsuz zeka.', glow: 'rgba(244,114,182,0.3)', hex: 0xf472b6 },
  { icon: '🔍', title: 'Dinamik Dilimleyici', desc: 'Gerçek zamanlı filtreleme.', glow: 'rgba(96,165,250,0.3)', hex: 0x60a5fa }
];

if (scrollySteps.length > 0) {
  const scrollyObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if(entry.isIntersecting) {
        scrollySteps.forEach(s => s.classList.remove('active'));
        entry.target.classList.add('active');
        
        const index = Array.from(scrollySteps).indexOf(entry.target);
        if(scrollyData[index]) {
          const infoCard = document.getElementById('svInfoCard');
          if (infoCard) {
            infoCard.style.transform = 'translateY(10px)';
            infoCard.style.opacity = '0';
          }
          
          setTimeout(() => {
            if(svIcon) svIcon.innerText = scrollyData[index].icon;
            if(svTitle) svTitle.innerText = scrollyData[index].title;
            if(svDesc) svDesc.innerText = scrollyData[index].desc;
            
            const svGlow = document.getElementById('svGlow');
            if (svGlow) svGlow.style.background = scrollyData[index].glow;
            
            if (window.THREE && typeof window.threeTargetColor !== 'undefined') {
              window.threeTargetColor = new THREE.Color(scrollyData[index].hex);
            }
            
            if (infoCard) {
              infoCard.style.transform = 'translateY(0)';
              infoCard.style.opacity = '1';
            }
          }, 200);
        }
      }
    });
  }, { rootMargin: '-40% 0px -40% 0px', threshold: 0.1 });

  scrollySteps.forEach(step => scrollyObserver.observe(step));
}


/* ── MAGNETIC BUTTONS ── */
document.querySelectorAll('[data-magnetic]').forEach(btn => {
  btn.addEventListener('mousemove', (e) => {
    const rect = btn.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    btn.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px)`;
  });
  btn.addEventListener('mouseleave', () => {
    btn.style.transform = 'translate(0px, 0px)';
  });
});

/* ── HERO MOCKUP 3D PARALLAX ── */
const heroSection = document.getElementById('hero');
const heroMockup = document.getElementById('heroMockup');

if(heroSection && heroMockup) {
  heroSection.addEventListener('mousemove', (e) => {
    const x = (window.innerWidth / 2 - e.pageX) / 40;
    const y = (window.innerHeight / 2 - e.pageY) / 40;
    heroMockup.style.transform = `rotateY(${x}deg) rotateX(${y + 5}deg)`;
  });
  heroSection.addEventListener('mouseleave', () => {
    heroMockup.style.transform = `rotateY(0deg) rotateX(8deg)`;
  });
}
