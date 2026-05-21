(function () {
  var lastCalledNumber = document.body.dataset.initialNumber || '';

  function updateDisplay() {
    // Jangan fetch jika tab di background
    if (document.visibilityState !== 'visible') return;

    fetch('/api/queue-status/')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var numEl = document.getElementById('currentNumber');
        var counterEl = document.getElementById('currentCounter');
        var emptyEl = document.getElementById('currentEmpty');
        var waitEl = document.getElementById('estWait');
        var totalEl = document.getElementById('totalWaiting');
        var upcomingEl = document.getElementById('upcomingList');

        if (data.current && numEl) {
          numEl.textContent = data.current.number;
          numEl.classList.remove('is-empty', 'is-pulse');
          if (!counterEl) {
            counterEl = document.createElement('div');
            counterEl.id = 'currentCounter';
            counterEl.className = 'display-counter-badge';
            numEl.parentNode.insertBefore(counterEl, numEl.nextSibling);
          }
          counterEl.textContent = data.current.counter;
          counterEl.classList.remove('is-hidden');
          if (emptyEl) emptyEl.classList.add('is-hidden');
          if (data.current.number !== lastCalledNumber) {
            numEl.classList.add('is-pulse');
            lastCalledNumber = data.current.number;
            playCallSound();
            setTimeout(function () {
              speakCall(data.current.number, data.current.counter);
            }, 1500);
          }
        } else if (numEl) {
          numEl.textContent = '---';
          numEl.classList.add('is-empty');
          if (counterEl) counterEl.classList.add('is-hidden');
          if (emptyEl) { emptyEl.classList.remove('is-hidden'); emptyEl.textContent = 'Belum ada antrian dipanggil'; }
        }

        if (waitEl) waitEl.textContent = (data.total_waiting * 5) + ' Menit';
        if (totalEl) totalEl.textContent = data.total_waiting + ' Orang';
        if (upcomingEl) {
          if (data.upcoming && data.upcoming.length > 0) {
            upcomingEl.innerHTML = data.upcoming.map(function (t) {
              return '<li class="upcoming-item"><span class="number">' + t.number + '</span></li>';
            }).join('');
          } else {
            upcomingEl.innerHTML = '<li class="upcoming-item"><span class="text-neutral-500">Tidak ada antrian</span></li>';
          }
        }
      })
      .catch(function () {});
  }

  function playCallSound() {
    try {
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      [660, 880, 1100].forEach(function (freq, i) {
        setTimeout(function () {
          var osc = ctx.createOscillator();
          var gain = ctx.createGain();
          osc.frequency.value = freq;
          gain.gain.value = 0.3;
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.start();
          setTimeout(function () { osc.stop(); }, 250);
        }, i * 350);
      });
    } catch (e) {}
  }

  function formatNumberForSpeech(numStr) {
    if (!numStr) return '';
    var parts = numStr.split('-');
    var prefix = parts[0] || '';
    var digits = parts[1] || '';
    
    var spokenDigits = [];
    for (var i = 0; i < digits.length; i++) {
      var char = digits.charAt(i);
      if (char === '0') {
        spokenDigits.push('nol');
      } else {
        spokenDigits.push(char);
      }
    }
    return prefix + ' ' + spokenDigits.join(' ');
  }

  function speakCall(number, counter) {
    if (!('speechSynthesis' in window)) return;
    
    var spokenNumber = formatNumberForSpeech(number);
    var text = "Nomor antrian " + spokenNumber + ", silakan menuju " + counter;

    var utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'id-ID';
    utterance.rate = 0.85;
    utterance.pitch = 1.0;

    // Load Indonesian voice if available
    if (window.speechSynthesis.getVoices) {
      var voices = window.speechSynthesis.getVoices();
      var idVoice = voices.find(function (v) {
        return v.lang.indexOf('id') === 0;
      });
      if (idVoice) {
        utterance.voice = idVoice;
      }
    }

    window.speechSynthesis.speak(utterance);
  }

  // Refresh langsung saat tab kembali aktif
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') updateDisplay();
  });

  // Poll setiap 4 detik
  setInterval(updateDisplay, 4000);
})();
