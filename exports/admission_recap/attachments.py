# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from io import BytesIO
from typing import List, Optional, Dict

import img2pdf
from django.utils.translation import override
from osis_document.api.utils import get_raw_content_remotely

from admission.constants import IMAGE_MIME_TYPES, SUPPORTED_MIME_TYPES
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeFinancement,
    ChoixEtatSignature,
)
from admission.ddd.admission.doctorat.preparation.dtos import ExperienceAcademiqueDTO
from admission.ddd.admission.doctorat.preparation.dtos.comptabilite import (
    DerniersEtablissementsSuperieursCommunauteFrancaiseFrequentesDTO,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceNonAcademiqueDTO
from admission.ddd.admission.domain.validator._should_comptabilite_etre_completee import recuperer_champs_requis_dto
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.enums.emplacement_document import (
    DocumentsIdentification,
    DocumentsEtudesSecondaires,
    DocumentsConnaissancesLangues,
    DocumentsCurriculum,
    DocumentsQuestionsSpecifiques,
    DocumentsComptabilite,
    DocumentsProjetRecherche,
    DocumentsCotutelle,
    DocumentsSupervision,
    IdentifiantBaseEmplacementDocument,
    DocumentsSuiteAutorisation,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_generale.domain.model.enums import (
    CHOIX_DIPLOME_OBTENU,
    ChoixStatutPropositionGenerale,
)
from admission.exports.admission_recap.constants import CURRICULUM_ACTIVITY_LABEL
from base.models.enums.education_group_types import TrainingType
from base.utils.utils import format_academic_year
from osis_profile.models.enums.curriculum import TranscriptType
from osis_profile.models.enums.education import ForeignDiplomaTypes, Equivalence


class Attachment:
    def __init__(
        self,
        identifier: str,
        label: str,
        uuids: List[str],
        sub_identifier='',
        sub_identifier_label='',
        required=False,
        candidate_language_label='',
        candidate_language='',
        label_interpolation: Optional[dict] = None,
    ):
        self.identifier = f'{sub_identifier}.{identifier}' if sub_identifier else identifier
        self.label = self._get_label(label, sub_identifier_label, label_interpolation)

        self.uuids = [str(uuid) for uuid in uuids if uuid]
        self.required = required

        if candidate_language_label:
            self.candidate_language_label = candidate_language_label
        else:
            with override(language=candidate_language):
                self.candidate_language_label = str(self._get_label(label, sub_identifier_label, label_interpolation))

    @staticmethod
    def _get_label(base_label: str, sub_label: str, label_interpolation: Optional[dict]):
        label = f'{base_label} {sub_label}' if sub_label else base_label
        if label_interpolation:
            return label % label_interpolation
        return label

    def get_raw(self, token: Optional[str], metadata: Optional[Dict], default_content: BytesIO) -> BytesIO:
        """
        Returns the raw content of an attachment if a token is specified and the mimetype is supported else a default
        content.
        """
        if token and metadata and metadata.get('mimetype') in SUPPORTED_MIME_TYPES:
            raw_content = get_raw_content_remotely(token)
            if not raw_content:
                return default_content
            if metadata.get('mimetype') in IMAGE_MIME_TYPES:
                raw_content = img2pdf.convert(raw_content, rotation=img2pdf.Rotation.ifvalid)
            return BytesIO(raw_content)
        return default_content

    def __eq__(self, other):
        return isinstance(other, Attachment) and self.identifier == other.identifier

    def __str__(self):
        return self.label


def get_identification_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the identification attachments."""
    attachments = [
        Attachment(
            identifier='PHOTO_IDENTITE',
            label=DocumentsIdentification['PHOTO_IDENTITE'],
            uuids=context.identification.photo_identite,
            required=True,
            candidate_language=context.identification.langue_contact,
        )
    ]
    if context.identification.numero_carte_identite or context.identification.numero_registre_national_belge:
        attachments.append(
            Attachment(
                identifier='CARTE_IDENTITE',
                label=DocumentsIdentification['CARTE_IDENTITE'],
                uuids=context.identification.carte_identite,
                required=True,
                candidate_language=context.identification.langue_contact,
            )
        )
    if context.identification.numero_passeport:
        attachments.append(
            Attachment(
                identifier='PASSEPORT',
                label=DocumentsIdentification['PASSEPORT'],
                uuids=context.identification.passeport,
                required=True,
                candidate_language=context.identification.langue_contact,
            )
        )
    return attachments


def get_secondary_studies_attachments(
    context: ResumePropositionDTO,
    specific_questions: List[QuestionSpecifiqueDTO],
    need_translations: bool = None,
    ue_or_assimilated: bool = None,
) -> List[Attachment]:
    """Returns the secondary studies attachments."""
    attachments = []
    got_diploma = context.etudes_secondaires.diplome_etudes_secondaires
    if context.proposition.formation.type == TrainingType.BACHELOR.name:
        if context.etudes_secondaires.diplome_belge:
            if got_diploma in CHOIX_DIPLOME_OBTENU:
                attachments.append(
                    Attachment(
                        identifier='DIPLOME_BELGE_DIPLOME',
                        label=DocumentsEtudesSecondaires['DIPLOME_BELGE_DIPLOME'],
                        uuids=context.etudes_secondaires.diplome_belge.diplome,
                        required=True,
                        candidate_language=context.identification.langue_contact,
                    )
                )
        elif context.etudes_secondaires.diplome_etranger:
            if context.etudes_secondaires.diplome_etranger.type_diplome == ForeignDiplomaTypes.NATIONAL_BACHELOR.name:
                if ue_or_assimilated:
                    if context.etudes_secondaires.diplome_etranger.equivalence == Equivalence.YES.name:
                        attachments.append(
                            Attachment(
                                identifier='DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE',
                                label=DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE'],
                                uuids=context.etudes_secondaires.diplome_etranger.decision_final_equivalence_ue,
                                required=True,
                                candidate_language=context.identification.langue_contact,
                            )
                        )
                    elif context.etudes_secondaires.diplome_etranger.equivalence == Equivalence.PENDING.name:
                        attachments.append(
                            Attachment(
                                identifier='DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE',
                                label=DocumentsEtudesSecondaires['DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE'],
                                uuids=context.etudes_secondaires.diplome_etranger.preuve_decision_equivalence,
                                required=True,
                                candidate_language=context.identification.langue_contact,
                            )
                        )
                else:
                    attachments.append(
                        Attachment(
                            identifier='DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE',
                            label=DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE'],
                            uuids=context.etudes_secondaires.diplome_etranger.decision_final_equivalence_hors_ue,
                            required=True,
                            candidate_language=context.identification.langue_contact,
                        )
                    )

            if got_diploma in CHOIX_DIPLOME_OBTENU:
                attachments.append(
                    Attachment(
                        identifier='DIPLOME_ETRANGER_DIPLOME',
                        label=DocumentsEtudesSecondaires['DIPLOME_ETRANGER_DIPLOME'],
                        uuids=context.etudes_secondaires.diplome_etranger.diplome,
                        required=True,
                        candidate_language=context.identification.langue_contact,
                    ),
                )

                if need_translations:
                    attachments.append(
                        Attachment(
                            identifier='DIPLOME_ETRANGER_TRADUCTION_DIPLOME',
                            label=DocumentsEtudesSecondaires['DIPLOME_ETRANGER_TRADUCTION_DIPLOME'],
                            uuids=context.etudes_secondaires.diplome_etranger.traduction_diplome,
                            required=True,
                            candidate_language=context.identification.langue_contact,
                        )
                    )

            attachments.append(
                Attachment(
                    identifier='DIPLOME_ETRANGER_RELEVE_NOTES',
                    label=DocumentsEtudesSecondaires['DIPLOME_ETRANGER_RELEVE_NOTES'],
                    uuids=context.etudes_secondaires.diplome_etranger.releve_notes,
                    required=True,
                    candidate_language=context.identification.langue_contact,
                )
            )
            if need_translations:
                attachments.append(
                    Attachment(
                        identifier='DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES',
                        label=DocumentsEtudesSecondaires['DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES'],
                        uuids=context.etudes_secondaires.diplome_etranger.traduction_releve_notes,
                        required=True,
                        candidate_language=context.identification.langue_contact,
                    )
                )

        elif context.etudes_secondaires.alternative_secondaires:
            attachments.append(
                Attachment(
                    identifier='ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE',
                    label=DocumentsEtudesSecondaires['ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE'],
                    uuids=context.etudes_secondaires.alternative_secondaires.examen_admission_premier_cycle,
                    required=not context.curriculum.candidat_est_potentiel_vae,
                    candidate_language=context.identification.langue_contact,
                )
            )

    attachments.extend(get_dynamic_questions_attachments(specific_questions))

    return attachments


def get_languages_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the languages attachments."""
    return [
        Attachment(
            identifier='CERTIFICAT_CONNAISSANCE_LANGUE',
            label=DocumentsConnaissancesLangues['CERTIFICAT_CONNAISSANCE_LANGUE'],
            sub_identifier=language.langue,
            sub_identifier_label=language.nom_langue,
            uuids=language.certificat,
            required=False,
            candidate_language=context.identification.langue_contact,
        )
        for language in context.connaissances_langues
    ]


def get_curriculum_attachments(
    context: ResumePropositionDTO,
    specific_questions: List[QuestionSpecifiqueDTO],
    display_equivalence: bool,
    display_curriculum: bool,
    require_equivalence: bool,
    require_curriculum: bool,
    **kwargs,
) -> List[Attachment]:
    """Returns the curriculum attachments."""
    attachments = []

    if display_equivalence:
        attachments.append(
            Attachment(
                identifier='DIPLOME_EQUIVALENCE',
                label=DocumentsCurriculum['DIPLOME_EQUIVALENCE'],
                uuids=context.proposition.equivalence_diplome,
                required=require_equivalence,
                candidate_language=context.identification.langue_contact,
            )
        )

    if display_curriculum:
        attachments.append(
            Attachment(
                identifier='CURRICULUM',
                label=DocumentsCurriculum['CURRICULUM'],
                uuids=context.proposition.curriculum,
                required=require_curriculum,
                candidate_language=context.identification.langue_contact,
            )
        )

    attachments.extend(get_dynamic_questions_attachments(specific_questions))

    return attachments


def get_curriculum_academic_experience_attachments(
    context: ResumePropositionDTO,
    experience: ExperienceAcademiqueDTO,
    translation_required: bool,
) -> List[Attachment]:
    """Returns the academic experience attachments."""
    attachments = []
    if context.est_proposition_doctorale or context.est_proposition_generale:
        if experience.type_releve_notes == TranscriptType.ONE_FOR_ALL_YEARS.name:
            attachments.append(
                Attachment(
                    identifier='RELEVE_NOTES',
                    label=DocumentsCurriculum['RELEVE_NOTES'],
                    uuids=experience.releve_notes,
                    required=True,
                    candidate_language=context.identification.langue_contact,
                )
            )
            if translation_required:
                attachments.append(
                    Attachment(
                        identifier='TRADUCTION_RELEVE_NOTES',
                        label=DocumentsCurriculum['TRADUCTION_RELEVE_NOTES'],
                        uuids=experience.traduction_releve_notes,
                        required=True,
                        candidate_language=context.identification.langue_contact,
                    )
                )
        elif experience.type_releve_notes == TranscriptType.ONE_A_YEAR.name:
            for annee in experience.annees:
                sub_identifier = str(annee.annee)
                sub_identifier_label = format_academic_year(annee.annee)
                attachments.append(
                    Attachment(
                        identifier='RELEVE_NOTES_ANNUEL',
                        label=DocumentsCurriculum['RELEVE_NOTES_ANNUEL'],
                        sub_identifier=sub_identifier,
                        sub_identifier_label=sub_identifier_label,
                        uuids=annee.releve_notes,
                        required=True,
                        candidate_language=context.identification.langue_contact,
                    )
                )
                if translation_required:
                    attachments.append(
                        Attachment(
                            identifier='TRADUCTION_RELEVE_NOTES_ANNUEL',
                            label=DocumentsCurriculum['TRADUCTION_RELEVE_NOTES_ANNUEL'],
                            sub_identifier=sub_identifier,
                            sub_identifier_label=sub_identifier_label,
                            uuids=annee.traduction_releve_notes,
                            required=True,
                            candidate_language=context.identification.langue_contact,
                        )
                    )

    if experience.a_obtenu_diplome:
        if context.est_proposition_doctorale:
            attachments.append(
                Attachment(
                    identifier='RESUME_MEMOIRE',
                    label=DocumentsCurriculum['RESUME_MEMOIRE'],
                    uuids=experience.resume_memoire,
                    required=True,
                    candidate_language=context.identification.langue_contact,
                )
            )

        attachments.append(
            Attachment(
                identifier='DIPLOME',
                label=DocumentsCurriculum['DIPLOME'],
                uuids=experience.diplome,
                required=True,
                candidate_language=context.identification.langue_contact,
            )
        )

        if translation_required:
            attachments.append(
                Attachment(
                    identifier='TRADUCTION_DIPLOME',
                    label=DocumentsCurriculum['TRADUCTION_DIPLOME'],
                    uuids=experience.traduction_diplome,
                    required=True,
                    candidate_language=context.identification.langue_contact,
                )
            )

    return attachments


def get_curriculum_non_academic_experience_attachments(
    context: ResumePropositionDTO,
    experience: ExperienceNonAcademiqueDTO,
) -> List[Attachment]:
    """Returns the non academic experience attachments."""
    attachments = []
    if context.est_proposition_doctorale or context.est_proposition_generale:
        attachments.append(
            Attachment(
                identifier='CERTIFICAT_EXPERIENCE',
                label=CURRICULUM_ACTIVITY_LABEL[experience.type],
                uuids=experience.certificat,
                candidate_language=context.identification.langue_contact,
            )
        )
        return attachments


def get_specific_questions_attachments(
    context: ResumePropositionDTO,
    specific_questions: List[QuestionSpecifiqueDTO],
    eligible_for_reorientation: bool,
    eligible_for_modification: bool,
) -> List[Attachment]:
    """Returns the specific questions attachments."""
    attachments = []
    if context.est_proposition_continue and context.proposition.pays_nationalite_ue_candidat is False:
        attachments.append(
            Attachment(
                identifier='COPIE_TITRE_SEJOUR',
                label=DocumentsQuestionsSpecifiques['COPIE_TITRE_SEJOUR'],
                uuids=context.proposition.copie_titre_sejour,
                candidate_language=context.identification.langue_contact,
            )
        )

    if eligible_for_reorientation and context.proposition.est_reorientation_inscription_externe:
        attachments.append(
            Attachment(
                identifier='ATTESTATION_INSCRIPTION_REGULIERE',
                label=DocumentsQuestionsSpecifiques['ATTESTATION_INSCRIPTION_REGULIERE'],
                uuids=context.proposition.attestation_inscription_reguliere,
                required=True,
                candidate_language=context.identification.langue_contact,
            )
        )
    if eligible_for_modification and context.proposition.est_modification_inscription_externe:
        attachments.append(
            Attachment(
                identifier='FORMULAIRE_MODIFICATION_INSCRIPTION',
                label=DocumentsQuestionsSpecifiques['FORMULAIRE_MODIFICATION_INSCRIPTION'],
                uuids=context.proposition.formulaire_modification_inscription,
                required=True,
                candidate_language=context.identification.langue_contact,
            )
        )
    attachments.extend(get_dynamic_questions_attachments(specific_questions))
    attachments.append(
        Attachment(
            identifier='ADDITIONAL_DOCUMENTS',
            label=DocumentsQuestionsSpecifiques['ADDITIONAL_DOCUMENTS'],
            uuids=context.proposition.documents_additionnels,
            required=False,
            candidate_language=context.identification.langue_contact,
        )
    )
    return attachments


def get_accounting_attachments(
    context: ResumePropositionDTO,
    last_fr_institutes: DerniersEtablissementsSuperieursCommunauteFrancaiseFrequentesDTO,
    with_assimilation: bool,
    formatted_relationship: str,
) -> List[Attachment]:
    """Returns the accounting attachments."""
    attachments = []

    if last_fr_institutes:
        attachments.append(
            Attachment(
                identifier='ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT',
                label=DocumentsComptabilite['ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT'],
                label_interpolation={
                    'academic_year': format_academic_year(last_fr_institutes.annee),
                    'names': ', '.join(last_fr_institutes.noms),
                    'count': len(last_fr_institutes.noms),
                },
                uuids=context.comptabilite.attestation_absence_dette_etablissement,
                required=True,
                candidate_language=context.identification.langue_contact,
            )
        )

    if getattr(context.comptabilite, 'enfant_personnel', None):
        attachments.append(
            Attachment(
                identifier='ATTESTATION_ENFANT_PERSONNEL',
                label=DocumentsComptabilite['ATTESTATION_ENFANT_PERSONNEL'],
                uuids=context.comptabilite.attestation_enfant_personnel,
                candidate_language=context.identification.langue_contact,
            )
        )

    if with_assimilation:
        fields = recuperer_champs_requis_dto(
            nom_champ='type_situation_assimilation',
            comptabilite=context.comptabilite,
        )
        for field in fields:
            field_id = field.upper()
            if field_id in DocumentsComptabilite:
                attachments.append(
                    Attachment(
                        identifier=field_id,
                        label=DocumentsComptabilite[field_id],
                        label_interpolation={'person_concerned': formatted_relationship},
                        uuids=getattr(context.comptabilite, field),
                        required=True,
                        candidate_language=context.identification.langue_contact,
                    )
                )

    return attachments


def get_research_project_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the research project attachments."""
    attachments = []
    if context.proposition.type_financement == ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name:
        attachments.append(
            Attachment(
                identifier='PREUVE_BOURSE',
                label=DocumentsProjetRecherche['PREUVE_BOURSE'],
                uuids=context.proposition.bourse_preuve,
                candidate_language=context.identification.langue_contact,
            )
        )

    attachments += [
        Attachment(
            identifier='DOCUMENTS_PROJET',
            label=DocumentsProjetRecherche['DOCUMENTS_PROJET'],
            uuids=context.proposition.documents_projet,
            required=True,
            candidate_language=context.identification.langue_contact,
        ),
        Attachment(
            identifier='PROPOSITION_PROGRAMME_DOCTORAL',
            label=DocumentsProjetRecherche['PROPOSITION_PROGRAMME_DOCTORAL'],
            uuids=context.proposition.proposition_programme_doctoral,
            required=True,
            candidate_language=context.identification.langue_contact,
        ),
        Attachment(
            identifier='PROJET_FORMATION_COMPLEMENTAIRE',
            label=DocumentsProjetRecherche['PROJET_FORMATION_COMPLEMENTAIRE'],
            uuids=context.proposition.projet_formation_complementaire,
            candidate_language=context.identification.langue_contact,
        ),
        Attachment(
            identifier='GRAPHE_GANTT',
            label=DocumentsProjetRecherche['GRAPHE_GANTT'],
            uuids=context.proposition.graphe_gantt,
            candidate_language=context.identification.langue_contact,
        ),
        Attachment(
            identifier='LETTRES_RECOMMANDATION',
            label=DocumentsProjetRecherche['LETTRES_RECOMMANDATION'],
            uuids=context.proposition.lettres_recommandation,
            candidate_language=context.identification.langue_contact,
        ),
    ]

    return attachments


def get_cotutelle_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the cotutelle attachments."""
    attachments = []
    if (
        context.groupe_supervision
        and context.groupe_supervision.cotutelle
        and context.groupe_supervision.cotutelle.cotutelle
    ):
        attachments += [
            Attachment(
                identifier='DEMANDE_OUVERTURE',
                label=DocumentsCotutelle['DEMANDE_OUVERTURE'],
                uuids=context.groupe_supervision.cotutelle.demande_ouverture,
                required=True,
                candidate_language=context.identification.langue_contact,
            ),
            Attachment(
                identifier='CONVENTION',
                label=DocumentsCotutelle['CONVENTION'],
                uuids=context.groupe_supervision.cotutelle.convention,
                candidate_language=context.identification.langue_contact,
            ),
            Attachment(
                identifier='AUTRES_DOCUMENTS',
                label=DocumentsCotutelle['AUTRES_DOCUMENTS'],
                uuids=context.groupe_supervision.cotutelle.autres_documents,
                candidate_language=context.identification.langue_contact,
            ),
        ]
    return attachments


def get_supervision_group_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the supervision group attachments."""
    attachments = []
    for supervision_member in context.groupe_supervision.signatures_promoteurs:
        if supervision_member.pdf and supervision_member.statut == ChoixEtatSignature.APPROVED.name:
            attachments.append(
                Attachment(
                    identifier='APPROBATION_PDF',
                    label=DocumentsSupervision['APPROBATION_PDF'],
                    sub_identifier=supervision_member.promoteur.uuid,
                    sub_identifier_label=f'{supervision_member.promoteur.prenom} {supervision_member.promoteur.nom}',
                    uuids=supervision_member.pdf,
                    candidate_language=context.identification.langue_contact,
                )
            )
    for supervision_member in context.groupe_supervision.signatures_membres_CA:
        if supervision_member.pdf and supervision_member.statut == ChoixEtatSignature.APPROVED.name:
            attachments.append(
                Attachment(
                    identifier='APPROBATION_PDF',
                    label=DocumentsSupervision['APPROBATION_PDF'],
                    sub_identifier=supervision_member.membre_CA.uuid,
                    sub_identifier_label=f'{supervision_member.membre_CA.prenom} {supervision_member.membre_CA.nom}',
                    uuids=supervision_member.pdf,
                    candidate_language=context.identification.langue_contact,
                )
            )
    return attachments


def get_dynamic_questions_attachments(
    specific_questions: List[QuestionSpecifiqueDTO],
    with_base_identifier=True,
):
    """Returns the dynamic questions attachments."""
    prefix = f'{IdentifiantBaseEmplacementDocument.QUESTION_SPECIFIQUE.name}.' if with_base_identifier else ''
    return [
        Attachment(
            identifier=f'{prefix}{question.uuid}',
            label=question.label,
            uuids=question.valeur or [],
            required=question.requis,
            candidate_language_label=question.label_langue_candidat,
        )
        for question in specific_questions
        if question.type == TypeItemFormulaire.DOCUMENT.name
    ]


def get_training_choice_attachments(specific_questions: List[QuestionSpecifiqueDTO]) -> List[Attachment]:
    """Returns the training choice attachments."""
    return get_dynamic_questions_attachments(specific_questions)


def get_requestable_free_documents(specific_questions: List[QuestionSpecifiqueDTO]) -> List[Attachment]:
    """Returns the requestable free attachments."""
    return get_dynamic_questions_attachments(
        specific_questions,
        with_base_identifier=False,
    )


def get_authorization_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the authorization attachments."""

    attachments = []

    if context.est_proposition_generale and context.proposition.type == TypeDemande.ADMISSION.name:
        if (
            context.proposition.statut == ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name
            or context.proposition.certificat_autorisation_signe
        ):
            attachments.append(
                Attachment(
                    identifier='AUTORISATION_PDF_SIGNEE',
                    label=DocumentsSuiteAutorisation['AUTORISATION_PDF_SIGNEE'],
                    uuids=context.proposition.certificat_autorisation_signe,
                    required=False,
                    candidate_language=context.identification.langue_contact,
                )
            )

        if (
            context.proposition.statut == ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name
            and context.proposition.doit_fournir_visa_etudes
        ) or context.proposition.visa_etudes_d:
            attachments.append(
                Attachment(
                    identifier='VISA_ETUDES',
                    label=DocumentsSuiteAutorisation['VISA_ETUDES'],
                    uuids=context.proposition.visa_etudes_d,
                    required=False,
                    candidate_language=context.identification.langue_contact,
                )
            )

    return attachments
