(function () {
  var lastCalledNumber = document.body.dataset.lastCalled || '';

  function sendBrowserNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
      var notif = new Notification(title, { body: body, requireInteraction: true });
      setTimeout(function () { notif.close(); }, 15000);
    }
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
    } catch (e) {}
  }

  function statusBadgeHtml(status, statusDisplay) {
    if (status === 'waiting') return '<span class="inline-flex border-2 border-black bg-[#FFD600] px-2 py-0.5 text-[10px] font-black uppercase shadow-[2px_2px_0px_0px_#000]">Pending</span>';
    if (status === 'called' || status === 'serving') return '<span class="inline-flex border-2 border-black bg-[#2D5BFF] px-2 py-0.5 text-[10px] font-black uppercase text-white shadow-[2px_2px_0px_0px_#000]">Diproses</span>';
    if (status === 'done') return '<span class="inline-flex border-2 border-black bg-[#00E676] px-2 py-0.5 text-[10px] font-black uppercase shadow-[2px_2px_0px_0px_#000]">Selesai</span>';
    if (status === 'skipped') return '<span class="inline-flex border-2 border-black bg-neutral-200 px-2 py-0.5 text-[10px] font-black uppercase shadow-[2px_2px_0px_0px_#000]">Dilewati</span>';
    return '<span class="inline-flex border-2 border-black bg-red-400 px-2 py-0.5 text-[10px] font-black uppercase text-white shadow-[2px_2px_0px_0px_#000]">' + statusDisplay + '</span>';
  }

  function rowClass(status) {
    if (status === 'called' || status === 'serving') return 'bg-blue-50';
    if (status === 'done') return 'bg-green-50/50';
    return '';
  }

  window.refreshQueue = function () {
    // Jangan fetch jika tab di background
    if (document.visibilityState !== 'visible') return;

    fetch(document.body.dataset.queueApi)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.current && data.current.number !== lastCalledNumber) {
          lastCalledNumber = data.current.number;
          var el = document.getElementById('callNotification');
          document.getElementById('notifTitle').textContent = 'Nomor ' + data.current.number + ' Dipanggil!';
          document.getElementById('notifMessage').textContent = 'Silakan menuju ' + data.current.counter + '. Nama: ' + data.current.name;
          if (el) { el.classList.remove('is-hidden'); el.classList.add('is-visible'); }
          sendBrowserNotification('Antrian Dipanggil!', 'Antrian ' + data.current.number + ' — menuju ' + data.current.counter);
          playBeepAlert();
        }
        if (data.all_tickets && data.all_tickets.length > 0) {
          var html = '';
          data.all_tickets.forEach(function (t) {
            html += '<tr class="' + rowClass(t.status) + '"><td class="px-4 py-3 font-black sm:px-5">' + t.number + '</td><td class="px-4 py-3 font-mono text-xs font-semibold text-neutral-600 sm:px-5">' + t.tracking + '</td><td class="px-4 py-3 font-semibold sm:px-5">' + t.name + '</td><td class="px-4 py-3 sm:px-5">' + t.service + '</td><td class="px-4 py-3 font-medium sm:px-5">' + t.time + '</td><td class="px-4 py-3 sm:px-5">' + statusBadgeHtml(t.status, t.status_display) + '</td></tr>';
          });
          document.getElementById('queueTableBody').innerHTML = html;
        }
        var li = document.getElementById('liveIndicator');
        if (li) { li.classList.add('text-brand-green'); setTimeout(function () { li.classList.remove('text-brand-green'); }, 500); }
      })
      .catch(function () {});
  };

  if ('Notification' in window && Notification.permission === 'default') Notification.requestPermission();

  // Refresh langsung saat tab kembali aktif
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') window.refreshQueue();
  });

  setInterval(window.refreshQueue, 5000);
})();
