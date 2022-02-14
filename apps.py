from django.apps import AppConfig


class AdmissionConfig(AppConfig):
    name = "admission"

    def ready(self) -> None:
        from . import checks
