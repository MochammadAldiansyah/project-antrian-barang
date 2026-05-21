(function () {
  var trackingCode = document.body.dataset.trackingCode;
  var lastStatus = document.body.dataset.initialStatus;
  var pollingActive = true;

  function requestNotifPermission() {
    if (!('Notification' in window)) {
      alert('Browser Anda tidak mendukung notifikasi.');
      return;
    }
    Notification.requestPermission().then(function (permission) {
      var banner = document.getElementById('notifPermBanner');
      if (permission === 'granted' && banner) banner.classList.add('is-hidden');
    });
  }

  window.requestNotifPermission = requestNotifPermission;

  function sendBrowserNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
      var notif = new Notification(title, { body: body, requireInteraction: true });
      setTimeout(function () { notif.close(); }, 15000);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var banner = document.getElementById('notifPermBanner');
    if ('Notification' in window && Notification.permission === 'default' && banner) {
      banner.classList.remove('is-hidden');
      banner.classList.add('is-flex');
    }
  });

  function statusBadgeHtml(status, label) {
    var cls = 'inline-flex border-2 border-black px-3 py-1 text-xs font-black uppercase shadow-brutal-sm';
    if (status === 'waiting') return '<span class="' + cls + ' bg-brand-yellow">Pending</span>';
    if (status === 'called' || status === 'serving') return '<span class="' + cls + ' bg-brand-blue text-white">Diproses</span>';
    if (status === 'done') return '<span class="' + cls + ' bg-brand-green">Selesai</span>';
    return '<span class="' + cls + '">' + label + '</span>';
  }

  function checkTicket() {
    if (!pollingActive || !trackingCode) return;
    // Jangan fetch jika tab di background
    if (document.visibilityState !== 'visible') return;

    fetch('/api/check-ticket/' + trackingCode + '/')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var posEl = document.getElementById('positionDisplay');
        if (posEl) posEl.textContent = data.position > 0 ? data.position : (data.status === 'called' ? '' : '-');
        var badgeEl = document.getElementById('statusBadge');
        if (badgeEl) badgeEl.innerHTML = statusBadgeHtml(data.status, data.status_display);
        if (data.status === 'called' && lastStatus !== 'called') {
          var el = document.getElementById('callNotification');
          document.getElementById('notifTitle').textContent = 'Nomor ' + data.ticket_number + ' Dipanggil!';
          document.getElementById('notifMessage').textContent = 'Silahkan menuju ' + data.counter;
          if (el) { el.classList.remove('is-hidden'); el.classList.add('is-visible'); }
          sendBrowserNotification('Antrian Anda Dipanggil!', 'Antrian ' + data.ticket_number + ' — menuju ' + data.counter);
          playBeepAlert();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        if (data.status === 'done' && lastStatus !== 'done') {
          pollingActive = false;
          sendBrowserNotification('Antrian Selesai', 'Terima kasih! Layanan Anda telah selesai.');
        }
        lastStatus = data.status;
      })
      .catch(function () { });
  }

  function playBeepAlert() {
    try {
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      [880, 1100, 880, 1100].forEach(function (freq, i) {
        setTimeout(function () {
          var osc = ctx.createOscillator();
          var gain = ctx.createGain();
          osc.frequency.value = freq;
          gain.gain.value = 0.4;
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start();
          setTimeout(function () { osc.stop(); }, 220);
        }, i * 320);
      });
    } catch (e) { }
  }

  // Refresh langsung saat tab kembali aktif
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') checkTicket();
  });

  setInterval(checkTicket, 5000);
})();
