# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from functools import partial

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from admission.api.permissions import IsListingOrHasNotAlreadyCreatedPermission, IsSelfPersonTabOrTabPermission
from admission.api.serializers import (
    CandidateReEnrolmentEligibilitySerializer,
    CandidateReEnrolmentPeriodDTOSerializer,
    CandidateUCLEnrolmentDTOSerializer,
)
from admission.api.serializers.candidate_ucl_enrolments import CandidateEnrolmentInformationSerializer
from admission.api.views.mixins import (
    ContinuingEducationPersonRelatedMixin,
    GeneralEducationPersonRelatedMixin,
    PersonRelatedMixin,
)
from admission.ddd.admission.shared_kernel.commands import (
    CandidatEstEligibleALaReinscriptionQuery,
    CandidatEstInscritRecemmentUCLQuery,
    RecupererInscriptionsCandidatQuery,
    RecupererPeriodeReinscriptionQuery,
)
from infrastructure.messages_bus import message_bus_instance
from osis_role.contrib.views import APIPermissionRequiredMixin

__all__ = [
    'CandidateUCLEnrolmentsView',
    'CandidateReEnrolmentPeriodView',
    'CandidateReEnrolmentEligibilityView',
    'CandidateEnrolmentInformationView',
    'GeneralCandidateEnrolmentInformationView',
    'ContinuingCandidateEnrolmentInformationView',
]


class CandidateUCLEnrolmentsView(APIPermissionRequiredMixin, ListAPIView):
    name = "candidate_ucl_enrolments"
    pagination_class = None
    filter_backends = []
    permission_classes = [IsListingOrHasNotAlreadyCreatedPermission]
    serializer_class = CandidateUCLEnrolmentDTOSerializer

    def list(self, request, **kwargs):
        """List the ucl enrolments of the logged in user"""
        candidate_ucl_enrolments = message_bus_instance.invoke(
            RecupererInscriptionsCandidatQuery(matricule_candidat=request.user.person.global_id)
        )

        serializer = CandidateUCLEnrolmentDTOSerializer(
            instance=candidate_ucl_enrolments,
            many=True,
        )

        return Response(serializer.data)


class CandidateReEnrolmentPeriodView(APIPermissionRequiredMixin, RetrieveAPIView):
    name = "candidate_re_enrolment_period"
    permission_classes = [IsListingOrHasNotAlreadyCreatedPermission]
    serializer_class = CandidateReEnrolmentPeriodDTOSerializer

    def get_object(self):
        return message_bus_instance.invoke(RecupererPeriodeReinscriptionQuery())


class CandidateReEnrolmentEligibilityView(APIPermissionRequiredMixin, RetrieveAPIView):
    name = "candidate_re_enrolment_eligibility"
    permission_classes = [IsListingOrHasNotAlreadyCreatedPermission]
    serializer_class = CandidateReEnrolmentEligibilitySerializer

    def get_object(self):
        return message_bus_instance.invoke(
            CandidatEstEligibleALaReinscriptionQuery(
                matricule_candidat=self.request.user.person.global_id,
            )
        )


class CandidateEnrolmentInformationView(PersonRelatedMixin, APIPermissionRequiredMixin, RetrieveAPIView):
    name = "candidate_enrolment_information"
    permission_classes = [
        partial(IsSelfPersonTabOrTabPermission, permission_suffix='candidate_enrolment_information'),
    ]
    serializer_class = CandidateEnrolmentInformationSerializer

    def get_object(self):
        return {
            'est_inscrit_recemment': message_bus_instance.invoke(
                CandidatEstInscritRecemmentUCLQuery(
                    matricule_candidat=self.candidate.global_id,
                )
            )
        }


class GeneralCandidateEnrolmentInformationView(GeneralEducationPersonRelatedMixin, CandidateEnrolmentInformationView):
    name = 'general_candidate_enrolment_information'
    permission_mapping = {
        'GET': 'admission.view_generaleducationadmission_candidate_enrolment_information',
    }

    def get_object(self):
        return CandidateEnrolmentInformationView.get_object(self)


class ContinuingCandidateEnrolmentInformationView(
    ContinuingEducationPersonRelatedMixin,
    CandidateEnrolmentInformationView,
):
    name = 'continuing_candidate_enrolment_information'
    permission_mapping = {
        'GET': 'admission.view_continuingeducationadmission_candidate_enrolment_information',
    }

    def get_object(self):
        return CandidateEnrolmentInformationView.get_object(self)
