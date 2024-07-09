# docker exec -it securityhub-dev tail -F /var/log/mail.log /volume/planckproxy.log
docker compose logs -f -n 200
