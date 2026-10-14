# Gateway NGINX

Container que expõe a porta pública (Elastic IP) e roteia para:

* `/` → frontend (Next.js)
* `/upload` → backend FastAPI
* `/message/` → painel do RabbitMQ

## Variáveis de ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `FRONTEND_UPSTREAM` | `http://frontend:3000` | Host/porta alcançável pelo gateway para o frontend |
| `BACKEND_UPSTREAM`  | `http://backend:8000`  | Endpoint do FastAPI responsável pelo upload |
| `RABBIT_UPSTREAM`   | `http://rabbitmq:15672` | Painel HTTP do RabbitMQ (porta 15672) |
| `CLIENT_MAX_BODY_SIZE` | `2G` | Limite máximo de upload aceito pelo gateway |

Altere esses valores com `-e VAR=value` ao executar o container ou usando um arquivo `.env`.

## Build & Run

```bash
docker build -t videobox-gateway nginx

docker run -d \
  -p 80:80 \
  -e FRONTEND_UPSTREAM=http://10.0.1.20:3000 \
  -e BACKEND_UPSTREAM=http://10.0.2.15:8000 \
  -e RABBIT_UPSTREAM=http://10.0.3.10:15672 \
  --name gateway videobox-gateway
```

O endpoint `http://<elastic-ip>/healthz` responde `ok` e pode ser usado por k3s/monitoramento.
