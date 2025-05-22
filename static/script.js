navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    document.getElementById("video").srcObject = stream;
  })
  .catch(err => {
    console.error("Kamera hatası:", err);
  });

function captureAndSend() {
  const video = document.getElementById("video");
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const dataURL = canvas.toDataURL("image/jpeg");

  fetch("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: dataURL })
  })
  .then(res => res.json())
  .then(data => {
    showMoodButtons(data.mood);
  });
}

function showMoodButtons(mood) {
  const moodDiv = document.getElementById("moodButtons");
  moodDiv.innerHTML = "";

  const playlists = {
    happy: "https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC",
    sad: "https://open.spotify.com/playlist/37i9dQZF1DX3YSRoSdA634",
    angry: "https://open.spotify.com/playlist/37i9dQZF1DWZLcGGC0HJbc",
    neutral: "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
  };

  const button = document.createElement("button");
  button.innerText = `🎵 ${mood.toUpperCase()} Müzikleri Aç`;
  button.onclick = () => window.open(playlists[mood] || playlists["neutral"], "_blank");
  moodDiv.appendChild(button);
}
