# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import itertools
import os
import uuid
from collections import defaultdict
from contextlib import suppress
from typing import Dict, Iterable, List, Union

import weasyprint
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models import F, QuerySet
from django.shortcuts import resolve_url
from django.utils import timezone
from django.utils.translation import get_language, gettext, override, pgettext
from django_htmx.http import trigger_client_event
from rest_framework.generics import get_object_or_404

from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.program_manager import (
    ProgramManager as AdmissionProgramManager,
)
from admission.auth.roles.sic_management import SicManagement
from admission.constants import CONTEXT_CONTINUING, CONTEXT_DOCTORATE, CONTEXT_GENERAL
from admission.ddd.admission.doctorat.preparation.commands import (
    VerifierCurriculumApresSoumissionQuery as VerifierCurriculumApresSoumissionDoctoraleQuery,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AnneesCurriculumNonSpecifieesException,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import (
    CurriculumAdmissionDTO,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from admission.ddd.admission.domain.model.enums.condition_acces import (
    TypeTitreAccesSelectionnable,
)
from admission.ddd.admission.dtos.etudes_secondaires import (
    EtudesSecondairesAdmissionDTO,
)
from admission.ddd.admission.dtos.titre_acces_selectionnable import (
    TitreAccesSelectionnableDTO,
)
from admission.ddd.admission.formation_generale.commands import (
    VerifierCurriculumApresSoumissionQuery as VerifierCurriculumApresSoumissionGeneraleQuery,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE,
)
from admission.models import (
    ContinuingEducationAdmission,
    DoctorateAdmission,
    GeneralEducationAdmission,
)
from backoffice.settings.rest_framework.exception_handler import get_error_data
from base.auth.roles.program_manager import ProgramManager
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.forms.utils import EMPTY_CHOICE
from base.models.academic_calendar import AcademicCalendar
from base.models.entity_version import EntityVersion
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.enums.establishment_type import EstablishmentTypeEnum
from base.models.person import Person
from base.utils.utils import format_academic_year
from ddd.logic.formation_catalogue.commands import GetSigleFormationParenteQuery
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import (
    AlternativeSecondairesDTO,
    DiplomeBelgeEtudesSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    ExperienceAcademiqueDTO,
    ExperienceNonAcademiqueDTO,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_interne import (
    ExperienceParcoursInterneDTO,
)
from osis_common.ddd.interface import BusinessException, QueryRequest
from program_management.ddd.domain.exception import ProgramTreeNotFoundException
from reference.models.country import Country
from reference.models.language import Language
from reference.models.scholarship import Scholarship


def get_cached_admission_perm_obj(admission_uuid):
    qs = DoctorateAdmission.objects.select_related(
        'supervision_group',
        'candidate__personmergeproposal',
        'training__academic_year',
        'training__education_group_type',
        'determined_academic_year',
    )
    return cache.get_or_set(
        'admission_permission_{}'.format(admission_uuid),
        lambda: get_object_or_404(qs, uuid=admission_uuid),
    )


def get_cached_general_education_admission_perm_obj(admission_uuid):
    qs = GeneralEducationAdmission.objects.select_related(
        'candidate__personmergeproposal',
        'training__academic_year',
        'training__education_group_type',
        'determined_academic_year',
    )
    return cache.get_or_set(
        'admission_permission_{}'.format(admission_uuid),
        lambda: get_object_or_404(qs, uuid=admission_uuid),
    )


def get_cached_continuing_education_admission_perm_obj(admission_uuid):
    qs = ContinuingEducationAdmission.objects.select_related(
        'candidate__personmergeproposal',
        'training__academic_year',
        'training__specificiufcinformations',
    )
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


def get_missing_curriculum_periods(proposition_uuid: str):
    from infrastructure.messages_bus import message_bus_instance

    try:
        message_bus_instance.invoke(VerifierCurriculumApresSoumissionGeneraleQuery(uuid_proposition=proposition_uuid))
        return []
    except MultipleBusinessExceptions as exc:
        return [
            e.message
            for e in sorted(
                [
                    period_exception
                    for period_exception in exc.exceptions
                    if isinstance(period_exception, AnneesCurriculumNonSpecifieesException)
                ],
                key=lambda exception: exception.periode[0],
                reverse=True,
            )
        ]


def get_missing_curriculum_periods_for_doctorate(proposition_uuid: str):
    from infrastructure.messages_bus import message_bus_instance

    try:
        message_bus_instance.invoke(VerifierCurriculumApresSoumissionDoctoraleQuery(uuid_proposition=proposition_uuid))
        return []
    except MultipleBusinessExceptions as exc:
        return [
            e.message
            for e in sorted(
                [
                    period_exception
                    for period_exception in exc.exceptions
                    if isinstance(period_exception, AnneesCurriculumNonSpecifieesException)
                ],
                key=lambda exception: exception.periode[0],
                reverse=True,
            )
        ]


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
        trigger_client_event(response, 'messages', [{'message': str(msg.message), 'tags': msg.tags} for msg in msgs])


def add_close_modal_into_htmx_response(response):
    trigger_client_event(response, 'closeModal')


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
        settings.BACKEND_LINK_PREFIX,
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

    @classmethod
    def get_stylesheets_bootstrap_5(cls):
        """Get the stylesheets needed to generate the pdf"""
        # Load the stylesheets once and cache them
        if not hasattr(cls, '_stylesheet_bs5'):
            setattr(
                cls,
                '_stylesheet_bs5',
                [
                    weasyprint.CSS(filename=os.path.join(settings.BASE_DIR, file_path))
                    for file_path in [
                        'base/static/css/bootstrap5/bootstrap.min.css',
                    ]
                ],
            )
        return getattr(cls, '_stylesheet_bs5')


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


def get_training_url(training_type, training_acronym, partial_training_acronym, suffix):
    # Circular import otherwise
    from admission.constants import (
        CONTEXT_CONTINUING,
        CONTEXT_DOCTORATE,
        CONTEXT_GENERAL,
    )
    from infrastructure.messages_bus import message_bus_instance

    if training_type == TrainingType.PHD.name:
        return (
            "https://uclouvain.be/en/study/inscriptions/doctorate-and-doctoral-training.html"
            if get_language() == settings.LANGUAGE_CODE_EN
            else "https://uclouvain.be/fr/etudier/inscriptions/conditions-doctorats.html"
        )
    else:
        admission_context = ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE.get(training_type)

        academic_calendar_type = {
            CONTEXT_GENERAL: AcademicCalendarTypes.ADMISSION_ACCESS_CONDITIONS_URL,
            CONTEXT_CONTINUING: AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT,
            CONTEXT_DOCTORATE: AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT,
        }.get(admission_context) or AcademicCalendarTypes.ADMISSION_ACCESS_CONDITIONS_URL

        # Get the last year being published
        today = timezone.now().today()
        year = (
            AcademicCalendar.objects.filter(
                reference=academic_calendar_type.name,
                start_date__lte=today,
            )
            .order_by('-start_date')
            .values_list('data_year__year', flat=True)
            .first()
        )

        sigle = training_acronym
        with suppress(ProgramTreeNotFoundException):  # pragma: no cover
            # Try to get the acronym from the parent, if it exists
            sigle = message_bus_instance.invoke(
                GetSigleFormationParenteQuery(
                    code_formation=partial_training_acronym,
                    annee=year,
                )
            )

        return f"https://uclouvain.be/prog-{year}-{sigle}-{suffix}"


def get_practical_information_url(training_type, training_acronym, partial_training_acronym):
    return get_training_url(training_type, training_acronym, partial_training_acronym, 'infos_pratiques')


def get_access_conditions_url(training_type, training_acronym, partial_training_acronym):
    return get_training_url(training_type, training_acronym, partial_training_acronym, 'cond_adm')


def get_access_titles_names(
    access_titles: Dict[str, TitreAccesSelectionnableDTO],
) -> List[str]:
    """
    Returns the list of access titles formatted names in reverse chronological order.
    """
    # Sort the access titles by year and only keep the selected ones
    access_titles_list = sorted(
        (access_title for access_title in access_titles.values() if access_title.selectionne),
        key=lambda title: title.annee,
        reverse=True,
    )

    return [access_title.nom for access_title in access_titles_list]


def get_experience_urls(
    user: User,
    admission: Union[DoctorateAdmission, GeneralEducationAdmission, ContinuingEducationAdmission],
    experience: Union[ExperienceAcademiqueDTO, ExperienceNonAcademiqueDTO, EtudesSecondairesAdmissionDTO],
    candidate_noma: str = '',
):
    """
    Return the details and edit urls of an experience (cv experience or secondary studies).
    :param user: The current user
    :param admission: The admission object
    :param experience: The experience dto
    :param candidate_noma: The candidate noma, if any
    :return: A dictionary containing the urls of the experience.
    """

    current_context = {
        GeneralEducationAdmission: CONTEXT_GENERAL,
        DoctorateAdmission: CONTEXT_DOCTORATE,
        ContinuingEducationAdmission: CONTEXT_CONTINUING,
    }[type(admission)]

    base_namespace = f'admission:{current_context}'

    res_context = {
        'edit_url': '',
        'delete_url': '',
        'duplicate_url': '',
        'details_url': '',
        'curex_url': '',
        'edit_new_link_tab': False,
    }

    if not getattr(user, '_computed_permissions', None):
        computed_permissions = {
            'admission.change_admission_curriculum': user.has_perm(
                perm='admission.change_admission_curriculum',
                obj=admission,
            ),
            'admission.change_admission_secondary_studies': user.has_perm(
                perm='admission.change_admission_secondary_studies',
                obj=admission,
            ),
            'admission.delete_admission_curriculum': user.has_perm(
                perm='admission.delete_admission_curriculum',
                obj=admission,
            ),
            'profil.can_edit_parcours_externe': user.has_perm(perm='profil.can_edit_parcours_externe'),
            'profil.can_see_parcours_externe': user.has_perm(perm='profil.can_see_parcours_externe'),
        }
        setattr(user, '_computed_permissions', computed_permissions)
    else:
        computed_permissions = getattr(user, '_computed_permissions')

    if isinstance(experience, ExperienceAcademiqueDTO):
        res_context['details_url'] = resolve_url(
            f'{base_namespace}:curriculum:educational',
            uuid=admission.uuid,
            experience_uuid=experience.uuid,
        )

        if not computed_permissions['admission.change_admission_curriculum']:
            return res_context

        if experience.epc_experience:
            if candidate_noma:
                if computed_permissions['profil.can_edit_parcours_externe']:
                    res_context['edit_url'] = resolve_url(
                        'edit-experience-academique-view',
                        noma=candidate_noma,
                        experience_uuid=experience.annees[0].uuid,
                    )
                    res_context['curex_url'] = res_context['edit_url']
                    res_context['edit_new_link_tab'] = True
                elif computed_permissions['profil.can_see_parcours_externe']:
                    res_context['curex_url'] = resolve_url(
                        'parcours-externe-view',
                        noma=candidate_noma,
                    )

        else:
            res_context['duplicate_url'] = resolve_url(
                f'{base_namespace}:update:curriculum:educational_duplicate',
                uuid=admission.uuid,
                experience_uuid=experience.uuid,
            )

            res_context['edit_url'] = resolve_url(
                f'{base_namespace}:update:curriculum:educational',
                uuid=admission.uuid,
                experience_uuid=experience.uuid,
            )

            if computed_permissions['admission.delete_admission_curriculum']:
                res_context['delete_url'] = resolve_url(
                    f'{base_namespace}:update:curriculum:educational_delete',
                    uuid=admission.uuid,
                    experience_uuid=experience.uuid,
                )

    elif isinstance(experience, ExperienceNonAcademiqueDTO):
        res_context['details_url'] = resolve_url(
            f'{base_namespace}:curriculum:non_educational',
            uuid=admission.uuid,
            experience_uuid=experience.uuid,
        )

        if not computed_permissions['admission.change_admission_curriculum']:
            return res_context

        if experience.epc_experience:
            if candidate_noma:
                if computed_permissions['profil.can_edit_parcours_externe']:
                    res_context['curex_url'] = resolve_url(
                        'edit-experience-non-academique-view',
                        noma=candidate_noma,
                        experience_uuid=experience.uuid,
                    )

        else:
            res_context['edit_url'] = resolve_url(
                f'{base_namespace}:update:curriculum:non_educational',
                uuid=admission.uuid,
                experience_uuid=experience.uuid,
            )

            res_context['duplicate_url'] = resolve_url(
                f'{base_namespace}:update:curriculum:non_educational_duplicate',
                uuid=admission.uuid,
                experience_uuid=experience.uuid,
            )

            if computed_permissions['admission.delete_admission_curriculum']:
                res_context['delete_url'] = resolve_url(
                    f'{base_namespace}:update:curriculum:non_educational_delete',
                    uuid=admission.uuid,
                    experience_uuid=experience.uuid,
                )

    elif isinstance(experience, EtudesSecondairesAdmissionDTO):
        res_context['details_url'] = resolve_url(
            f'{base_namespace}:education',
            uuid=admission.uuid,
        )

        if not computed_permissions['admission.change_admission_secondary_studies']:
            return res_context

        if experience.epc_experience:
            if candidate_noma:
                if computed_permissions['profil.can_edit_parcours_externe']:
                    res_context['edit_url'] = resolve_url(
                        'edit-etudes-secondaires-view',
                        noma=candidate_noma,
                    )
                    res_context['edit_new_link_tab'] = True

        else:
            res_context['edit_url'] = resolve_url(
                f'{base_namespace}:update:education',
                uuid=admission.uuid,
            )

    return res_context


def format_address(street='', street_number='', postal_code='', city='', country=''):
    """Return the concatenation of the specified street, street number, postal code, city and country."""
    address_parts = [
        f'{street} {street_number}',
        f'{postal_code} {city}',
        country,
    ]
    return ', '.join(filter(lambda part: part and len(part) > 1, address_parts))


def format_school_title(school):
    """Return the concatenation of the school name and city."""
    return '{} <span class="school-address">{}</span>'.format(
        school.name,
        format_address(
            street=school.street,
            street_number=school.street_number,
            postal_code=school.zipcode,
            city=school.city,
        ),
    )


def get_superior_institute_queryset():
    return EntityVersion.objects.filter(
        entity__organization__establishment_type__in=[
            EstablishmentTypeEnum.UNIVERSITY.name,
            EstablishmentTypeEnum.NON_UNIVERSITY_HIGHER.name,
        ],
        parent__isnull=True,
    ).annotate(
        organization_id=F('entity__organization_id'),
        organization_uuid=F('entity__organization__uuid'),
        organization_acronym=F('entity__organization__acronym'),
        organization_community=F('entity__organization__community'),
        organization_establishment_type=F('entity__organization__establishment_type'),
        name=F('entity__organization__name'),
        city=F('entityversionaddress__city'),
        street=F('entityversionaddress__street'),
        street_number=F('entityversionaddress__street_number'),
        zipcode=F('entityversionaddress__postal_code'),
    )


def get_thesis_location_initial_choices(value):
    return EMPTY_CHOICE if not value else EMPTY_CHOICE + ((value, value),)


def get_scholarship_initial_choices(uuid):
    if not uuid:
        return EMPTY_CHOICE
    try:
        scholarship = Scholarship.objects.get(uuid=uuid)
    except Scholarship.DoesNotExist:
        return EMPTY_CHOICE
    return EMPTY_CHOICE + ((uuid, scholarship.long_name or scholarship.short_name),)


def get_language_initial_choices(code):
    if not code:
        return EMPTY_CHOICE
    try:
        language = Language.objects.get(code=code)
    except Language.DoesNotExist:
        return EMPTY_CHOICE
    return EMPTY_CHOICE + (
        (language.code, language.name if get_language() == settings.LANGUAGE_CODE_FR else language.name_en),
    )


def get_country_initial_choices(iso_code):
    if not iso_code:
        return EMPTY_CHOICE
    try:
        country = Country.objects.get(iso_code=iso_code)
    except Country.DoesNotExist:
        return EMPTY_CHOICE
    return EMPTY_CHOICE + (
        (country.iso_code, country.name if get_language() == settings.LANGUAGE_CODE_FR else country.name_en),
    )
