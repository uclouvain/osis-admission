# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from contextlib import suppress
from typing import Union

from django.conf import settings
from django.utils import timezone
from django.utils.translation import get_language
from rest_framework import mixins, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.settings import api_settings

from admission.api import serializers
from admission.api.schema import ResponseSpecificSchema
from admission.api.serializers import PropositionErrorsSerializer
from admission.contrib.models import (
    GeneralEducationAdmission,
    ContinuingEducationAdmission,
    DoctorateAdmission,
)
from admission.ddd.admission.doctorat.preparation.commands import (
    RecupererElementsConfirmationQuery as RecupererElementsConfirmationDoctoralQuery,
    SoumettrePropositionCommand as SoumettrePropositionDoctoratCommand,
    VerifierProjetQuery,
)
from admission.ddd.admission.doctorat.validation.commands import ApprouverDemandeCddCommand
from admission.ddd.admission.domain.validator.exceptions import (
    ConditionsAccessNonRempliesException,
    PoolNonResidentContingenteNonOuvertException,
)
from admission.ddd.admission.formation_continue.commands import (
    RecupererElementsConfirmationQuery as RecupererElementsConfirmationContinueQuery,
    SoumettrePropositionCommand as SoumettrePropositionContinueCommand,
)
from admission.ddd.admission.formation_generale.commands import (
    RecupererElementsConfirmationQuery as RecupererElementsConfirmationGeneralQuery,
    SoumettrePropositionCommand as SoumettrePropositionGeneraleCommand,
)
from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.utils import (
    gather_business_exceptions,
    get_cached_admission_perm_obj,
    get_cached_continuing_education_admission_perm_obj,
    get_cached_general_education_admission_perm_obj,
)
from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from ddd.logic.formation_catalogue.commands import GetSigleFormationParenteQuery
from infrastructure.messages_bus import message_bus_instance
from osis_profile.models import EducationalExperience, ProfessionalExperience
from osis_role.contrib.views import APIPermissionRequiredMixin
from program_management.ddd.domain.exception import ProgramTreeNotFoundException

__all__ = [
    "VerifyDoctoralProjectView",
    "SubmitDoctoralPropositionView",
    "SubmitGeneralEducationPropositionView",
    "SubmitContinuingEducationPropositionView",
    "get_access_conditions_url",
]


def valuate_experiences(instance: Union[GeneralEducationAdmission, ContinuingEducationAdmission, DoctorateAdmission]):
    # Valuate the secondary studies of the candidate if no admission already valuated them
    if isinstance(
        instance,
        (GeneralEducationAdmission, ContinuingEducationAdmission),
    ) and not ProfilCandidatTranslator.etudes_secondaires_valorisees(instance.candidate.global_id):
        instance.valuated_secondary_studies_person_id = instance.candidate_id
        instance.save(update_fields=['valuated_secondary_studies_person_id'])

    # Valuate curriculum experiences
    instance.educational_valuated_experiences.add(
        *EducationalExperience.objects.filter(person_id=instance.candidate_id)
    )

    # Valuate curriculum experiences
    instance.professional_valuated_experiences.add(
        *ProfessionalExperience.objects.filter(person_id=instance.candidate_id)
    )


class VerifySchema(ResponseSpecificSchema):
    response_description = "Verification errors"


class VerifyProjectSchema(VerifySchema):
    operation_id_base = '_verify_project'
    response_description = "Project verification errors"

    def get_responses(self, path, method):
        return (
            {
                status.HTTP_200_OK: {
                    "description": self.response_description,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "status_code": {
                                            "type": "string",
                                        },
                                        "detail": {
                                            "type": "string",
                                        },
                                    },
                                },
                            }
                        }
                    },
                }
            }
            if method == 'GET'
            else super(VerifySchema, self).get_responses(path, method)
        )


class VerifyDoctoralProjectView(APIPermissionRequiredMixin, mixins.RetrieveModelMixin, GenericAPIView):
    name = "verify-project"
    schema = VerifyProjectSchema()
    permission_mapping = {
        'GET': 'admission.change_admission_project',
    }
    pagination_class = None
    filter_backends = []

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the project to be OK with all validators."""
        data = gather_business_exceptions(VerifierProjetQuery(uuid_proposition=str(kwargs["uuid"])))
        return Response(data.get(api_settings.NON_FIELD_ERRORS_KEY, []), status=status.HTTP_200_OK)


class SubmitDoctoralPropositionSchema(VerifySchema):
    response_description = "Proposition verification errors"

    serializer_mapping = {
        'GET': serializers.PropositionErrorsSerializer,
        'POST': (serializers.SubmitPropositionSerializer, serializers.PropositionIdentityDTOSerializer),
    }

    def get_operation_id(self, path, method):
        if method == 'GET':
            return 'verify_proposition'
        elif method == 'POST':
            return 'submit_proposition'
        return super().get_operation_id(path, method)


def get_access_conditions_url(training_type, training_acronym, partial_training_acronym):
    if training_type == TrainingType.PHD.name:
        return (
            "https://uclouvain.be/en/study/inscriptions/doctorate-and-doctoral-training.html"
            if get_language() == settings.LANGUAGE_CODE_EN
            else "https://uclouvain.be/fr/etudier/inscriptions/conditions-doctorats.html"
        )
    else:
        # Get the last year being published
        today = timezone.now().today()
        year = (
            AcademicCalendar.objects.filter(
                reference=AcademicCalendarTypes.ADMISSION_ACCESS_CONDITIONS_URL.name,
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

        return f"https://uclouvain.be/prog-{year}-{sigle}-cond_adm"


class SubmitPropositionMixin:
    pagination_class = None
    filter_backends = []

    def add_access_conditions_url(self, data):
        error_codes = [e['status_code'] for e in data['errors']]
        if ConditionsAccessNonRempliesException.status_code in error_codes:
            admission = self.get_permission_object()
            data['access_conditions_url'] = get_access_conditions_url(
                training_type=admission.training.education_group_type.name,
                training_acronym=admission.training.acronym,
                partial_training_acronym=admission.training.partial_acronym,
            )


class SubmitDoctoralPropositionView(
    SubmitPropositionMixin,
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    GenericAPIView,
):
    name = "submit-doctoral-proposition"
    schema = SubmitDoctoralPropositionSchema()
    permission_mapping = {
        'GET': 'admission.submit_doctorateadmission',
        'POST': 'admission.submit_doctorateadmission',
    }

    def get_permission_object(self):
        return get_cached_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the proposition to be OK with all validators."""
        admission = self.get_permission_object()
        admission.update_detailed_status(request.user.person)

        data = {'errors': admission.detailed_status}
        self.add_access_conditions_url(data)
        if not data['errors']:
            cmd = RecupererElementsConfirmationDoctoralQuery(self.kwargs['uuid'])
            data['elements_confirmation'] = message_bus_instance.invoke(cmd)
        return Response(PropositionErrorsSerializer(data).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Submit the proposition."""
        # Trigger the submit command
        serializer = serializers.SubmitPropositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cmd = SoumettrePropositionDoctoratCommand(**serializer.data, uuid_proposition=str(kwargs['uuid']))
        proposition_id = message_bus_instance.invoke(cmd)
        valuate_experiences(self.get_permission_object())
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        # TODO To remove when the admission approval by CDD and SIC will be created
        message_bus_instance.invoke(ApprouverDemandeCddCommand(uuid=str(kwargs["uuid"])))
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitGeneralEducationPropositionSchema(VerifySchema):
    response_description = "Proposition verification errors"
    serializer_mapping = {
        'GET': serializers.PropositionErrorsSerializer,
        'POST': (serializers.SubmitPropositionSerializer, serializers.PropositionIdentityDTOSerializer),
    }

    def get_operation_id(self, path, method):
        return 'verify_general_education_proposition' if method == 'GET' else 'submit_general_education_proposition'


class SubmitGeneralEducationPropositionView(
    SubmitPropositionMixin,
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    GenericAPIView,
):
    name = "submit-general-proposition"
    schema = SubmitGeneralEducationPropositionSchema()
    permission_mapping = {
        'GET': 'admission.submit_generaleducationadmission',
        'POST': 'admission.submit_generaleducationadmission',
    }

    def get_permission_object(self):
        return get_cached_general_education_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the proposition to be OK with all validators."""
        admission = self.get_permission_object()
        admission.update_detailed_status(request.user.person)

        data = {'errors': admission.detailed_status}
        error_codes = [e['status_code'] for e in data['errors']]
        if PoolNonResidentContingenteNonOuvertException.status_code in error_codes:
            # Pots contigenté non-ouvert
            today = timezone.now().today()
            period = (
                AcademicCalendar.objects.filter(
                    reference=AcademicCalendarTypes.ADMISSION_POOL_NON_RESIDENT_QUOTA.name,
                    start_date__gte=today,
                    end_date__gte=today,
                )
                .order_by('start_date')
                .first()
            )
            data['pool_start_date'] = period.start_date
            data['pool_end_date'] = period.end_date

        self.add_access_conditions_url(data)
        if not data['errors']:
            cmd = RecupererElementsConfirmationGeneralQuery(self.kwargs['uuid'])
            data['elements_confirmation'] = message_bus_instance.invoke(cmd)

        return Response(PropositionErrorsSerializer(data).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Submit the proposition."""
        serializer = serializers.SubmitPropositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cmd = SoumettrePropositionGeneraleCommand(**serializer.data, uuid_proposition=str(kwargs['uuid']))
        proposition_id = message_bus_instance.invoke(cmd)
        valuate_experiences(self.get_permission_object())
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmitContinuingEducationPropositionSchema(VerifySchema):
    response_description = "Proposition verification errors"
    serializer_mapping = {
        'GET': serializers.PropositionErrorsSerializer,
        'POST': (serializers.SubmitPropositionSerializer, serializers.PropositionIdentityDTOSerializer),
    }

    def get_operation_id(self, path, method):
        return (
            'verify_continuing_education_proposition' if method == 'GET' else 'submit_continuing_education_proposition'
        )


class SubmitContinuingEducationPropositionView(
    SubmitPropositionMixin,
    APIPermissionRequiredMixin,
    mixins.RetrieveModelMixin,
    GenericAPIView,
):
    name = "submit-continuing-proposition"
    schema = SubmitContinuingEducationPropositionSchema()
    permission_mapping = {
        'GET': 'admission.submit_continuingeducationadmission',
        'POST': 'admission.submit_continuingeducationadmission',
    }

    def get_permission_object(self):
        return get_cached_continuing_education_admission_perm_obj(self.kwargs['uuid'])

    def get(self, request, *args, **kwargs):
        """Check the proposition to be OK with all validators."""
        admission = self.get_permission_object()
        admission.update_detailed_status(request.user.person)

        data = {'errors': admission.detailed_status}
        self.add_access_conditions_url(data)
        if not data['errors']:
            cmd = RecupererElementsConfirmationContinueQuery(self.kwargs['uuid'])
            data['elements_confirmation'] = message_bus_instance.invoke(cmd)
        return Response(PropositionErrorsSerializer(data).data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """Submit the proposition."""
        serializer = serializers.SubmitPropositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cmd = SoumettrePropositionContinueCommand(**serializer.data, uuid_proposition=str(kwargs['uuid']))
        proposition_id = message_bus_instance.invoke(cmd)
        valuate_experiences(self.get_permission_object())
        serializer = serializers.PropositionIdentityDTOSerializer(instance=proposition_id)
        return Response(serializer.data, status=status.HTTP_200_OK)
