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

from admission.api.serializers.fields import (
    DOCTORATE_ACTION_LINKS,
    ActionLinksField,
    RelatedInstituteField,
    CONTINUING_EDUCATION_ACTION_LINKS,
    GENERAL_EDUCATION_ACTION_LINKS,
    AnswerToSpecificQuestionField,
)
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
    "DoctoratePropositionDTOSerializer",
    "DoctoratePropositionSearchDTOSerializer",
    "GeneralEducationPropositionSearchDTOSerializer",
    "ContinuingEducationPropositionSearchDTOSerializer",
    "FormationContinueDTOSerializer",
    "FormationGeneraleDTOSerializer",
    "GeneralEducationPropositionDTOSerializer",
    "ContinuingEducationPropositionDTOSerializer",
    "PROPOSITION_ERROR_SCHEMA",
]


PROPOSITION_ERROR_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "status_code": {"type": "string"},
            "detail": {"type": "string"},
        },
    },
}


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
            'retrieve_person': DOCTORATE_ACTION_LINKS['retrieve_person'],
            'update_person': DOCTORATE_ACTION_LINKS['update_person'],
            # Coordinates
            'retrieve_coordinates': DOCTORATE_ACTION_LINKS['retrieve_coordinates'],
            'update_coordinates': DOCTORATE_ACTION_LINKS['update_coordinates'],
            # Secondary studies
            'retrieve_secondary_studies': DOCTORATE_ACTION_LINKS['retrieve_secondary_studies'],
            'update_secondary_studies': DOCTORATE_ACTION_LINKS['update_secondary_studies'],
            # Language knowledge
            'retrieve_languages': DOCTORATE_ACTION_LINKS['retrieve_languages'],
            'update_languages': DOCTORATE_ACTION_LINKS['update_languages'],
            # Proposition
            'destroy_proposition': DOCTORATE_ACTION_LINKS['destroy_proposition'],
            'submit_proposition': DOCTORATE_ACTION_LINKS['submit_proposition'],
            # Project
            'retrieve_proposition': DOCTORATE_ACTION_LINKS['retrieve_proposition'],
            'update_proposition': DOCTORATE_ACTION_LINKS['update_proposition'],
            # Cotutelle
            'retrieve_cotutelle': DOCTORATE_ACTION_LINKS['retrieve_cotutelle'],
            'update_cotutelle': DOCTORATE_ACTION_LINKS['update_cotutelle'],
            # Supervision
            'retrieve_supervision': DOCTORATE_ACTION_LINKS['retrieve_supervision'],
            # Curriculum
            'retrieve_curriculum': DOCTORATE_ACTION_LINKS['retrieve_curriculum'],
            'update_curriculum': DOCTORATE_ACTION_LINKS['update_curriculum'],
            # Confirmation
            'retrieve_confirmation': DOCTORATE_ACTION_LINKS['retrieve_confirmation'],
            'update_confirmation': DOCTORATE_ACTION_LINKS['update_confirmation'],
            # Accounting
            'retrieve_accounting': DOCTORATE_ACTION_LINKS['retrieve_accounting'],
            'update_accounting': DOCTORATE_ACTION_LINKS['update_accounting'],
            # Training
            'retrieve_doctoral_training': DOCTORATE_ACTION_LINKS['retrieve_doctoral_training'],
            'retrieve_complementary_training': DOCTORATE_ACTION_LINKS['retrieve_complementary_training'],
            'retrieve_course_enrollment': DOCTORATE_ACTION_LINKS['retrieve_course_enrollment'],
            # Training choice
            'retrieve_training_choice': DOCTORATE_ACTION_LINKS['retrieve_doctorate_training_choice'],
        }
    )

    # This is to prevent schema from breaking on JSONField
    erreurs = None
    reponses_questions_specifiques = None

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
    links = ActionLinksField(
        actions={
            action: GENERAL_EDUCATION_ACTION_LINKS[action]
            for action in [
                # Profile
                'retrieve_person',
                'retrieve_coordinates',
                'retrieve_secondary_studies',
                'retrieve_curriculum',
                'retrieve_specific_question',
                # Project
                'retrieve_training_choice',
                'retrieve_accounting',
                # Proposition
                'destroy_proposition',
            ]
        }
    )

    # This is to prevent schema from breaking on JSONField
    erreurs = None
    reponses_questions_specifiques = None

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
    links = ActionLinksField(
        actions={
            action: CONTINUING_EDUCATION_ACTION_LINKS[action]
            for action in [
                # Profile
                'retrieve_person',
                'retrieve_coordinates',
                'retrieve_secondary_studies',
                'retrieve_curriculum',
                'retrieve_specific_question',
                # Project
                'retrieve_training_choice',
                'retrieve_accounting',
                # Proposition
                'destroy_proposition',
            ]
        }
    )

    # This is to prevent schema from breaking on JSONField
    erreurs = None
    reponses_questions_specifiques = None

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
    links = ActionLinksField(
        actions={
            'create_doctorate_proposition': DOCTORATE_ACTION_LINKS['create_doctorate_proposition'],
            'create_general_proposition': GENERAL_EDUCATION_ACTION_LINKS['create_proposition'],
            'create_continuing_proposition': CONTINUING_EDUCATION_ACTION_LINKS['create_proposition'],
        }
    )

    doctorate_propositions = DoctoratePropositionSearchDTOSerializer(many=True)
    general_education_propositions = GeneralEducationPropositionSearchDTOSerializer(many=True)
    continuing_education_propositions = ContinuingEducationPropositionSearchDTOSerializer(many=True)


class DoctoratePropositionDTOSerializer(IncludedFieldsMixin, DTOSerializer):
    links = ActionLinksField(
        actions={
            # Profile
            # Person
            'retrieve_person': DOCTORATE_ACTION_LINKS['retrieve_person'],
            'update_person': DOCTORATE_ACTION_LINKS['update_person'],
            # Coordinates
            'retrieve_coordinates': DOCTORATE_ACTION_LINKS['retrieve_coordinates'],
            'update_coordinates': DOCTORATE_ACTION_LINKS['update_coordinates'],
            # Secondary studies
            'retrieve_secondary_studies': DOCTORATE_ACTION_LINKS['retrieve_secondary_studies'],
            'update_secondary_studies': DOCTORATE_ACTION_LINKS['update_secondary_studies'],
            # Language knowledge
            'retrieve_languages': DOCTORATE_ACTION_LINKS['retrieve_languages'],
            'update_languages': DOCTORATE_ACTION_LINKS['update_languages'],
            # Proposition
            'destroy_proposition': DOCTORATE_ACTION_LINKS['destroy_proposition'],
            'submit_proposition': DOCTORATE_ACTION_LINKS['submit_proposition'],
            # Project
            'retrieve_proposition': DOCTORATE_ACTION_LINKS['retrieve_proposition'],
            'update_proposition': DOCTORATE_ACTION_LINKS['update_proposition'],
            # Training choice
            'retrieve_training_choice': DOCTORATE_ACTION_LINKS['retrieve_doctorate_training_choice'],
            'update_training_choice': DOCTORATE_ACTION_LINKS['update_doctorate_training_choice'],
            # Cotutelle
            'retrieve_cotutelle': DOCTORATE_ACTION_LINKS['retrieve_cotutelle'],
            'update_cotutelle': DOCTORATE_ACTION_LINKS['update_cotutelle'],
            # Supervision
            'add_approval': DOCTORATE_ACTION_LINKS['add_approval'],
            'add_member': DOCTORATE_ACTION_LINKS['add_member'],
            'remove_member': DOCTORATE_ACTION_LINKS['remove_member'],
            'set_reference_promoter': DOCTORATE_ACTION_LINKS['set_reference_promoter'],
            'retrieve_supervision': DOCTORATE_ACTION_LINKS['retrieve_supervision'],
            'request_signatures': DOCTORATE_ACTION_LINKS['request_signatures'],
            'approve_by_pdf': DOCTORATE_ACTION_LINKS['approve_by_pdf'],
            # Curriculum
            'retrieve_curriculum': DOCTORATE_ACTION_LINKS['retrieve_curriculum'],
            'update_curriculum': DOCTORATE_ACTION_LINKS['update_curriculum'],
            # Confirmation
            'retrieve_confirmation': DOCTORATE_ACTION_LINKS['retrieve_confirmation'],
            'update_confirmation': DOCTORATE_ACTION_LINKS['update_confirmation'],
            # Accounting
            'retrieve_accounting': DOCTORATE_ACTION_LINKS['retrieve_accounting'],
            'update_accounting': DOCTORATE_ACTION_LINKS['update_accounting'],
            # Training
            'retrieve_doctoral_training': DOCTORATE_ACTION_LINKS['retrieve_doctoral_training'],
            'retrieve_complementary_training': DOCTORATE_ACTION_LINKS['retrieve_complementary_training'],
            'retrieve_course_enrollment': DOCTORATE_ACTION_LINKS['retrieve_course_enrollment'],
        }
    )
    reponses_questions_specifiques = AnswerToSpecificQuestionField()

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
            'annee_calculee',
            'pot_calcule',
            'date_fin_pot',
            'matricule_candidat',
            'code_secteur_formation',
            'commission_proximite',
            'type_financement',
            'type_contrat_travail',
            'eft',
            'bourse_recherche',
            'autre_bourse_recherche',
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
            'bourse_erasmus_mundus',
            'reponses_questions_specifiques',
            'curriculum',
        ]


class GeneralEducationPropositionDTOSerializer(IncludedFieldsMixin, DTOSerializer):
    links = ActionLinksField(
        actions={
            action: GENERAL_EDUCATION_ACTION_LINKS[action]
            for action in [
                # Profile
                'retrieve_person',
                'update_person',
                'retrieve_coordinates',
                'update_coordinates',
                'retrieve_secondary_studies',
                'update_secondary_studies',
                'retrieve_curriculum',
                'update_curriculum',
                # Project
                'retrieve_training_choice',
                'update_training_choice',
                'retrieve_specific_question',
                'update_specific_question',
                'retrieve_accounting',
                'update_accounting',
                # Proposition
                'destroy_proposition',
                'submit_proposition',
            ]
        }
    )
    reponses_questions_specifiques = AnswerToSpecificQuestionField()
    erreurs = serializers.JSONField()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['erreurs'].field_schema = PROPOSITION_ERROR_SCHEMA

    class Meta:
        source = FormationGeneralePropositionDTO

        fields = [
            'uuid',
            'formation',
            'annee_calculee',
            'pot_calcule',
            'date_fin_pot',
            'matricule_candidat',
            'prenom_candidat',
            'nom_candidat',
            'creee_le',
            'statut',
            'links',
            'erreurs',
            'bourse_double_diplome',
            'bourse_internationale',
            'bourse_erasmus_mundus',
            'reponses_questions_specifiques',
            'continuation_cycle_bachelier',
            'attestation_continuation_cycle_bachelier',
            'curriculum',
            'equivalence_diplome',
        ]


class ContinuingEducationPropositionDTOSerializer(IncludedFieldsMixin, DTOSerializer):
    links = ActionLinksField(
        actions={
            action: CONTINUING_EDUCATION_ACTION_LINKS[action]
            for action in [
                # Profile
                'retrieve_person',
                'update_person',
                'retrieve_coordinates',
                'update_coordinates',
                'retrieve_secondary_studies',
                'update_secondary_studies',
                'retrieve_curriculum',
                'update_curriculum',
                # Project
                'retrieve_training_choice',
                'update_training_choice',
                'retrieve_specific_question',
                'update_specific_question',
                'retrieve_accounting',
                'update_accounting',
                # Proposition
                'destroy_proposition',
                'submit_proposition',
            ]
        }
    )
    reponses_questions_specifiques = AnswerToSpecificQuestionField()

    erreurs = serializers.JSONField()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['erreurs'].field_schema = PROPOSITION_ERROR_SCHEMA

    class Meta:
        source = FormationContinuePropositionDTO
        fields = [
            'uuid',
            'formation',
            'annee_calculee',
            'pot_calcule',
            'date_fin_pot',
            'matricule_candidat',
            'prenom_candidat',
            'nom_candidat',
            'creee_le',
            'statut',
            'links',
            'erreurs',
            'reponses_questions_specifiques',
            'curriculum',
            'equivalence_diplome',
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
