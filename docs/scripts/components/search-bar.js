document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.querySelector('.search-input');
  const searchButton = document.querySelector('.search-button');
  
  if (searchInput && searchButton) {
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') performSearch();
    });
  }
  
  function performSearch() {
    const query = searchInput.value.trim();
    if (query) {
      if (window.Telegram?.WebApp) {
        Telegram.WebApp.showAlert(`Поиск по запросу: ${query}`);
      } else {
        console.log('Поиск:', query);
      }
      searchInput.value = '';
    }
  }
});