from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .base import BaseAdmission


class AdmissionDoctorate(BaseAdmission):
    class Meta:
        verbose_name = _("Doctorate admission")
        ordering = ('-created',)

    def get_absolute_url(self):
        return reverse("admissions:doctorate-detail", args=[self.pk])
