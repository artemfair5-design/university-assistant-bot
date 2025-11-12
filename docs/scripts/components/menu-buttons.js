document.addEventListener('DOMContentLoaded', function() {
  const notificationsBtn = document.querySelector('.notifications');
  const userBtn = document.querySelector('.user');
  
  if (notificationsBtn) {
    notificationsBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      if (window.Telegram?.WebApp) {
        Telegram.WebApp.showAlert('У вас 3 новых уведомления');
      } else {
        console.log('Telegram WebApp не доступен');
      }
    });
  }
  
  if (userBtn) {
    userBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      if (window.Telegram?.WebApp) {
        Telegram.WebApp.showAlert('Профиль пользователя');
      } else {
        console.log('Telegram WebApp не доступен');
      }
    });
  }
});