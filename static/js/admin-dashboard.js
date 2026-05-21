(function () {
  var apiEndpoint = document.body.dataset.dashboardApi;
  if (!apiEndpoint) return;

  function refreshDashboard() {
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

  // Poll every 3 seconds
  setInterval(refreshDashboard, 3000);
})();
