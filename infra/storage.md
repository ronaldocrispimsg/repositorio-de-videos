# Storage compartilhado (Process ↔ Stream Repo)

O conversor (`process`) gera os arquivos HLS em `/srv/videobox/export` e o `repo_stream` consome exatamente o mesmo diretório. Para manter os dados consistentes entre instâncias, configure um volume compartilhado (EFS na AWS ou NFS em outra VM).

## 1. Provisionar (EFS)

1. Crie um File System na região das instâncias.
2. Adicione um Mount Target em cada sub-rede privada usada pelos servidores.
3. Abra a porta 2049/TCP no security group para os nós autorizados.

## 2. Montar no servidor Process

Veja `process/comandos_instalar` para a entrada no `/etc/fstab`. Exemplo:

```
fs-12345678.efs.sa-east-1.amazonaws.com:/ /srv/videobox/export nfs4 defaults,_netdev 0 0
```

## 3. Montar no servidor Stream Repo

No `repo_stream`:

```bash
sudo mkdir -p /srv/videobox/export
sudo tee -a /etc/fstab <<'EOF'
fs-12345678.efs.sa-east-1.amazonaws.com:/ /srv/videobox/export nfs4 defaults,_netdev 0 0
EOF
sudo mount -a
sudo chown -R ubuntu:ubuntu /srv/videobox/export
```

E ao iniciar o container:

```bash
docker run -d \
  --name videobox-stream \
  --restart unless-stopped \
  --env RABBIT_URL=amqp://videobox:123456@rabbit.internal/ \
  --env PROCESS_EXPORT_ROOT=/srv/videobox/export \
  --env STREAM_PATH=/var/www/html/streams \
  -v /srv/videobox/export:/srv/videobox/export:ro \
  -v /var/www/html/streams:/var/www/html/streams \
  videobox-stream:latest
```

Assim, o repo_stream copia localmente para `/var/www/html/streams` (servido pelo NGINX interno) e, se `CLEAN_EXPORTED=true`, remove o diretório exportado do EFS.
