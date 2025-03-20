# Dockerfile per supelearn.azurecr.io/superlearn-nginx:preprod
# docker/prod/nginx/Dockerfile

FROM nginx:1.27.4-alpine3.21
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d