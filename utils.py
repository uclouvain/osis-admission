# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import json
import os
import uuid
from collections import defaultdict
from typing import Dict, Union, Iterable

import weasyprint
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.db import models
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.utils.translation import pgettext, override
from rest_framework.generics import get_object_or_404

from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.program_manager import ProgramManager as AdmissionProgramManager
from admission.auth.roles.sic_management import SicManagement
from admission.contrib.models import ContinuingEducationAdmission, DoctorateAdmission, GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AnneesCurriculumNonSpecifieesException,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from admission.ddd.admission.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
    ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED,
)
from backoffice.settings.rest_framework.exception_handler import get_error_data
from base.auth.roles.program_manager import ProgramManager
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.academic_year import AcademicYear
from base.models.person import Person
from osis_common.ddd.interface import BusinessException, QueryRequest


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
    from infrastructure.messages_bus import message_bus_instance

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


def format_academic_year(year: Union[int, str, float], short: bool = False) -> str:
    """Return the academic year related to a specific year."""
    if not year:
        return ''
    if isinstance(year, (str, float)):
        year = int(year)
    elif isinstance(year, AcademicYear):
        year = year.year
    end_year = year + 1
    if short:
        end_year = end_year % 100
    return f'{year}-{end_year}'


def get_uuid_value(value: str) -> Union[uuid.UUID, str]:
    """Return the uuid value from a string."""
    try:
        return uuid.UUID(hex=value)
    except ValueError:
        return value


def force_title(string: str):
    """
    Return a string in which all words are lowercase, except for the first letter of each one, which can written in
    upper or lower case"""
    title_string = list(string.title())

    for index, char in enumerate(title_string):
        if char.isupper() and string[index].islower():
            title_string[index] = string[index]

    return ''.join(title_string)


def get_admission_cdd_managers(education_group_id) -> models.QuerySet[Person]:
    return Person.objects.filter(
        models.Q(
            id__in=AdmissionProgramManager.objects.filter(education_group_id=education_group_id).values('person_id')
        )
        | models.Q(id__in=ProgramManager.objects.filter(education_group_id=education_group_id).values('person_id'))
    )


def get_doctoral_cdd_managers(education_group_id) -> QuerySet[Person]:
    return Person.objects.filter(
        id__in=ProgramManager.objects.filter(education_group_id=education_group_id).values('person_id')
    )


def add_messages_into_htmx_response(request, response):
    msgs = list(messages.get_messages(request))

    if msgs:
        response['HX-Trigger'] = json.dumps(
            {
                'messages': [{'message': str(msg.message), 'tags': msg.tags} for msg in msgs],
            },
        )


def add_close_modal_into_htmx_response(response):
    if 'HX-Trigger' in response:
        trigger = json.loads(response['HX-Trigger'])
        trigger['closeModal'] = ""
        response['HX-Trigger'] = json.dumps(trigger)
    else:
        response['HX-Trigger'] = json.dumps({'closeModal': ""})


def get_portal_admission_list_url() -> str:
    """Return the url of the list of the admissions in the portal."""
    return f'{settings.OSIS_PORTAL_URL}admission/'


def get_portal_admission_url(context, admission_uuid) -> str:
    """Return the url of the admission in the portal."""
    return settings.ADMISSION_FRONTEND_LINK.format(
        context=context,
        uuid=admission_uuid,
    )


def get_backoffice_admission_url(context, admission_uuid, sub_namespace='', url_suffix='') -> str:
    """Return the url of the admission in the backoffice."""
    return '{}{}{}'.format(
        settings.ADMISSION_BACKEND_LINK_PREFIX,
        resolve_url(f'admission:{context}{sub_namespace}', uuid=admission_uuid),
        url_suffix,
    )


def person_is_sic(person: Person):
    return SicManagement.belong_to(person) or CentralManager.belong_to(person)


def person_is_fac_cdd(person: Person):
    return AdmissionProgramManager.belong_to(person)


class WeasyprintStylesheets:
    @classmethod
    def get_stylesheets(cls):
        """Get the stylesheets needed to generate the pdf"""
        # Load the stylesheets once and cache them
        if not hasattr(cls, '_stylesheet'):
            setattr(
                cls,
                '_stylesheet',
                [
                    weasyprint.CSS(filename=os.path.join(settings.BASE_DIR, file_path))
                    for file_path in [
                        'base/static/css/bootstrap.min.css',
                        'admission/static/admission/admission.css',
                        'admission/static/admission/base_pdf.css',
                    ]
                ],
            )
        return getattr(cls, '_stylesheet')


def get_salutation_prefix(person: Person) -> str:
    with override(language=person.language):
        return {
            ChoixGenre.H.name: pgettext('male gender', 'Dear'),
            ChoixGenre.F.name: pgettext('female gender', 'Dear'),
            ChoixGenre.X.name: pgettext('other gender', 'Dear'),
        }.get(person.gender or ChoixGenre.X.name)


def access_title_country(selectable_access_titles: Iterable[TitreAccesSelectionnableDTO]) -> str:
    """Return the iso code of the country of the latest access title having a specify country."""
    country = ''
    last_experience_year = 0
    for title in selectable_access_titles:
        if title.selectionne and title.pays_iso_code and title.annee > last_experience_year:
            country = title.pays_iso_code
            last_experience_year = title.annee
    return country
