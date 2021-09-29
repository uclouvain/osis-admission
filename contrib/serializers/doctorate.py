# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from rest_framework import serializers

from admission.contrib.models import AdmissionType, DoctorateAdmission
from base.utils.serializers import DTOSerializer
from ddd.logic.admission.preparation.projet_doctoral.commands import (
    CompleterPropositionCommand,
    InitierPropositionCommand,
)
from ddd.logic.admission.preparation.projet_doctoral.domain.model._detail_projet import ChoixLangueRedactionThese
from ddd.logic.admission.preparation.projet_doctoral.domain.model._experience_precedente_recherche import \
    ChoixDoctoratDejaRealise
from ddd.logic.admission.preparation.projet_doctoral.domain.model._enums import ChoixBureauCDE
from ddd.logic.admission.preparation.projet_doctoral.dtos import DoctoratDTO, PropositionDTO, PropositionSearchDTO

__all__ = [
    "PropositionIdentityDTOSerializer",
    "PropositionSearchDTOSerializer",
    "InitierPropositionCommandSerializer",
    "CompleterPropositionCommandSerializer",
    "DoctorateAdmissionReadSerializer",
    "DoctoratDTOSerializer",
    "SectorDTOSerializer",
    "PropositionDTOSerializer",
]


class DoctorateAdmissionReadSerializer(serializers.ModelSerializer):
    url = serializers.ReadOnlyField(source="get_absolute_url")
    type = serializers.ReadOnlyField(source="get_type_display")
    candidate = serializers.StringRelatedField()

    class Meta:
        model = DoctorateAdmission
        fields = [
            "uuid",
            "url",
            "type",
            "candidate",
            "comment",
            "created",
            "modified",
        ]


class PropositionIdentityDTOSerializer(serializers.Serializer):
    uuid = serializers.ReadOnlyField()


class PropositionSearchDTOSerializer(DTOSerializer):
    class Meta:
        source = PropositionSearchDTO


class PropositionDTOSerializer(DTOSerializer):
    class Meta:
        source = PropositionDTO


class InitierPropositionCommandSerializer(DTOSerializer):
    class Meta:
        source = InitierPropositionCommand

    type_admission = serializers.ChoiceField(choices=AdmissionType.choices())
    bureau_CDE = serializers.ChoiceField(
        choices=ChoixBureauCDE.choices(),
        allow_null=True,
        default=None,
    )
    documents_projet = serializers.ListField(child=serializers.CharField())
    graphe_gantt = serializers.ListField(child=serializers.CharField())
    proposition_programme_doctoral = serializers.ListField(child=serializers.CharField())
    projet_formation_complementaire = serializers.ListField(child=serializers.CharField())
    doctorat_deja_realise = serializers.ChoiceField(
        choices=ChoixDoctoratDejaRealise.choices(),
        default=ChoixDoctoratDejaRealise.NO.name,
    )
    langue_redaction_these = serializers.ChoiceField(
        choices=ChoixLangueRedactionThese.choices(),
        default=ChoixLangueRedactionThese.UNDECIDED.name,
    )


class CompleterPropositionCommandSerializer(DTOSerializer):
    class Meta:
        source = CompleterPropositionCommand

    type_admission = serializers.ChoiceField(choices=AdmissionType.choices())
    bureau_CDE = serializers.ChoiceField(
        choices=ChoixBureauCDE.choices(),
        allow_null=True,
        default=None,
    )
    documents_projet = serializers.ListField(child=serializers.CharField())
    graphe_gantt = serializers.ListField(child=serializers.CharField())
    proposition_programme_doctoral = serializers.ListField(child=serializers.CharField())
    projet_formation_complementaire = serializers.ListField(child=serializers.CharField())
    doctorat_deja_realise = serializers.ChoiceField(
        choices=ChoixDoctoratDejaRealise.choices(),
        default=ChoixDoctoratDejaRealise.NO.name,
    )
    langue_redaction_these = serializers.ChoiceField(
        choices=ChoixLangueRedactionThese.choices(),
        default=ChoixLangueRedactionThese.UNDECIDED.name,
    )


class SectorDTOSerializer(serializers.Serializer):
    sigle = serializers.ReadOnlyField()
    intitule_fr = serializers.ReadOnlyField()
    intitule_en = serializers.ReadOnlyField()


class DoctoratDTOSerializer(DTOSerializer):
    class Meta:
        source = DoctoratDTO
