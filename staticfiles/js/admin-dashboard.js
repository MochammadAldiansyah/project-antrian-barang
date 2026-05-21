(function () {
  var apiEndpoint = document.body.dataset.dashboardApi;
  if (!apiEndpoint) return;

  function refreshDashboard() {
    // Jangan fetch jika tab sedang di background (hemat koneksi serverless)
    if (document.visibilityState !== 'visible') return;

    fetch(apiEndpoint)
      .then(function (response) {
        if (!response.ok) throw new Error('Network error');
        return response.json();
      })
      .then(function (data) {
        if (data && data.html) {
          var container = document.getElementById('dashboardContent');
          if (container) {
            container.innerHTML = data.html;
          }
        }
      })
      .catch(function (error) {
        console.error('Error refreshing dashboard:', error);
      });
  }

  // Refresh langsung saat tab kembali aktif
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') refreshDashboard();
  });

  // Poll setiap 5 detik (lebih hemat dari 3 detik)
  setInterval(refreshDashboard, 5000);
})();
