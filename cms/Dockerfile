FROM taccwma/core-cms:v4.41.0-rc1

WORKDIR /code

RUN pip install --no-cache-dir beautifulsoup4 requests

COPY /src/apps /code/apps
COPY /src/taccsite_custom /code/taccsite_custom
COPY /src/taccsite_cms /code/taccsite_cms
