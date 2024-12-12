FROM mambaorg/micromamba:2.0.4

COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

WORKDIR /app

RUN mkdir /app/res
RUN chown -R $MAMBA_USER:$MAMBA_USER /app/res

COPY --chown=$MAMBA_USER:$MAMBA_USER . .

EXPOSE 5000

ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN python --version
RUN python -c "import flask; print(flask.__version__)"
RUN whoami

ENV FLASK_APP='/app/app.py'

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "flask", "run", "--host=0.0.0.0", "--port=5000"]