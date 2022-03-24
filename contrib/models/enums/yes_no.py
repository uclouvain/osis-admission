from base.models.utils.utils import ChoiceEnum

from django.utils.translation import gettext_lazy as _


class YesNo(ChoiceEnum):
    YES = _("Yes")
    NO = _("No")
