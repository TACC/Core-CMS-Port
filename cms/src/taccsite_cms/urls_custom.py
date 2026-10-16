from django.urls import include, path, re_path

custom_urls = [
    path('example_app/', include('apps.example_app.urls', namespace='example_app')),
    re_path(r'^taggit_autosuggest/', include('taggit_autosuggest.urls')),
]
