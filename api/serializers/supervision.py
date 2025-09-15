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

from rest_framework import serializers

from admission.ddd.admission.doctorat.preparation.commands import (
    DesignerPromoteurReferenceCommand,
    IdentifierMembreCACommand,
    IdentifierPromoteurCommand,
    ModifierMembreSupervisionExterneCommand,
    RenvoyerInvitationSignatureCommand,
    SupprimerMembreCACommand,
    SupprimerPromoteurCommand,
)
from admission.ddd.admission.doctorat.preparation.dtos import (
    GroupeDeSupervisionDTO,
    PropositionDTO,
)
from admission.models.enums.actor_type import ActorType
from base.models.person import Person
from base.utils.serializers import DTOSerializer

from . import DoctoratDTOSerializer
from .mixins import IncludedFieldsMixin

__all__ = [
    'SupervisionDTOSerializer',
    'ExternalSupervisionDTOSerializer',
    'SupervisionActorReferenceSerializer',
    'IdentifierPromoteurCommandSerializer',
    'IdentifierMembreCACommandSerializer',
    'IdentifierSupervisionActorSerializer',
    'DesignerPromoteurReferenceCommandSerializer',
    'SupprimerPromoteurCommandSerializer',
    'SupprimerMembreCACommandSerializer',
    'ModifierMembreSupervisionExterneSerializer',
    'RenvoyerInvitationSignatureSerializer',
    'PersonSerializer',
    'TutorSerializer',
]

from .project import DoctoratePropositionStatusMixin


class SupervisionDTOSerializer(DTOSerializer):
    cotutelle = None

    class Meta:
        source = GroupeDeSupervisionDTO


class ExternalDoctoratePropositionDTOSerializer(IncludedFieldsMixin, DoctoratePropositionStatusMixin, DTOSerializer):
    links = None
    erreurs = None
    reponses_questions_specifiques = None
    elements_confirmation = None
    documents_demandes = None
    doctorat = DoctoratDTOSerializer()

    class Meta:
        source = PropositionDTO
        fields = [
            'uuid',
            'type_admission',
            'reference',
            'doctorat',
            'matricule_candidat',
            'code_secteur_formation',
            'commission_proximite',
            'institut_these',
            'institution',
            'domaine_these',
            'fiche_archive_signatures_envoyees',
            'statut',
        ]


class ExternalSupervisionDTOSerializer(serializers.Serializer):
    proposition = ExternalDoctoratePropositionDTOSerializer()
    supervision = SupervisionDTOSerializer()


class SupervisionActorReferenceSerializer(serializers.Serializer):
    actor_type = serializers.ChoiceField(
        choices=ActorType.choices(),
    )
    uuid_membre = serializers.CharField()


class IdentifierPromoteurCommandSerializer(DTOSerializer):
    class Meta:
        source = IdentifierPromoteurCommand
        extra_kwargs = {
            'prenom': {'max_length': 50},
            'nom': {'max_length': 50},
            'email': {'max_length': 255},
            'institution': {'max_length': 255},
            'ville': {'max_length': 255},
        }


class IdentifierMembreCACommandSerializer(DTOSerializer):
    matricule_auteur = None

    class Meta:
        source = IdentifierMembreCACommand
        extra_kwargs = {
            'prenom': {'max_length': 50},
            'nom': {'max_length': 50},
            'email': {'max_length': 255},
            'institution': {'max_length': 255},
            'ville': {'max_length': 255},
        }


class IdentifierSupervisionActorSerializer(IdentifierMembreCACommandSerializer):
    uuid_proposition = None
    actor_type = serializers.ChoiceField(
        choices=ActorType.choices(),
    )


class DesignerPromoteurReferenceCommandSerializer(DTOSerializer):
    matricule_auteur = None

    class Meta:
        source = DesignerPromoteurReferenceCommand


class SupprimerPromoteurCommandSerializer(DTOSerializer):
    class Meta:
        source = SupprimerPromoteurCommand


class SupprimerMembreCACommandSerializer(DTOSerializer):
    class Meta:
        source = SupprimerMembreCACommand


class ModifierMembreSupervisionExterneSerializer(DTOSerializer):
    matricule_auteur = None

    class Meta:
        source = ModifierMembreSupervisionExterneCommand


class RenvoyerInvitationSignatureSerializer(DTOSerializer):
    uuid_proposition = None

    class Meta:
        source = RenvoyerInvitationSignatureCommand


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = (
            'first_name',
            'last_name',
            'global_id',
        )


class TutorSerializer(PersonSerializer):
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    global_id = serializers.ReadOnlyField()
