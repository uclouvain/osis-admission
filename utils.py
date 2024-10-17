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
import itertools
import os
import uuid
from collections import defaultdict
from contextlib import suppress
from typing import Dict, Union, Iterable, List

import weasyprint
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models import QuerySet
from django.shortcuts import resolve_url
from django.utils import timezone
from django.utils.translation import pgettext, override, get_language, gettext
from django_htmx.http import trigger_client_event
from rest_framework.generics import get_object_or_404

from admission.auth.roles.central_manager import CentralManager
from admission.auth.roles.program_manager import ProgramManager as AdmissionProgramManager
from admission.auth.roles.sic_management import SicManagement
from admission.constants import CONTEXT_CONTINUING, CONTEXT_GENERAL, CONTEXT_DOCTORATE
from admission.contrib.models import ContinuingEducationAdmission, DoctorateAdmission, GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    AnneesCurriculumNonSpecifieesException,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import CurriculumAdmissionDTO
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixGenre
from admission.ddd.admission.domain.model.enums.condition_acces import TypeTitreAccesSelectionnable
from admission.ddd.admission.dtos.etudes_secondaires import EtudesSecondairesAdmissionDTO
from admission.ddd.admission.dtos.titre_acces_selectionnable import TitreAccesSelectionnableDTO
from admission.ddd.admission.formation_generale.commands import VerifierCurriculumApresSoumissionQuery
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE,
)
from admission.mail_templates import (
    ADMISSION_EMAIL_CONFIRMATION_PAPER_INFO_STUDENT,
    ADMISSION_EMAIL_GENERIC_ONCE_ADMITTED,
)
from backoffice.settings.rest_framework.exception_handler import get_error_data
from base.auth.roles.program_manager import ProgramManager
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.person import Person
from base.utils.utils import format_academic_year
from ddd.logic.formation_catalogue.commands import GetSigleFormationParenteQuery
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import (
    DiplomeBelgeEtudesSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
    AlternativeSecondairesDTO,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    ExperienceAcademiqueDTO,
    ExperienceNonAcademiqueDTO,
)
from ddd.logic.shared_kernel.profil.dtos.parcours_interne import ExperienceParcoursInterneDTO
from osis_common.ddd.interface import BusinessException, QueryRequest
from program_management.ddd.domain.exception import ProgramTreeNotFoundException


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


def get_missing_curriculum_periods(proposition_uuid: str):
    from infrastructure.messages_bus import message_bus_instance

    try:
        message_bus_instance.invoke(VerifierCurriculumApresSoumissionQuery(uuid_proposition=proposition_uuid))
        return []
    except MultipleBusinessExceptions as exc:
        return [e.message for e in sorted(exc.exceptions, key=lambda exception: exception.periode[0], reverse=True)]


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


def get_training_url(training_type, training_acronym, partial_training_acronym, suffix):
    # Circular import otherwise
    from infrastructure.messages_bus import message_bus_instance
    from admission.constants import CONTEXT_CONTINUING
    from admission.constants import CONTEXT_GENERAL
    from admission.constants import CONTEXT_DOCTORATE

    if training_type == TrainingType.FORMATION_PHD.name:
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
    curriculum_dto: CurriculumAdmissionDTO,
    etudes_secondaires_dto: EtudesSecondairesAdmissionDTO,
    internal_experiences: List[ExperienceParcoursInterneDTO],
) -> List[str]:
    """
    Returns the list of access titles formatted names in reverse chronological order.
    """
    access_titles_names = []

    # Sort the access titles by year and only keep the selected ones
    access_titles_list = sorted(
        (access_title for access_title in access_titles.values() if access_title.selectionne),
        key=lambda title: title.annee,
        reverse=True,
    )

    curriculum_experiences_by_uuid = {
        experience.uuid: experience
        for experience in itertools.chain(
            curriculum_dto.experiences_academiques,
            curriculum_dto.experiences_non_academiques,
            [etudes_secondaires_dto.experience],
            internal_experiences,
        )
        if experience
    }

    for access_title in access_titles_list:
        experience_name = ''
        experience = curriculum_experiences_by_uuid.get(access_title.uuid_experience)

        if access_title.type_titre == TypeTitreAccesSelectionnable.EXPERIENCE_PARCOURS_INTERNE.name:
            # Internal experience
            if isinstance(experience, ExperienceParcoursInterneDTO):
                experience_derniere_annee = experience.derniere_annee
                experience_name = '{title} ({year}) - UCL'.format(
                    title=experience_derniere_annee.intitule_formation,
                    year=format_academic_year(experience_derniere_annee.annee),
                )

        elif access_title.type_titre == TypeTitreAccesSelectionnable.ETUDES_SECONDAIRES.name:
            # Secondary studies
            if isinstance(experience, DiplomeBelgeEtudesSecondairesDTO):
                experience_name = '{title} ({year}) - {institute}'.format(
                    title=str(etudes_secondaires_dto.diplome_belge),
                    year=format_academic_year(access_title.annee),
                    institute=etudes_secondaires_dto.diplome_belge.nom_institut,
                )
            elif isinstance(experience, DiplomeEtrangerEtudesSecondairesDTO):
                experience_name = '{title} ({year}) - {country}'.format(
                    title=str(etudes_secondaires_dto.diplome_etranger),
                    year=format_academic_year(access_title.annee),
                    country=etudes_secondaires_dto.diplome_etranger.pays_nom,
                )
            elif isinstance(experience, AlternativeSecondairesDTO):
                experience_name = str(etudes_secondaires_dto.alternative_secondaires)
            elif etudes_secondaires_dto.annee_diplome_etudes_secondaires:
                experience_name = '{title} ({year})'.format(
                    title=gettext('Secondary school'),
                    year=format_academic_year(access_title.annee),
                )
        else:
            # Curriculum experiences
            if isinstance(experience, ExperienceAcademiqueDTO):
                experience_name = '{title} ({year}) - {institute}'.format(
                    title=f'{experience.nom_formation} ({experience.nom_formation_equivalente_communaute_fr})'
                    if experience.nom_formation_equivalente_communaute_fr
                    else experience.nom_formation,
                    year=format_academic_year(access_title.annee),
                    institute=experience.nom_institut,
                )
            elif isinstance(experience, ExperienceNonAcademiqueDTO):
                experience_name = '{title} ({year})'.format(
                    title=str(experience),
                    year=format_academic_year(access_title.annee),
                )

        access_titles_names.append(experience_name)

    return access_titles_names


def copy_documents(objs):
    """
    Create copies of the files of the specified objects and affect them to the specified objects.
    :param objs: The list of objects.
    """
    from osis_document.api.utils import get_several_remote_metadata, get_remote_tokens, documents_remote_duplicate
    from osis_document.contrib import FileField
    from osis_document.utils import generate_filename

    all_document_uuids = []
    all_document_upload_paths = {}
    document_fields_by_obj_uuid = {}

    # Get all the document fields and the uuids of the documents to duplicate
    for obj in objs:
        document_fields_by_obj_uuid[obj.uuid] = {}

        for field in obj._meta.get_fields():
            if isinstance(field, FileField):
                document_uuids = getattr(obj, field.name)

                if document_uuids:
                    document_fields_by_obj_uuid[obj.uuid][field.name] = field
                    all_document_uuids += [document_uuid for document_uuid in document_uuids if document_uuid]

    all_tokens = get_remote_tokens(all_document_uuids)
    metadata_by_token = get_several_remote_metadata(tokens=list(all_tokens.values()))

    # Get the upload paths of the documents to duplicate
    for obj in objs:
        for field_name, field in document_fields_by_obj_uuid[obj.uuid].items():
            document_uuids = getattr(obj, field_name)

            for document_uuid in document_uuids:
                if not document_uuid:
                    continue

                document_uuid_str = str(document_uuid)
                file_name = 'file'

                if document_uuid_str in all_tokens and all_tokens[document_uuid_str] in metadata_by_token:
                    metadata = metadata_by_token[all_tokens[document_uuid_str]]
                    if metadata.get('name'):
                        file_name = metadata['name']

                all_document_upload_paths[document_uuid_str] = generate_filename(obj, file_name, field.upload_to)

    # Make a copy of the documents and return the uuids of the copied documents
    duplicates_documents_uuids = documents_remote_duplicate(
        uuids=all_document_uuids,
        with_modified_upload=True,
        upload_path_by_uuid=all_document_upload_paths,
    )

    # Update the uuids of the documents with the uuids of the copied documents
    for obj in objs:
        for field_name in document_fields_by_obj_uuid[obj.uuid]:
            setattr(
                obj,
                field_name,
                [
                    uuid.UUID(duplicates_documents_uuids[str(document_uuid)])
                    for document_uuid in getattr(obj, field_name)
                    if duplicates_documents_uuids.get(str(document_uuid))
                ],
            )


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
                if computed_permissions['profil.can_see_parcours_externe']:
                    res_context['curex_url'] = resolve_url(
                        'parcours-externe-view',
                        noma=candidate_noma,
                    )
                if computed_permissions['profil.can_edit_parcours_externe']:
                    res_context['edit_url'] = resolve_url(
                        'edit-experience-academique-view',
                        noma=candidate_noma,
                        experience_uuid=experience.annees[0].uuid,
                    )
                    res_context['edit_new_link_tab'] = True

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

        res_context['duplicate_url'] = resolve_url(
            f'{base_namespace}:update:curriculum:non_educational_duplicate',
            uuid=admission.uuid,
            experience_uuid=experience.uuid,
        )

        if experience.epc_experience:
            if candidate_noma:
                if computed_permissions['profil.can_edit_parcours_externe']:
                    res_context['edit_url'] = resolve_url(
                        'edit-experience-non-academique-view',
                        noma=candidate_noma,
                        experience_uuid=experience.uuid,
                    )
                    res_context['edit_new_link_tab'] = True

        else:
            res_context['edit_url'] = resolve_url(
                f'{base_namespace}:update:curriculum:non_educational',
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
