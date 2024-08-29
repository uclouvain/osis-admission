# osis-admission

## Automatic schema generation command

```console
./manage.py generateschema --urlconf=admission.api.url_v1 --generator_class admission.api.schema.AdmissionSchemaGenerator --file admission/schema.yml
openapi-generator-cli generate -i admission/schema.yml -g python -o ../osis-portal/osis-admission-sdk --additional-properties packageName=osis_admission_sdk --additional-properties projectName=osis_admission_sdk
```

openapi-generator-cli 5.4.0

## Type checking

Install dependencies

```shell
pip install mypy "django-stubs==1.7.0"
mypy --install-types
```

From the root osis directory, create a `mypy.ini` file:

```ini
[mypy]
ignore_missing_imports = True
follow_imports = silent
plugins =
    mypy_django_plugin.main

[mypy.plugins.django-stubs]
django_settings_module = "backoffice.settings.dev"
```

Then, still from the root osis directory, run

```shell
mypy -p admission.ddd
```


