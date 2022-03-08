
FROM ubuntu:latest

# https://medium.com/@chamilad/lets-make-your-docker-image-better-than-90-of-existing-ones-8b1e5de950d
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.name="BigFixOperator"
LABEL org.label-schema.description="Run bigfixoperator on Ubuntu:latest"
LABEL org.label-schema.docker.cmd="docker run --rm bigfixoperator"

# https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
RUN apt-get update && apt-get install -y curl git python3 python3-pip && rm -rf /var/lib/apt/lists/*

RUN pip3 install pipenv

WORKDIR /tmp

# copy local repo contents over
COPY . /tmp/BigFixOperator

WORKDIR /tmp/BigFixOperator
RUN pipenv install

ENTRYPOINT ["pipenv","run","python3", "./src/BigFixOperator.py"]
CMD ["--help"]
