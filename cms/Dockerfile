FROM taccwma/core-cms:latest

WORKDIR /code

RUN pip install --no-cache-dir beautifulsoup4 requests google-api-python-client google-auth

COPY /src/apps /code/apps
COPY /src/taccsite_custom /code/taccsite_custom
COPY /src/taccsite_cms /code/taccsite_cms
