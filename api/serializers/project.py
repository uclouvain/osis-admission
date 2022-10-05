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

from rest_framework import serializers

from admission.api.serializers.fields import ACTION_LINKS, ActionLinksField, RelatedInstituteField
from admission.api.serializers.mixins import IncludedFieldsMixin
from admission.contrib.models import AdmissionType, DoctorateAdmission
from admission.ddd.admission.doctorat.preparation.commands import CompleterPropositionCommand, InitierPropositionCommand
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_generale.dtos import PropositionDTO as FormationGeneralePropositionDTO
from admission.ddd.admission.formation_continue.dtos import PropositionDTO as FormationContinuePropositionDTO
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixLangueRedactionThese,
    ChoixSousDomaineSciences,
)
from admission.ddd.admission.doctorat.preparation.dtos import DoctoratDTO, PropositionDTO as DoctoratPropositionDTO
from base.utils.serializers import DTOSerializer

__all__ = [
    "PropositionIdentityDTOSerializer",
    "PropositionSearchSerializer",
    "InitierPropositionCommandSerializer",
    "CompleterPropositionCommandSerializer",
    "DoctorateAdmissionReadSerializer",
    "DoctoratDTOSerializer",
    "SectorDTOSerializer",
    "PropositionDTOSerializer",
    "DoctoratePropositionSearchDTOSerializer",
    "GeneralEducationPropositionSearchDTOSerializer",
    "ContinuingEducationPropositionSearchDTOSerializer",
    "FormationContinueDTOSerializer",
    "FormationGeneraleDTOSerializer",
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


class DoctoratePropositionSearchDTOSerializer(IncludedFieldsMixin, DTOSerializer):
    links = ActionLinksField(
        actions={
            # Profile
            # Person
            'retrieve_person': ACTION_LINKS['retrieve_person'],
            'update_person': ACTION_LINKS['update_person'],
            # Coordinates
            'retrieve_coordinates': ACTION_LINKS['retrieve_coordinates'],
            'update_coordinates': ACTION_LINKS['update_coordinates'],
            # Secondary studies
            'retrieve_secondary_studies': ACTION_LINKS['retrieve_secondary_studies'],
            'update_secondary_studies': ACTION_LINKS['update_secondary_studies'],
            # Language knowledge
            'retrieve_languages': ACTION_LINKS['retrieve_languages'],
            'update_languages': ACTION_LINKS['update_languages'],
            # Proposition
            'destroy_proposition': ACTION_LINKS['destroy_proposition'],
            'submit_proposition': ACTION_LINKS['submit_proposition'],
            # Project
            'retrieve_proposition': ACTION_LINKS['retrieve_proposition'],
            'update_proposition': ACTION_LINKS['update_proposition'],
            # Cotutelle
            'retrieve_cotutelle': ACTION_LINKS['retrieve_cotutelle'],
            'update_cotutelle': ACTION_LINKS['update_cotutelle'],
            # Supervision
            'retrieve_supervision': ACTION_LINKS['retrieve_supervision'],
            # Curriculum
            'retrieve_curriculum': ACTION_LINKS['retrieve_curriculum'],
            'update_curriculum': ACTION_LINKS['update_curriculum'],
            # Confirmation
            'retrieve_confirmation': ACTION_LINKS['retrieve_confirmation'],
            'update_confirmation': ACTION_LINKS['update_confirmation'],
            # Accounting
            'retrieve_accounting': ACTION_LINKS['retrieve_accounting'],
            'update_accounting': ACTION_LINKS['update_accounting'],
            # Training
            'retrieve_doctoral_training': ACTION_LINKS['retrieve_doctoral_training'],
            'retrieve_complementary_training': ACTION_LINKS['retrieve_complementary_training'],
            'retrieve_course_enrollment': ACTION_LINKS['retrieve_course_enrollment'],
        }
    )

    # This is to prevent schema from breaking on JSONField
    erreurs = None

    class Meta:
        source = DoctoratPropositionDTO
        fields = [
            'uuid',
            'reference',
            'type_admission',
            'doctorat',
            'matricule_candidat',
            'prenom_candidat',
            'nom_candidat',
            'code_secteur_formation',
            'intitule_secteur_formation',
            'commission_proximite',
            'creee_le',
            'statut',
            'links',
        ]


class GeneralEducationPropositionSearchDTOSerializer(IncludedFieldsMixin, DTOSerializer):
    links = ActionLinksField(actions={})

    # This is to prevent schema from breaking on JSONField
    erreurs = None

    class Meta:
        source = FormationGeneralePropositionDTO

        fields = [
            'uuid',
            'formation',
            'matricule_candidat',
            'prenom_candidat',
            'nom_candidat',
            'creee_le',
            'statut',
            'links',
        ]


class ContinuingEducationPropositionSearchDTOSerializer(IncludedFieldsMixin, DTOSerializer):
    links = ActionLinksField(actions={})

    # This is to prevent schema from breaking on JSONField
    erreurs = None

    class Meta:
        source = FormationContinuePropositionDTO
        fields = [
            'uuid',
            'formation',
            'matricule_candidat',
            'prenom_candidat',
            'nom_candidat',
            'creee_le',
            'statut',
            'links',
        ]


class PropositionSearchSerializer(serializers.Serializer):
    links = ActionLinksField(actions={'create_proposition': ACTION_LINKS['create_proposition']})

    doctorate_propositions = DoctoratePropositionSearchDTOSerializer(many=True)
    general_education_propositions = GeneralEducationPropositionSearchDTOSerializer(many=True)
    continuing_education_propositions = ContinuingEducationPropositionSearchDTOSerializer(many=True)


class PropositionDTOSerializer(IncludedFieldsMixin, DTOSerializer):
    links = ActionLinksField(
        actions={
            # Profile
            # Person
            'retrieve_person': ACTION_LINKS['retrieve_person'],
            'update_person': ACTION_LINKS['update_person'],
            # Coordinates
            'retrieve_coordinates': ACTION_LINKS['retrieve_coordinates'],
            'update_coordinates': ACTION_LINKS['update_coordinates'],
            # Secondary studies
            'retrieve_secondary_studies': ACTION_LINKS['retrieve_secondary_studies'],
            'update_secondary_studies': ACTION_LINKS['update_secondary_studies'],
            # Language knowledge
            'retrieve_languages': ACTION_LINKS['retrieve_languages'],
            'update_languages': ACTION_LINKS['update_languages'],
            # Proposition
            'destroy_proposition': ACTION_LINKS['destroy_proposition'],
            'submit_proposition': ACTION_LINKS['submit_proposition'],
            # Project
            'retrieve_proposition': ACTION_LINKS['retrieve_proposition'],
            'update_proposition': ACTION_LINKS['update_proposition'],
            # Cotutelle
            'retrieve_cotutelle': ACTION_LINKS['retrieve_cotutelle'],
            'update_cotutelle': ACTION_LINKS['update_cotutelle'],
            # Supervision
            'add_approval': ACTION_LINKS['add_approval'],
            'add_member': ACTION_LINKS['add_member'],
            'remove_member': ACTION_LINKS['remove_member'],
            'set_reference_promoter': ACTION_LINKS['set_reference_promoter'],
            'retrieve_supervision': ACTION_LINKS['retrieve_supervision'],
            'request_signatures': ACTION_LINKS['request_signatures'],
            'approve_by_pdf': ACTION_LINKS['approve_by_pdf'],
            # Curriculum
            'retrieve_curriculum': ACTION_LINKS['retrieve_curriculum'],
            'update_curriculum': ACTION_LINKS['update_curriculum'],
            # Confirmation
            'retrieve_confirmation': ACTION_LINKS['retrieve_confirmation'],
            'update_confirmation': ACTION_LINKS['update_confirmation'],
            # Accounting
            'retrieve_accounting': ACTION_LINKS['retrieve_accounting'],
            'update_accounting': ACTION_LINKS['update_accounting'],
            # Training
            'retrieve_doctoral_training': ACTION_LINKS['retrieve_doctoral_training'],
            'retrieve_complementary_training': ACTION_LINKS['retrieve_complementary_training'],
            'retrieve_course_enrollment': ACTION_LINKS['retrieve_course_enrollment'],
        }
    )
    # The schema is explicit in PropositionSchema
    erreurs = serializers.JSONField()

    class Meta:
        source = DoctoratPropositionDTO
        fields = [
            'uuid',
            'type_admission',
            'reference',
            'justification',
            'doctorat',
            'matricule_candidat',
            'code_secteur_formation',
            'commission_proximite',
            'type_financement',
            'type_contrat_travail',
            'eft',
            'bourse_recherche',
            'bourse_date_debut',
            'bourse_date_fin',
            'bourse_preuve',
            'duree_prevue',
            'temps_consacre',
            'titre_projet',
            'resume_projet',
            'documents_projet',
            'graphe_gantt',
            'proposition_programme_doctoral',
            'projet_formation_complementaire',
            'lettres_recommandation',
            'langue_redaction_these',
            'institut_these',
            'lieu_these',
            'doctorat_deja_realise',
            'institution',
            'domaine_these',
            'date_soutenance',
            'raison_non_soutenue',
            'fiche_archive_signatures_envoyees',
            'statut',
            'links',
            'erreurs',
            'comptabilite',
        ]


class InitierPropositionCommandSerializer(DTOSerializer):
    class Meta:
        source = InitierPropositionCommand

    type_admission = serializers.ChoiceField(choices=AdmissionType.choices())
    commission_proximite = serializers.ChoiceField(
        choices=ChoixCommissionProximiteCDEouCLSM.choices()
        + ChoixCommissionProximiteCDSS.choices()
        + ChoixSousDomaineSciences.choices(),
        allow_blank=True,
    )


class CompleterPropositionCommandSerializer(InitierPropositionCommandSerializer):
    documents_projet = serializers.ListField(child=serializers.CharField())
    graphe_gantt = serializers.ListField(child=serializers.CharField())
    proposition_programme_doctoral = serializers.ListField(child=serializers.CharField())
    projet_formation_complementaire = serializers.ListField(child=serializers.CharField())
    lettres_recommandation = serializers.ListField(child=serializers.CharField())
    doctorat_deja_realise = serializers.ChoiceField(
        choices=ChoixDoctoratDejaRealise.choices(),
        default=ChoixDoctoratDejaRealise.NO.name,
    )
    langue_redaction_these = serializers.ChoiceField(
        choices=ChoixLangueRedactionThese.choices(),
        default=ChoixLangueRedactionThese.UNDECIDED.name,
    )
    institut_these = RelatedInstituteField(required=False)

    class Meta:
        source = CompleterPropositionCommand


class SectorDTOSerializer(serializers.Serializer):
    sigle = serializers.ReadOnlyField()
    intitule = serializers.ReadOnlyField()


class DoctoratDTOSerializer(DTOSerializer):
    class Meta:
        source = DoctoratDTO


class FormationGeneraleDTOSerializer(DTOSerializer):
    class Meta:
        source = FormationDTO


class FormationContinueDTOSerializer(DTOSerializer):
    class Meta:
        source = FormationDTO
