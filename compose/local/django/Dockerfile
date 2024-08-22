FROM alpine:3.16

ENV PYTHONUNBUFFERED 1

RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

RUN apk --no-cache add bash mc \
            util-linux \
            ttf-droid-nonlatin \
            ttf-droid \
            ttf-dejavu \
            ttf-freefont \
            ttf-liberation \
        && rm -rf /var/cache/apk/*
        

RUN apk update \
  # psycopg2 dependencies
  && apk add --virtual build-deps gcc musl-dev \
  # Pillow dependencies
  && apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
  # CFFI dependencies
  && apk add libffi-dev py-cffi \
  && apk add cargo \
  # Translations dependencies
  && apk add gettext \
  && apk add g++ gcc libxslt-dev
  # https://docs.djangoproject.com/en/dev/ref/django-admin/#dbshell

# Requirements are installed here to ensure they will be cached.
RUN apk add python3-dev
RUN apk add postgresql-client

COPY ./requirements /requirements
RUN pip install -r /requirements/local.txt

COPY ./compose/production/django/wait_for_postgres.py /wait_for_postgres.py
# RUN chmod +x /wait_for_postgres.py

COPY ./compose/local/django/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start

COPY ./compose/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

WORKDIR /app

# ENTRYPOINT ["/start"]
