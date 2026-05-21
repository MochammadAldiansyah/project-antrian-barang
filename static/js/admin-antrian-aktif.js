(function () {
  var apiEndpoint = document.body.dataset.antrianAktifApi;
  if (!apiEndpoint) return;

  function refreshAntrianAktif() {
    fetch(apiEndpoint)
      .then(function (response) {
        if (!response.ok) throw new Error('Network error');
        return response.json();
      })
      .then(function (data) {
        if (data && data.html) {
          var container = document.getElementById('antrianAktifContent');
          if (container) {
            container.innerHTML = data.html;
          }
        }
      })
      .catch(function (error) {
        console.error('Error refreshing active queue:', error);
      });
  }

  // Poll every 3 seconds
  setInterval(refreshAntrianAktif, 3000);
})();
