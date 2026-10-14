# k3s nas instâncias VideoBox

Objetivo: permitir que RabbitMQ, Process e NGINX fiquem registrados no cluster para observabilidade, restart automático e provisionamento futuro.

## 1. Control-plane (instância de monitoramento)

1. Atualize o sistema e instale o k3s server:
   ```bash
   curl -sfL https://get.k3s.io | sh -s - server \
     --disable traefik \
     --write-kubeconfig-mode 644
   ```
2. Verifique se está rodando:
   ```bash
   sudo kubectl get nodes
   ```
3. Guarde o token para conectar as instâncias gerenciadas:
   ```bash
   sudo cat /var/lib/rancher/k3s/server/node-token
   ```
4. Libere a porta 6443/TCP no security group para que as demais instâncias consigam se registrar.

## 2. Nós gerenciados (RabbitMQ, Process, NGINX)

Repita em cada instância, substituindo `<MASTER_IP>` e `<TOKEN>`:

```bash
curl -sfL https://get.k3s.io | \
  K3S_URL="https://<MASTER_IP>:6443" \
  K3S_TOKEN="<TOKEN>" \
  sh -s - agent \
  --node-name rabbit-node # altere para process-node/nginx-node etc.
```

Depois confirme no master:

```bash
sudo kubectl get nodes -o wide
```

## 3. Etiquetas úteis

Identifique os serviços para o futuro (DaemonSets/alertas):

```bash
kubectl label node rabbit-node role=rabbitmq
kubectl label node process-node role=processor
kubectl label node nginx-node role=gateway
```

## 4. Monitoramento básico

* Use `kubectl top nodes` (necessita `kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/metrics-server/...`) para métricas.
* Configure `k3s kubectl cordon node && drain` antes de atualizar a instância.

## 5. Distribuição das cargas

| Instância | Componentes locais | Observações |
|-----------|-------------------|-------------|
| `nginx-node` | Container `videobox-gateway` | Expõe Elastic IP, healthz em `/healthz` |
| `process-node` | Container `process/main.py` + agentes FFmpeg | Compartilha EFS com stream_repo |
| `rabbit-node` | Serviço RabbitMQ + plugin management | `/message/` via gateway |

Com todos registrados no k3s é possível usar DaemonSets para instalar agentes (Prometheus node exporter, Falco, etc.) ou orquestrar upgrades automatizados.
