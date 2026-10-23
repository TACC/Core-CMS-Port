#!/bin/sh

# To copy default settings files only if they don't exist locally
cp -n /code/taccsite_cms/settings_from_host/* /code/taccsite_cms/settings/

# TODO: Delete after Core-CMS-Port #6
# settings_default.py is committed project config; refresh it on every start
if [ -f /code/taccsite_cms/settings_from_host/settings_default.py ]; then
  cp /code/taccsite_cms/settings_from_host/settings_default.py /code/taccsite_cms/settings/settings_default.py
fi

# To run docker "command"
exec "$@"
