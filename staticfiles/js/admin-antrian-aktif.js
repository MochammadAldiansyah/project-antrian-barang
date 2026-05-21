(function () {
  var apiEndpoint = document.body.dataset.antrianAktifApi;
  if (!apiEndpoint) return;

  function refreshAntrianAktif() {
    // Jangan fetch jika tab sedang di background
    if (document.visibilityState !== 'visible') return;

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

  // Refresh langsung saat tab kembali aktif
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') refreshAntrianAktif();
  });

  // Poll setiap 4 detik
  setInterval(refreshAntrianAktif, 4000);
})();
