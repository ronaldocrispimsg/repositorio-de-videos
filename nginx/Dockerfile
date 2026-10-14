FROM nginx:1.25-alpine

RUN apk add --no-cache bash gettext

ENV FRONTEND_UPSTREAM=http://frontend:3000 \
    BACKEND_UPSTREAM=http://backend:8000 \
    RABBIT_UPSTREAM=http://rabbitmq:15672 \
    CLIENT_MAX_BODY_SIZE=2G

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY .env /etc/nginx/.env
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
