# VideoBox

**Sistema Distribuído para Upload, Processamento e Consumo de Vídeos**

---

## Contexto

O **VideoBox** é um sistema distribuído desenvolvido como trabalho final da disciplina **Sistemas Distribuídos**, com o objetivo de aplicar conceitos como **arquitetura orientada a eventos**, **processamento assíncrono**, **orquestração de serviços** e **streaming de mídia**.

O sistema permite que usuários façam upload de vídeos e os assistam posteriormente utilizando o protocolo **HLS (HTTP Live Streaming)**, após processamento distribuído.

---

## Objetivos

1. Implementar um sistema distribuído realista
2. Utilizar as tecnologias **K3s, KEDA, RabbitMQ, NGINX e FastAPI**
3. Permitir o upload de vídeos pelos usuários
4. Permitir o consumo dos vídeos via **HLS**
5. Aplicar comunicação assíncrona baseada em eventos
6. Demonstrar escalabilidade horizontal orientada a eventos no processamento de vídeos

---

## Arquitetura & Stack

O sistema é composto por módulos modulares, cada um encapsulado em seu próprio container com Dockerfile e configurações em arquivos `.env`:

### NGINX (Gateway)

* Atua como **entrypoint do sistema** (porta 80)
* Responsável por:
  * API Gateway
  * Reverse proxy
  * Centralização do acesso aos serviços
  * Roteamento para frontend (`/`), backend (`/api/`) e RabbitMQ (`/message/`)

---

### Backend (FastAPI)

* Responsável pelas **APIs RESTful** (porta 8000)
* Implementa as **regras de negócio**
* Cria e publica eventos no **RabbitMQ**
* Gerencia metadados e status dos vídeos
* Disponibiliza download do arquivo bruto original

---

### Frontend (HTML, CSS e JavaScript Puro)

* Interface leve e limpa, sem frameworks adicionais
* Permite:
  * Upload de vídeos
  * Monitoramento de status em tempo real
  * Reprodução direta via player com suporte a HLS (`hls.js`)
* Comunicação via API REST com o backend

---

### RabbitMQ

* Broker de mensagens (AMQP na porta 5672 e painel na porta 15672)
* Utiliza imagem oficial pronta com plugin de gerenciamento
* Responsável pela **comunicação assíncrona orientada a eventos**
* Desacopla o recebimento, a fila de processamento e a entrega

---

### Process (FFMPEG Worker)

* Serviço worker responsável pelo **processamento dos vídeos**
* Consome a fila do RabbitMQ e executa o **FFMPEG** para converter arquivos brutos (`mp4`, `mov`, `mkv`, etc.) em:
  * Playlists `m3u8`
  * Segmentos HLS (`.ts`)
* Envia os fragmentos processados para o serviço `repository` e notifica o término

---

### Repository (Streaming & Storage)

* Serviço FastAPI responsável por receber e armazenar os segmentos HLS na pasta compartilhada `processed_videos`
* Serve diretamente as playlists e fragmentos via HTTP (porta 8001) para consumo do player
* Habilita CORS para transmissões sem bloqueio no navegador

---

### K3s & KEDA (Orquestração e Escalabilidade)

* **K3s**: Orquestrador leve de containers para o cluster distribuído
* **KEDA**: Responsável pelo autoscaling orientado a eventos (HPA)
* Monitora a fila `video.uploaded` no RabbitMQ e ajusta dinamicamente a quantidade de réplicas do `process`:
  * Escala a 0 quando não há vídeos a processar (economia de recursos)
  * Sobe réplicas sob demanda para processar múltiplos vídeos em paralelo
* Persistência de arquivos através de volumes compartilhados (`storage.yaml`)

---

## Fluxo de Funcionamento

1. O usuário seleciona e envia um vídeo pelo frontend.
2. O backend salva o arquivo bruto temporariamente e emite o evento `video.uploaded` no RabbitMQ.
3. O worker **Process**:
   * Consome o evento `video.uploaded`
   * Emite `video.processing` para atualizar o status no sistema
   * Baixa o arquivo do backend e executa o FFMPEG para gerar o streaming HLS
4. Concluída a conversão, o **Process**:
   * Envia os fragmentos e a playlist para a pasta `processed_videos` do **Repository**
   * Emite o evento `video.ready` com a URL do stream gerado
5. O backend recebe `video.ready` e marca o vídeo como pronto.
6. O frontend atualiza a lista e o usuário assiste ao vídeo via **HLS** no player.

---

## Eventos do Sistema

| Evento | Origem | Destino | Descrição |
| --- | --- | --- | --- |
| `video.uploaded` | Backend | Process | Novo vídeo enviado e disponível para conversão |
| `video.processing` | Process | Backend | Conversão iniciada pelo FFMPEG |
| `video.ready` | Process | Backend / Frontend | Conversão finalizada e streaming HLS disponível |

---

## Estrutura do Projeto

```text
/backend      # API FastAPI e regras de negócio
/frontend     # Interface em HTML, CSS e JS puro
/process      # Worker de conversão FFMPEG
/rabbitMQ     # Broker RabbitMQ com dashboard
/repository   # Servidor de streaming e armazenamento (processed_videos)
/nginx        # Gateway e proxy reverso
/infra        # Manifestos K3s (Deployment, KEDA ScaledObject, Storage)
```

---

## Instalação e Execução

### Pré-requisitos

* Docker
* Docker Compose

### Configuração

Cada módulo possui um arquivo `.env.example` pré-configurado. Para utilizá-los, basta copiar ou renomear para `.env` em cada diretório (o projeto já conta com valores padrão funcionais).

### Execução Local (Docker Compose)

1. Clone o repositório
2. Acesse a pasta do projeto
3. Execute:

```bash
docker compose up --build
```

4. Acessos locais disponíveis:
   * **Aplicação Web (Frontend)**: `http://localhost` (ou `http://localhost:3000`)
   * **API Backend**: `http://localhost:8000/docs`
   * **Servidor de Streams (Repository)**: `http://localhost:8001/docs`
   * **Painel RabbitMQ**: `http://localhost:15672` (usuário: `videobox` / senha: `123456`)
