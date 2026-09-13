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
# WEB_CONCURRENCY must match -w below. The API rate limiter counts in-process, so it
# divides the advertised limit by this to enforce the number it actually promises.
ENV WEB_CONCURRENCY=2
# A CSV import commits one row at a time (see run_import in importer.py) so a firm's own writes can
# interleave with it; at real switch-from-Clio sizes that adds up to minutes, not seconds, of wall time
# on one request. 120s killed the worker mid-commit on a 10,000-row import, which the browser saw as the
# tab going unresponsive even though the rows committed before the kill had already been saved.
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "2", "--timeout", "600", "wsgi:app"]
