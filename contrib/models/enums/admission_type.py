from base.models.utils.utils import ChoiceEnum

from django.utils.translation import gettext_lazy as _


class AdmissionType(ChoiceEnum):
    ADMISSION = _("Admission")
    PRE_ADMISSION = _("Pre-Admission")
