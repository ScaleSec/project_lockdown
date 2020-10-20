FROM python:3-alpine

# Update and install deps
RUN apk -U upgrade && apk add --update --no-cache bash build-base libffi-dev && \
  rm /var/cache/apk/*

ENV WORKDIR="/app"
ENV VENV_DIR="${WORKDIR}/venv/bin/activate"

# run as app user
RUN adduser --disabled-password --no-create-home app app && mkdir -p ${WORKDIR}/src /workspace && chown -R app:app ${WORKDIR}
USER app

WORKDIR ${WORKDIR}

# Copy src
COPY --chown=app:app src ${WORKDIR}/src

# Copy rest of scripts
COPY --chown=app:app docker/scripts/* /usr/local/bin/

# Copy tests
COPY --chown=app:app tests ${WORKDIR}/tests

ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ] 
CMD [ "test" ]