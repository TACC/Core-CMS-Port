FROM taccwma/core-cms:770fd9d

WORKDIR /code

# Install curl and Node.js 20.x.
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs

RUN pip install --no-cache-dir beautifulsoup4 requests

COPY /src/apps /code/apps
COPY /src/taccsite_custom /code/taccsite_custom
COPY /src/taccsite_cms /code/taccsite_cms
