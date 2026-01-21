ARG PYTHON_VERSION=3.13
ARG BUILDPLATFORM=x86_64

FROM --platform=${BUILDPLATFORM} public.ecr.aws/lambda/python:${PYTHON_VERSION} AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install required utilities
RUN dnf install -y findutils binutils && \
    dnf clean all && \
    rm -rf /var/cache/dnf

WORKDIR /tmp
COPY pyproject.toml pyproject.toml
COPY README.md README.md
RUN uv pip install --compile-bytecode . --target /asset

# Reduce package size and remove useless files
WORKDIR /asset
RUN find . -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-[0-9]*//'); cp $f $n; done;
RUN find . -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN find . -type f -a -name '*.py' -print0 | xargs -0 rm -f
RUN find . -type d -a -name 'tests' -print0 | xargs -0 rm -rf
RUN find . -type f -name '*.so*' -exec strip --strip-unneeded {} \;

FROM --platform=${BUILDPLATFORM} public.ecr.aws/lambda/python:${PYTHON_VERSION}
ENV TZ=UTC
WORKDIR ${LAMBDA_TASK_ROOT}
COPY --from=builder /asset ${LAMBDA_TASK_ROOT}
COPY lambda/handler.py ${LAMBDA_TASK_ROOT}
CMD [ "handler.handler" ]
