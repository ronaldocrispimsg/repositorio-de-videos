# Frontend Vanilla (HTML, CSS, JS)

Frontend simples e cru, sem frameworks, feito para você escrever e editar o código diretamente sem complexidade de build.

## Estrutura dos Arquivos

- `index.html`: Estrutura HTML da página (upload, player e lista de vídeos).
- `style.css`: Estilização simples e pura com CSS nativo.
- `app.js`: Lógica em JavaScript puro para envio de arquivos, consulta à API e execução no player.
- `nginx.conf` & `Dockerfile`: Usado apenas para empacotar no Docker na porta `3000`.

## Como Rodar

### Opção 1: Via Docker Compose (recomendado junto com todo o projeto)
Na raiz do repositório:
```bash
docker compose up -d --build
```
Acesse `http://localhost` (ou `http://localhost:3000`).

### Opção 2: Localmente sem Docker
Você pode abrir o arquivo `index.html` diretamente no seu navegador, ou usar qualquer servidor estático simples:
```bash
# Python
python3 -m http.server 3000

# Ou extensão "Live Server" do VS Code
```
