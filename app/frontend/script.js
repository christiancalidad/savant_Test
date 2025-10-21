(() => {
  const btnStart = document.getElementById('btnStart');
  const btnStop = document.getElementById('btnStop');
  const btnSend = document.getElementById('btnSend');
  const statusEl = document.getElementById('status');
  const spinner = document.getElementById('spinner');
  const originalAudio = document.getElementById('originalAudio');
  const replyAudio = document.getElementById('replyAudio');
  const transcriptionEl = document.getElementById('transcription');
  const responseTextEl = document.getElementById('responseText');
  const logEl = document.getElementById('log');

  let mediaRecorder;
  let chunks = [];
  let lastBlob;

  function log(msg) {
    logEl.textContent += `\n${msg}`;
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const options = { mimeType: 'audio/webm' };
      mediaRecorder = new MediaRecorder(stream, options);
      chunks = [];
      mediaRecorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data); };
      mediaRecorder.onstop = () => {
        lastBlob = new Blob(chunks, { type: 'audio/webm' });
        originalAudio.src = URL.createObjectURL(lastBlob);
        btnSend.disabled = false;
        statusEl.textContent = 'Grabación finalizada';
      };
      mediaRecorder.start();
      statusEl.textContent = 'Grabando…';
      btnStart.disabled = true;
      btnStop.disabled = false;
      btnSend.disabled = true;
      log('Grabación iniciada');
    } catch (err) {
      console.error(err);
      log(`Error al iniciar grabación: ${err.message || err}`);
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      btnStart.disabled = false;
      btnStop.disabled = true;
    }
  }

  async function sendToApi() {
    if (!lastBlob) {
      return log('No hay grabación para enviar.');
    }
    spinner.style.display = 'inline';
    statusEl.textContent = 'Enviando…';
    try {
      const form = new FormData();
      // filename with supported extension on backend; we also allow webm in backend
      const file = new File([lastBlob], 'recording.webm', { type: 'audio/webm' });
      form.append('file', file);

      const res = await fetch(`${window.API_BASE}/v1/voice`, {
        method: 'POST',
        body: form,
      });
      const json = await res.json();
      if (!res.ok) {
        throw new Error(`${res.status} ${json?.detail || res.statusText}`);
      }
      transcriptionEl.textContent = json.transcription || '—';
      responseTextEl.textContent = json.response_text || '—';

      if (json.audio_b64 && json.audio_mime_type) {
        replyAudio.src = `data:${json.audio_mime_type};base64,${json.audio_b64}`;
        await replyAudio.play().catch(() => {});
      }
      statusEl.textContent = 'Completado';
      log('Respuesta recibida');
    } catch (err) {
      console.error(err);
      log(`Error en la solicitud: ${err.message || err}`);
      statusEl.textContent = 'Error';
    } finally {
      spinner.style.display = 'none';
    }
  }

  btnStart.addEventListener('click', startRecording);
  btnStop.addEventListener('click', stopRecording);
  btnSend.addEventListener('click', sendToApi);
})();
