// ============================================================
// CONFIGURAÇÃO DA API
// ============================================================
// Quando acessado via gateway (porta 80), as requisições vão para '/api'.
// Quando aberto diretamente (ex: Live Server ou porta 3000), aponta para 'http://localhost:8000'.
const API_BASE = (window.location.port === "80" || window.location.port === "") && window.location.protocol.startsWith("http")
  ? "/api"
  : "http://localhost:8000";

// Elementos da página
const uploadForm = document.getElementById("uploadForm");
const videoFileInput = document.getElementById("videoFileInput");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");

const videoPlayer = document.getElementById("videoPlayer");
const playerCurrent = document.getElementById("playerCurrent");

const videoList = document.getElementById("videoList");
const loadingMsg = document.getElementById("loadingMsg");
const refreshBtn = document.getElementById("refreshBtn");

let currentHlsInstance = null;

// ============================================================
// MENSAGENS DE STATUS DE UPLOAD
// ============================================================
function showStatus(message, type = "info") {
  uploadStatus.textContent = message;
  uploadStatus.className = `status-msg ${type}`;
}

function clearStatus() {
  uploadStatus.textContent = "";
  uploadStatus.className = "status-msg";
}

// ============================================================
// UPLOAD DE VÍDEO
// ============================================================
uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const file = videoFileInput.files[0];
  if (!file) {
    showStatus("Por favor, selecione um arquivo de vídeo.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  uploadBtn.disabled = true;
  showStatus(`Enviando "${file.name}"...`, "info");

  try {
    const response = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Erro ${response.status}: falha ao enviar vídeo.`);
    }

    const data = await response.json();
    showStatus(`Vídeo "${data.filename || file.name}" enviado com sucesso!`, "success");
    videoFileInput.value = "";

    // Atualiza a lista após o envio
    await fetchVideos();
  } catch (error) {
    console.error("Erro no upload:", error);
    showStatus(`Erro ao enviar: ${error.message}`, "error");
  } finally {
    uploadBtn.disabled = false;
  }
});

// ============================================================
// LISTAGEM DE VÍDEOS
// ============================================================
async function fetchVideos() {
  loadingMsg.style.display = "block";
  loadingMsg.textContent = "Carregando vídeos...";

  try {
    const response = await fetch(`${API_BASE}/videos`);
    if (!response.ok) {
      throw new Error(`Erro ${response.status} ao buscar vídeos.`);
    }

    const videos = await response.json();
    renderVideoList(videos);
  } catch (error) {
    console.error("Erro ao listar vídeos:", error);
    loadingMsg.style.display = "block";
    loadingMsg.textContent = `Não foi possível carregar os vídeos (${error.message}).`;
  }
}

function renderVideoList(videos) {
  videoList.innerHTML = "";

  if (!videos || videos.length === 0) {
    loadingMsg.style.display = "block";
    loadingMsg.textContent = "Nenhum vídeo encontrado. Envie um vídeo pelo formulário acima!";
    return;
  }

  loadingMsg.style.display = "none";

  videos.forEach((video) => {
    const li = document.createElement("li");
    li.className = "video-item";

    // Informações do vídeo
    const infoDiv = document.createElement("div");
    infoDiv.className = "video-info";

    const nameP = document.createElement("p");
    nameP.className = "video-name";
    nameP.textContent = video.filename || video.video_id;

    const idP = document.createElement("p");
    idP.className = "video-id";
    idP.textContent = `ID: ${video.video_id}`;

    infoDiv.appendChild(nameP);
    infoDiv.appendChild(idP);

    // Status Badge
    const badge = document.createElement("span");
    badge.className = `badge ${video.status || "uploaded"}`;
    badge.textContent = video.status || "uploaded";

    // Ações
    const actionsDiv = document.createElement("div");
    actionsDiv.className = "video-actions";

    // Botão Assistir (se estiver pronto e tiver stream_url)
    if (video.status === "ready" && video.stream_url) {
      const playBtn = document.createElement("button");
      playBtn.type = "button";
      playBtn.textContent = "Assistir";
      playBtn.addEventListener("click", () => {
        playVideo(video.stream_url, video.filename || video.video_id);
      });
      actionsDiv.appendChild(playBtn);
    }

    // Link para Download do arquivo bruto
    if (video.download_url) {
      const downloadLink = document.createElement("a");
      downloadLink.href = video.download_url;
      downloadLink.className = "btn-link";
      downloadLink.textContent = "Baixar";
      downloadLink.setAttribute("download", "");
      actionsDiv.appendChild(downloadLink);
    }

    li.appendChild(infoDiv);
    li.appendChild(badge);
    li.appendChild(actionsDiv);
    videoList.appendChild(li);
  });
}

// ============================================================
// REPRODUÇÃO DE VÍDEO NO PLAYER
// ============================================================
function playVideo(streamUrl, filename) {
  playerCurrent.textContent = `Reproduzindo agora: ${filename}`;

  // Se houver uma instância anterior de hls.js, destrói para evitar conflito
  if (currentHlsInstance) {
    currentHlsInstance.destroy();
    currentHlsInstance = null;
  }

  const isHls = streamUrl.includes(".m3u8");

  if (isHls && window.Hls && Hls.isSupported()) {
    currentHlsInstance = new Hls();
    currentHlsInstance.loadSource(streamUrl);
    currentHlsInstance.attachMedia(videoPlayer);
    currentHlsInstance.on(Hls.Events.MANIFEST_PARSED, () => {
      videoPlayer.play().catch((err) => console.log("Autoplay bloqueado pelo navegador:", err));
    });
  } else if (videoPlayer.canPlayType("application/vnd.apple.mpegurl")) {
    // Suporte nativo a HLS (Safari / iOS)
    videoPlayer.src = streamUrl;
    videoPlayer.play().catch((err) => console.log("Autoplay bloqueado pelo navegador:", err));
  } else {
    // Fallback normal
    videoPlayer.src = streamUrl;
    videoPlayer.play().catch((err) => console.log("Autoplay bloqueado pelo navegador:", err));
  }

  // Rola suavemente até o player
  videoPlayer.scrollIntoView({ behavior: "smooth", block: "center" });
}

// Botão de atualizar lista
refreshBtn.addEventListener("click", fetchVideos);

// Inicialização ao carregar a página
document.addEventListener("DOMContentLoaded", () => {
  fetchVideos();
});
