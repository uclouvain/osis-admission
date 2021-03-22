from django.urls import reverse

from .base import BaseAdmission


class AdmissionDoctorate(BaseAdmission):
    def get_absolute_url(self):
        return reverse('admissions:doctorate-detail', args=[str(self.uuid)])
