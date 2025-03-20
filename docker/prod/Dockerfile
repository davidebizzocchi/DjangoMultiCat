# docker/preprod/Dockerfile
# 2024-12-26

# set base image
ARG BASE_IMAGE=python:3.13.1-slim-bookworm

# Usa l'argomento come immagine base
FROM ${BASE_IMAGE} AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file and install dependencies
COPY docker/preprod/requirements.txt /code/
RUN apt-get update \
    && pip install --upgrade pip 
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /code/wheels -r requirements.txt



FROM ${BASE_IMAGE} 

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

# install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd curl poppler-utils tesseract-ocr tesseract-ocr-ita tesseract-ocr-eng \
COPY --from=builder /code/wheels /wheels
RUN pip install --no-cache /wheels/*



# copy entrypoint.sh
COPY docker/preprod/entrypoint.sh .
RUN sed -i 's/\r$//g' $APP_HOME/entrypoint.sh
RUN chmod +x $APP_HOME/entrypoint.sh

# Copy the rest of the application's code
COPY . $APP_HOME

# chown all the files to the app user
# RUN chown -R app:app $APP_HOME
# RUN mkdir -p /home/app/web/uploads
# RUN chown -R app:app /home/app/web/uploads

# change to the app user
# USER app

# Create directory for sphinx
RUN mkdir -p /home/app/web/docs/_build/html 

# run entrypoint.prod.sh
ENTRYPOINT ["/home/app/web/entrypoint.sh"]