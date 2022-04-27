# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from collections import defaultdict
from typing import Dict

from django.core.cache import cache
from rest_framework.generics import get_object_or_404

from admission.contrib.models import DoctorateAdmission
from admission.ddd.projet_doctoral.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.mail_templates import ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED
from backoffice.settings.rest_framework.exception_handler import get_error_data
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import QueryRequest


def get_cached_admission_perm_obj(admission_uuid):
    qs = DoctorateAdmission.objects.select_related(
        'supervision_group',
        'candidate',
        'doctorate',
    )
    return cache.get_or_set(
        'admission_permission_{}'.format(admission_uuid),
        lambda: get_object_or_404(qs, uuid=admission_uuid),
    )


def gather_business_exceptions(command: QueryRequest) -> Dict[str, list]:
    data = defaultdict(list)
    try:
        # Trigger the verification command
        message_bus_instance.invoke(command)
    except MultipleBusinessExceptions as exc:
        # Gather all errors for output
        for exception in exc.exceptions:
            data = get_error_data(data, exception, {})
    return data


def get_mail_templates_from_admission(admission: DoctorateAdmission):
    if admission.post_enrolment_status == ChoixStatutDoctorat.ADMITTED.name:
        return [ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED]
    return []
