document.addEventListener('DOMContentLoaded', function() {
  if (window.Telegram?.WebApp) {
    Telegram.WebApp.ready();
    Telegram.WebApp.expand();
    Telegram.WebApp.disableVerticalSwipes();
    
    Telegram.WebApp.BackButton.show();
    Telegram.WebApp.BackButton.onClick(() => {
      Telegram.WebApp.close();
    });
  }

  const roleCards = document.querySelectorAll('.role-card');
  roleCards.forEach(card => {
    card.addEventListener('click', function() {
      const role = this.getAttribute('data-role');
      
      this.style.transform = 'scale(0.95)';
      setTimeout(() => {
        this.style.transform = '';
      }, 150);
      
      setTimeout(() => {
        navigateToDashboard(role);
      }, 200);
    });
  });

  function navigateToDashboard(role) {
    if (window.Telegram?.WebApp) {
      Telegram.WebApp.CloudStorage.setItem('max_user_role', role, () => {
        window.location.href = `dashboard.html?role=${encodeURIComponent(role)}`;
      });
    } else {
      localStorage.setItem('max_user_role', role);
      window.location.href = `dashboard.html?role=${encodeURIComponent(role)}`;
    }
  }
});