# 🎥 VideoBox

**Sistema Distribuído para Upload, Processamento e Consumo de Vídeos**

---

## 📌 Contexto

O **VideoBox** é um sistema distribuído desenvolvido como trabalho final da disciplina **Sistemas Distribuídos**, com o objetivo de aplicar conceitos como **arquitetura orientada a eventos**, **processamento assíncrono**, **orquestração de serviços** e **streaming de mídia**.

O sistema permite que usuários façam upload de vídeos e os assistam posteriormente utilizando o protocolo **HLS (HTTP Live Streaming)**, após processamento distribuído.

---

## 🎯 Objetivos

1. Implementar um sistema distribuído realista
2. Utilizar as tecnologias **K3s, RabbitMQ, NGINX e FastAPI**
3. Permitir o upload de vídeos pelos usuários
4. Permitir o consumo dos vídeos via **HLS**
5. Aplicar comunicação assíncrona baseada em eventos
6. Demonstrar escalabilidade horizontal no processamento de vídeos

---

## 🧱 Arquitetura & Stack

O sistema é composto por **7 módulos principais**, cada um com responsabilidades bem definidas.

### 🔹 NGINX

* Atua como **entrypoint do sistema**
* Responsável por:

  * API Gateway
  * Reverse proxy
  * Centralização do acesso aos serviços
  * Possível habilitação de HTTPS/SSL
* Permite que o frontend e os serviços internos se comuniquem de forma controlada

---

### 🔹 Backend (FastAPI)

* Responsável pelas **APIs RESTful**
* Implementa as **regras de negócio**
* Cria e publica eventos no **RabbitMQ**
* Gerencia metadados dos vídeos
* Atua como coordenador lógico do sistema

---

### 🔹 Frontend (Next.js)

* Interface de interação com o usuário
* Permite:

  * Upload de vídeos
  * Consumo de vídeos via HLS
* Comunicação exclusiva com o backend e com o repositório de streaming

---

### 🔹 RabbitMQ

* Broker de mensagens
* Responsável pela **comunicação assíncrona orientada a eventos**
* Permite o desacoplamento entre backend, processamento e armazenamento

---

### 🔹 K3s

* Atua como **orquestrador**
* Gerencia a quantidade e disponibilidade das instâncias de **Process**
* Permite escalabilidade horizontal do processamento de vídeos

---

### 🔹 Process

* Serviço executado em containers
* Responsável pelo **processamento dos vídeos**
* Utiliza **FFMPEG** para converter arquivos brutos (`mp4`, `mov`, `mkv`) em:

  * Playlists `m3u8`
  * Segmentos HLS
* Publica eventos indicando o progresso e finalização do processamento

---

### 🔹 Repository (RepoStream)

* Serviço responsável por armazenar as playlists e segmentos HLS
* O **frontend consome diretamente** os arquivos deste serviço
* Atua como repositório de streaming

---

## 🔄 Fluxo de Funcionamento

1. O usuário envia um vídeo pelo frontend
2. O backend:

   * Cria os metadados do vídeo
   * Emite o evento `video.uploaded` contendo a localização do arquivo
3. O serviço **Process**:

   * Escuta o evento `video.uploaded`
   * Baixa o vídeo
   * Emite o evento `video.processing`
   * Inicia a conversão para HLS
4. Ao finalizar a conversão, o **Process**:

   * Emite o evento `video.processed` com a localização da playlist
5. O **RepoStream**:

   * Escuta o evento `video.processed`
   * Baixa a playlist
   * Armazena localmente
   * Emite o evento `video.ready`
6. O usuário assiste ao vídeo utilizando **HLS**

---

## 📨 Eventos do Sistema

| Evento             | Descrição                                     |
| ------------------ | --------------------------------------------- |
| `video.uploaded`   | Vídeo enviado e disponível para processamento |
| `video.processing` | Conversão em andamento                        |
| `video.processed`  | Conversão finalizada                          |
| `video.ready`      | Vídeo pronto para consumo via HLS             |

---

## 🗂️ Estrutura do Projeto

```text
/nginx        # Gateway e proxies
/backend      # API FastAPI e regras de negócio
/frontend     # Interface do usuário
/process      # Workers de processamento (FFMPEG)
/repository   # Repositório de playlists HLS
```

---

## ⚙️ Instalação e Execução

### Pré-requisitos

* Docker
* Docker Compose
* Ambiente compatível com containers

### Execução

1. Clone o repositório
2. Acesse a pasta do projeto
3. Execute:

```bash
docker-compose up --build
```

4. Após a inicialização:

   * Acesse `http://localhost:3000`
   * Envie um vídeo
   * Aguarde o processamento
   * Consuma o vídeo via streaming HLS

---

## 👥 Equipe


* **[Ronaldo Crispim](https://github.com/ronaldocrispimsg/)** 
  Backend, RepoStream, RabbitMQ

* **[Marcio Martins](https://github.com/mferrreira)**
  Frontend, Process, K3s, Docker

* **[Vinicius Rodrigues](https://github.com/vinirodriguesz)**
  NGINX
  
---

## 📜 Licença

Este projeto utiliza a licença **MIT**.
Uso acadêmico e educacional.

---

## 🙏 Agradecimentos

Agradecemos ao **Prof. Adriano Antunes** pela excelente condução da disciplina e pelos conhecimentos transmitidos, e ao **IFNMG – Campus Januária** pela oportunidade de desenvolvimento do projeto.
 
---
