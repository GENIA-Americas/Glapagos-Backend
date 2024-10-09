FROM alpine:3.16

ENV PYTHONUNBUFFERED 1
ENV PORT 8000

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
RUN apk add libmagic

WORKDIR /app
COPY ./api /app

RUN pip install -r /app/requirements/production.txt

COPY ./compose/production/django/wait_for_postgres.py /wait_for_postgres.py
RUN chmod +x /wait_for_postgres.py

COPY ./compose/production/django/start /start
RUN chmod +x /start

COPY ./compose/production/django/celery/beat/start /start-celerybeat
RUN chmod +x /start-celerybeat

EXPOSE $PORT

ENTRYPOINT ["/start"]