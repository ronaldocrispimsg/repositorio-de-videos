const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8001;
const STREAM_PATH = path.resolve(process.env.STREAM_PATH || '/processed_videos');
const STREAM_BASE_URL = (process.env.STREAM_BASE_URL || 'http://localhost:8001/streams').replace(/\/+$/, '');

// Garante que o diretório de streams existe
if (!fs.existsSync(STREAM_PATH)) {
  fs.mkdirSync(STREAM_PATH, { recursive: true });
}

app.use(cors());
app.use(express.json());

// Servir arquivos estáticos de streaming (.m3u8 e .ts) com CORS liberado
app.use('/streams', express.static(STREAM_PATH));

// Healthcheck
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Multer para upload de segmentos de streaming em memória temporária
const upload = multer({ storage: multer.memoryStorage() });

// Endpoint: Receber segmento individual (.ts ou .m3u8)
app.post('/videos/:videoId/segments', upload.single('file'), async (req, res) => {
  try {
    const { videoId } = req.params;
    const relativePath = (req.body.relative_path || (req.file ? req.file.originalname : '')).replace(/^\/+/, '').replace(/\.\./g, '');

    if (!req.file || !relativePath) {
      return res.status(400).json({ error: 'Arquivo ou caminho relativo inválido.' });
    }

    const targetPath = path.join(STREAM_PATH, videoId, relativePath);
    const targetDir = path.dirname(targetPath);

    await fs.promises.mkdir(targetDir, { recursive: true });
    await fs.promises.writeFile(targetPath, req.file.buffer);

    return res.json({ status: 'stored', path: targetPath });
  } catch (error) {
    console.error('[repository] Erro ao salvar segmento:', error);
    return res.status(500).json({ error: error.message });
  }
});

// Endpoint: Finalizar upload e obter URL da playlist
app.post('/videos/:videoId/complete', (req, res) => {
  const { videoId } = req.params;
  const playlistName = req.body.playlist_name || 'playlist.m3u8';
  const playlistPath = path.join(STREAM_PATH, videoId, playlistName);

  if (!fs.existsSync(playlistPath)) {
    return res.status(400).json({ detail: 'Playlist não encontrada' });
  }

  const streamUrl = `${STREAM_BASE_URL}/${videoId}/${playlistName}`;
  return res.json({ stream_url: streamUrl });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`[repository] Servidor rodando na porta ${PORT}`);
  console.log(`[repository] Diretório de streams: ${STREAM_PATH}`);
  console.log(`[repository] URL base de streaming: ${STREAM_BASE_URL}`);
});
