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
from typing import Optional, Dict

from rest_framework import serializers

from admission.api.serializers.fields import (
    ACTION_LINKS,
    AnswerToSpecificQuestionField,
    CONTINUING_EDUCATION_ACTION_LINKS,
    DOCTORATE_ACTION_LINKS,
    GENERAL_EDUCATION_ACTION_LINKS,
    RelatedInstituteField,
)
from admission.api.serializers.mixins import IncludedFieldsMixin
from admission.contrib.models import DoctorateAdmission, GeneralEducationAdmission
from admission.ddd.admission.doctorat.preparation.commands import CompleterPropositionCommand, InitierPropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixLangueRedactionThese,
    ChoixSousDomaineSciences,
    ChoixTypeAdmission,
)
from admission.ddd.admission.doctorat.preparation.dtos import DoctoratDTO, PropositionDTO as DoctoratPropositionDTO
from admission.ddd.admission.dtos.formation import FormationDTO
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutPropositionContinue
from admission.ddd.admission.formation_continue.dtos import PropositionDTO as FormationContinuePropositionDTO
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.dtos import PropositionDTO as FormationGeneralePropositionDTO
from backoffice.settings.rest_framework.fields import ActionLinksField
from base.utils.serializers import DTOSerializer

__all__ = [
    "PropositionCreatePermissionsSerializer",
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
    "GeneralEducationPropositionIdentityWithStatusSerializer",
]

from reference.api.serializers.language import RelatedLanguageField

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

STATUT_A_COMPLETER = "A_COMPLETER"
STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS = "TRAITEMENT_UCLOUVAIN_EN_COURS"


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
            "created_at",
            "modified_at",
        ]


class PropositionIdentityDTOSerializer(serializers.Serializer):
    uuid = serializers.ReadOnlyField()


class GeneralEducationPropositionIdentityWithStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralEducationAdmission
        fields = [
            "uuid",
            "status",
        ]


class DoctoratDTOSerializer(DTOSerializer):
    class Meta:
        source = DoctoratDTO


class FormationGeneraleDTOSerializer(DTOSerializer):
    campus = serializers.CharField(source='campus.nom', default='')
    campus_inscription = serializers.CharField(source='campus_inscription.nom', default='')

    class Meta:
        source = FormationDTO


class FormationContinueDTOSerializer(DTOSerializer):
    campus = serializers.CharField(source='campus.nom', default='')
    campus_inscription = serializers.CharField(source='campus_inscription.nom', default='')

    class Meta:
        source = FormationDTO


class DoctoratePropositionSearchDTOSerializer(IncludedFieldsMixin, DTOSerializer):
    links = ActionLinksField(
        actions={
            'retrieve_training_choice': DOCTORATE_ACTION_LINKS['retrieve_doctorate_training_choice'],
            'update_training_choice': DOCTORATE_ACTION_LINKS['update_doctorate_training_choice'],
            **{
                action: DOCTORATE_ACTION_LINKS[action]
                for action in [
                    # Profile
                    'retrieve_person',
                    'update_person',
                    'retrieve_coordinates',
                    'update_coordinates',
                    'retrieve_secondary_studies',
                    'update_secondary_studies',
                    'retrieve_languages',
                    'update_languages',
                    'destroy_proposition',
                    'submit_proposition',
                    'retrieve_proposition',
                    'update_proposition',
                    'retrieve_cotutelle',
                    'update_cotutelle',
                    'retrieve_supervision',
                    'retrieve_curriculum',
                    'update_curriculum',
                    'retrieve_confirmation',
                    'update_confirmation',
                    'retrieve_accounting',
                    'update_accounting',
                    'retrieve_doctoral_training',
                    'retrieve_complementary_training',
                    'retrieve_course_enrollment',
                    'destroy_proposition',
                    'retrieve_jury_preparation',
                ]
            },
        }
    )

    # This is to prevent schema from breaking on JSONField
    erreurs = None
    reponses_questions_specifiques = None
    elements_confirmation = None

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
            'pdf_recapitulatif',
        ]


class PropositionStatusMixin(serializers.Serializer):
    statut = serializers.SerializerMethodField()

    STATUS_TO_PORTAL_STATUS = {}

    def get_statut(self, obj):
        return self.STATUS_TO_PORTAL_STATUS.get(obj.statut, obj.statut)


class GeneralEducationPropositionStatusMixin(PropositionStatusMixin):
    STATUS_TO_PORTAL_STATUS = {
        ChoixStatutPropositionGenerale.A_COMPLETER_POUR_SIC.name: STATUT_A_COMPLETER,
        ChoixStatutPropositionGenerale.A_COMPLETER_POUR_FAC.name: STATUT_A_COMPLETER,
        ChoixStatutPropositionGenerale.COMPLETEE_POUR_SIC.name: STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS,
        ChoixStatutPropositionGenerale.COMPLETEE_POUR_FAC.name: STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS,
        ChoixStatutPropositionGenerale.TRAITEMENT_FAC.name: STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS,
        ChoixStatutPropositionGenerale.RETOUR_DE_FAC.name: STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS,
        ChoixStatutPropositionGenerale.ATTENTE_VALIDATION_DIRECTION.name: STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS,
    }


class ContinuingEducationPropositionStatusMixin(PropositionStatusMixin):
    STATUS_TO_PORTAL_STATUS = {
        ChoixStatutPropositionContinue.A_COMPLETER_POUR_FAC.name: STATUT_A_COMPLETER,
        ChoixStatutPropositionContinue.EN_ATTENTE.name: STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS,
        ChoixStatutPropositionContinue.COMPLETEE_POUR_FAC.name: STATUT_TRAITEMENT_UCLOUVAIN_EN_COURS,
    }


class GeneralEducationPropositionSearchDTOSerializer(
    IncludedFieldsMixin,
    GeneralEducationPropositionStatusMixin,
    DTOSerializer,
):
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
                'retrieve_specific_question',
                'update_specific_question',
                # Project
                'retrieve_training_choice',
                'update_training_choice',
                'retrieve_accounting',
                'update_accounting',
                'submit_proposition',
                # Proposition
                'destroy_proposition',
                'retrieve_documents',
                'update_documents',
                # Payment
                'pay_after_submission',
                'pay_after_request',
            ]
        }
    )

    formation = FormationGeneraleDTOSerializer()

    # This is to prevent schema from breaking on JSONField
    erreurs = None
    reponses_questions_specifiques = None
    elements_confirmation = None
    documents_demandes = None
    droits_inscription_montant_autre = None

    class Meta:
        source = FormationGeneralePropositionDTO

        fields = [
            'uuid',
            'formation',
            'reference',
            'matricule_candidat',
            'prenom_candidat',
            'nom_candidat',
            'creee_le',
            'statut',
            'links',
            'pdf_recapitulatif',
        ]


class ContinuingEducationPropositionSearchDTOSerializer(
    IncludedFieldsMixin,
    ContinuingEducationPropositionStatusMixin,
    DTOSerializer,
):
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
                'retrieve_specific_question',
                'update_specific_question',
                # Project
                'retrieve_training_choice',
                'update_training_choice',
                'submit_proposition',
                # Proposition
                'destroy_proposition',
                'retrieve_documents',
                'update_documents',
            ]
        }
    )

    formation = FormationContinueDTOSerializer()

    # This is to prevent schema from breaking on JSONField
    erreurs = None
    reponses_questions_specifiques = None
    elements_confirmation = None
    documents_demandes = None

    class Meta:
        source = FormationContinuePropositionDTO
        fields = [
            'uuid',
            'reference',
            'formation',
            'matricule_candidat',
            'prenom_candidat',
            'nom_candidat',
            'creee_le',
            'statut',
            'links',
            'pdf_recapitulatif',
        ]


class PropositionSearchSerializer(serializers.Serializer):
    links = ActionLinksField(
        actions={
            'create_training_choice': ACTION_LINKS['create_training_choice'],
        }
    )

    doctorate_propositions = DoctoratePropositionSearchDTOSerializer(many=True)
    general_education_propositions = GeneralEducationPropositionSearchDTOSerializer(many=True)
    continuing_education_propositions = ContinuingEducationPropositionSearchDTOSerializer(many=True)


class PropositionCreatePermissionsSerializer(serializers.Serializer):
    links = ActionLinksField(
        actions={
            'create_person': ACTION_LINKS['update_person'],
            'create_coordinates': ACTION_LINKS['update_coordinates'],
            'create_training_choice': ACTION_LINKS['create_training_choice'],
        }
    )


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
            # Course choice
            'retrieve_training_choice': DOCTORATE_ACTION_LINKS['retrieve_doctorate_training_choice'],
            'update_training_choice': DOCTORATE_ACTION_LINKS['update_doctorate_training_choice'],
            # Cotutelle
            'retrieve_cotutelle': DOCTORATE_ACTION_LINKS['retrieve_cotutelle'],
            'update_cotutelle': DOCTORATE_ACTION_LINKS['update_cotutelle'],
            # Supervision
            'add_approval': DOCTORATE_ACTION_LINKS['add_approval'],
            'add_member': DOCTORATE_ACTION_LINKS['add_member'],
            'edit_external_member': DOCTORATE_ACTION_LINKS['edit_external_member'],
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
            # Jury
            'retrieve_jury_preparation': DOCTORATE_ACTION_LINKS['retrieve_jury_preparation'],
            'list_jury_members': DOCTORATE_ACTION_LINKS['list_jury_members'],
        }
    )
    reponses_questions_specifiques = AnswerToSpecificQuestionField()
    elements_confirmation = None
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
            'intitule_secteur_formation',
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
            'nom_institut_these',
            'sigle_institut_these',
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
            'reponses_questions_specifiques',
            'curriculum',
            'pdf_recapitulatif',
        ]
        extra_kwargs = {
            'autre_bourse_recherche': {'max_length': 255},
            'lieu_these': {'max_length': 255},
            'titre_projet': {'max_length': 255},
            'institution': {'max_length': 255},
            'domaine_these': {'max_length': 255},
            'raison_non_soutenue': {'max_length': 255},
        }


class GeneralEducationPropositionDTOSerializer(
    IncludedFieldsMixin,
    GeneralEducationPropositionStatusMixin,
    DTOSerializer,
):
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
                'retrieve_documents',
                'update_documents',
                # Payment
                'view_payment',
                'pay_after_submission',
                'pay_after_request',
            ]
        }
    )

    formation = FormationGeneraleDTOSerializer()

    reponses_questions_specifiques = AnswerToSpecificQuestionField()
    erreurs = serializers.JSONField()
    elements_confirmation = None
    documents_demandes = None
    droits_inscription_montant_autre = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['erreurs'].field_schema = PROPOSITION_ERROR_SCHEMA

    class Meta:
        source = FormationGeneralePropositionDTO

        fields = [
            'uuid',
            'reference',
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
            'curriculum',
            'equivalence_diplome',
            'pdf_recapitulatif',
            'documents_additionnels',
            'poste_diplomatique',
        ]


class ContinuingEducationPropositionDTOSerializer(
    IncludedFieldsMixin,
    ContinuingEducationPropositionStatusMixin,
    DTOSerializer,
):
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
                # Proposition
                'destroy_proposition',
                'submit_proposition',
                'retrieve_documents',
                'update_documents',
            ]
        }
    )

    formation = FormationContinueDTOSerializer()

    reponses_questions_specifiques = AnswerToSpecificQuestionField()
    erreurs = serializers.JSONField()
    elements_confirmation = None
    documents_demandes = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['erreurs'].field_schema = PROPOSITION_ERROR_SCHEMA

    class Meta:
        source = FormationContinuePropositionDTO
        fields = [
            'uuid',
            'reference',
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
            'inscription_a_titre',
            'nom_siege_social',
            'numero_unique_entreprise',
            'numero_tva_entreprise',
            'adresse_mail_professionnelle',
            'type_adresse_facturation',
            'adresse_facturation',
            'pays_nationalite_candidat',
            'pays_nationalite_ue_candidat',
            'copie_titre_sejour',
            'pdf_recapitulatif',
            'documents_additionnels',
            'motivations',
            'moyens_decouverte_formation',
            'autre_moyen_decouverte_formation',
            'adresses_emails_gestionnaires_formation',
            'aide_a_la_formation',
            'inscription_au_role_obligatoire',
            'etat_formation',
            'marque_d_interet',
        ]
        extra_kwargs = {
            'nom_siege_social': {'max_length': 255},
            'numero_unique_entreprise': {'max_length': 255},
            'numero_tva_entreprise': {'max_length': 255},
            'adresse_facturation_destinataire': {'max_length': 255},
        }


class InitierPropositionCommandSerializer(DTOSerializer):
    class Meta:
        source = InitierPropositionCommand

    type_admission = serializers.ChoiceField(choices=ChoixTypeAdmission.choices())
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
    langue_redaction_these = RelatedLanguageField(required=False)
    institut_these = RelatedInstituteField(required=False)

    class Meta:
        source = CompleterPropositionCommand


class SectorDTOSerializer(serializers.Serializer):
    sigle = serializers.ReadOnlyField()
    intitule = serializers.ReadOnlyField()
