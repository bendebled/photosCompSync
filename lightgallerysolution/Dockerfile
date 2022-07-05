# Download base image and install dependencies
# ------------------------------------------------------------------------------
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY ./app /app

# RUN mkdir /root/.ssh
# RUN chown root:root /root/.ssh
COPY ./ssh /root/.ssh

WORKDIR /app