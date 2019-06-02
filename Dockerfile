# base image
FROM python:3.7.2-alpine

# install dependencies
RUN apk update && \
    apk add --no-cache linux-headers g++ && \
    apk add --virtual build-deps gcc python-dev musl-dev && \
    apk add postgresql-dev && \
    apk add netcat-openbsd

# set working directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# add and install requirements
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# add app
COPY . /usr/src/app
RUN pip install -e .

# run server
CMD ["gunicorn", "-w", "9", "-b", ":5000", "libraryapi.wsgi:app"]
