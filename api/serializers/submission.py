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
from rest_framework import serializers

from admission.ddd.admission.formation_generale.commands import (
    SpecifierRaisonPlusieursDemandesMemeCycleMemeAnneeCommand,
)
from admission.ddd.admission.shared_kernel.domain.service.i_calendrier_inscription import (
    ICalendrierInscription,
)
from admission.ddd.admission.shared_kernel.domain.service.i_elements_confirmation import (
    ElementConfirmation,
)
from base.utils.serializers import DTOSerializer

__all__ = [
    'PropositionErrorsSerializer',
    'SubmitPropositionSerializer',
    'SpecifierRaisonPlusieursDemandesMemeCycleMemeAnneeCommandSerializer',
    'SubmitGeneralPropositionSerializer',
]


class PropositionErrorSerializer(serializers.Serializer):
    status_code = serializers.CharField()
    detail = serializers.CharField()


class ElementConfirmationSerializer(DTOSerializer):
    class Meta:
        source = ElementConfirmation


class PropositionErrorsSerializer(serializers.Serializer):
    errors = PropositionErrorSerializer(many=True)
    pool_start_date = serializers.DateField(allow_null=True, required=False)
    pool_end_date = serializers.DateField(allow_null=True, required=False)
    access_conditions_url = serializers.CharField(allow_null=True, required=False)
    elements_confirmation = ElementConfirmationSerializer(many=True, allow_null=True, required=False)
    display_several_applications_same_cycle_same_year_questions = serializers.BooleanField(
        allow_null=True,
        required=False,
    )


class SubmitPropositionSerializer(serializers.Serializer):
    annee = serializers.IntegerField()
    pool = serializers.ChoiceField(choices=[calendar.event_reference for calendar in ICalendrierInscription.all_pools])
    elements_confirmation = serializers.JSONField()


class SubmitGeneralPropositionSerializer(SubmitPropositionSerializer):
    raison_plusieurs_demandes_meme_cycle_meme_annee = serializers.CharField(allow_blank=True)
    justification_textuelle_plusieurs_demandes_meme_cycle_meme_annee = serializers.CharField(allow_blank=True)


class SpecifierRaisonPlusieursDemandesMemeCycleMemeAnneeCommandSerializer(DTOSerializer):
    """
    Serializer containing the answers to the questions asked when the candidate has several applications for the same
    cycle for the same year.
    """

    uuid_proposition = None

    class Meta:
        source = SpecifierRaisonPlusieursDemandesMemeCycleMemeAnneeCommand
