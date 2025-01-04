# Dockerfile.local

# Local Development Dockerfile

# Use an official Python runtime as a parent image
ARG BASE_IMAGE=python:3.13-slim-bookworm
ARG ENVIROMENT=local

# Usa l'argomento come immagine base
FROM ${BASE_IMAGE} AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /code

# Install necessary packages
RUN apt-get update \
    && apt-get upgrade -y \
    && python -m pip install --upgrade pip \
    && apt-get install -y netcat-openbsd curl poppler-utils tesseract-ocr tesseract-ocr-ita tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*


FROM builder

RUN pip install uv

RUN uv venv /home/packages/.venv

# Copy the requirements file and install dependencies
COPY docker/local/requirements.txt /code
RUN uv pip install --system --no-cache  -r requirements.txt

# Create a non-root user and set permissions
RUN useradd -m nonrootuser
RUN chown -R nonrootuser:nonrootuser /code

# copy entrypoint.sh
COPY django_cat/entrypoint.sh .
RUN sed -i 's/\r$//g' /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

# Switch to non-root user
USER nonrootuser

# Copy the rest of the application's code
#COPY . /code/

# run entrypoint.sh
ENTRYPOINT ["/code/entrypoint.sh"]
