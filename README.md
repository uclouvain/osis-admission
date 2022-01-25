# osis-admission

## Automatic schema generation command

```console
./manage.py generateschema --urlconf=admission.api.url_v1 --generator_class admission.api.schema.AdmissionSchemaGenerator --file admission/schema.yml
openapi-generator-cli generate -i admission/schema.yml -g python -o ../osis-portal/osis-admission-sdk --additional-properties packageName=osis_admission_sdk --additional-properties projectName=osis_admission_sdk
```
