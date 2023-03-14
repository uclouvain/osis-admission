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
import uuid
from collections import defaultdict
from typing import Dict, Union

from django.core.cache import cache
from rest_framework.generics import get_object_or_404

from admission.contrib.models import DoctorateAdmission, GeneralEducationAdmission, ContinuingEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AnneesCurriculumNonSpecifieesException,
)
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.mail_templates import (
    ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED,
    ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
)
from backoffice.settings.rest_framework.exception_handler import get_error_data
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from infrastructure.messages_bus import message_bus_instance
from osis_common.ddd.interface import QueryRequest, BusinessException


def get_cached_admission_perm_obj(admission_uuid):
    qs = DoctorateAdmission.objects.select_related(
        'supervision_group',
        'candidate',
        'training__academic_year',
    )
    return cache.get_or_set(
        'admission_permission_{}'.format(admission_uuid),
        lambda: get_object_or_404(qs, uuid=admission_uuid),
    )


def get_cached_general_education_admission_perm_obj(admission_uuid):
    qs = GeneralEducationAdmission.objects.select_related('candidate', 'training__academic_year')
    return cache.get_or_set(
        'admission_permission_{}'.format(admission_uuid),
        lambda: get_object_or_404(qs, uuid=admission_uuid),
    )


def get_cached_continuing_education_admission_perm_obj(admission_uuid):
    qs = ContinuingEducationAdmission.objects.select_related('candidate', 'training__academic_year')
    return cache.get_or_set(
        'admission_permission_{}'.format(admission_uuid),
        lambda: get_object_or_404(qs, uuid=admission_uuid),
    )


def sort_business_exceptions(exception: BusinessException):
    if isinstance(exception, AnneesCurriculumNonSpecifieesException):
        return exception.status_code, exception.periode
    return getattr(exception, 'status_code', ''), None


def gather_business_exceptions(command: QueryRequest) -> Dict[str, list]:
    data = defaultdict(list)
    try:
        # Trigger the verification command
        message_bus_instance.invoke(command)
    except MultipleBusinessExceptions as exc:
        # Gather all errors for output
        sorted_exceptions = sorted(exc.exceptions, key=sort_business_exceptions)

        for exception in sorted_exceptions:
            data = get_error_data(data, exception, {})

    return data


def get_mail_templates_from_admission(admission: DoctorateAdmission):
    allowed_templates = []
    if admission.post_enrolment_status != ChoixStatutDoctorat.ADMISSION_IN_PROGRESS.name:
        allowed_templates.append(ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED)
        if admission.post_enrolment_status == ChoixStatutDoctorat.SUBMITTED_CONFIRMATION.name:
            allowed_templates.append(ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT)
    return allowed_templates


def takewhile_return_attribute_values(predicate, iterable, attribute):
    """
    Make an iterator that returns the values of a specific attribute of elements from the iterable as long as the
    predicate is true.
    """
    for x in iterable:
        if predicate(x):
            yield x[attribute]
        else:
            break


def format_academic_year(year: Union[int, str, float]):
    """Return the academic year related to a specific year."""
    if not year:
        return ''
    if isinstance(year, (str, float)):
        year = int(year)
    return f'{year}-{year + 1}'


def get_uuid_value(value: str) -> Union[uuid.UUID, str]:
    """Return the uuid value from a string."""
    try:
        return uuid.UUID(hex=value)
    except ValueError:
        return value
