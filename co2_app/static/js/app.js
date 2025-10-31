document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('celebrateBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      confetti({ particleCount: 150, spread: 80, origin: { y: 0.6 } });
    });
  }
});


