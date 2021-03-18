from base.models.utils.utils import ChoiceEnum

from django.utils.translation import gettext_lazy as _


class AdmissionType(ChoiceEnum):
    ADMISSION = _("type_admission")
    PRE_ADMISSION = _("type_pre_admission")
