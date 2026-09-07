FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data/uploads data/pdf

# The running app has to be able to say which build it is, or nobody can tell what a firm
# is on when they report a bug, and the updater cannot tell a rollback from a no-op.
ARG COIL_VERSION=dev
ARG COIL_COMMIT=unknown
ENV COIL_VERSION=$COIL_VERSION \
    COIL_COMMIT=$COIL_COMMIT
LABEL org.opencontainers.image.version=$COIL_VERSION \
      org.opencontainers.image.revision=$COIL_COMMIT

EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "2", "--timeout", "120", "wsgi:app"]
