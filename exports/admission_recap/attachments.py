# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.utils.translation import gettext as _, ngettext

from admission.contrib.models import AdmissionFormItemInstantiation
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeFinancement,
    ChoixEtatSignature,
)

from admission.constants import IMAGE_MIME_TYPES, DEFAULT_MIME_TYPES
from admission.ddd.admission.doctorat.preparation.dtos import ExperienceAcademiqueDTO
from admission.ddd.admission.doctorat.preparation.dtos.comptabilite import (
    DerniersEtablissementsSuperieursCommunauteFrancaiseFrequentes,
)
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceNonAcademiqueDTO
from admission.ddd.admission.domain.validator._should_comptabilite_etre_completee import recuperer_champs_requis_dto
from admission.ddd.admission.dtos.question_specifique import QuestionSpecifiqueDTO
from admission.ddd.admission.dtos.resume import ResumePropositionDTO
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.exports.admission_recap.constants import CURRICULUM_ACTIVITY_LABEL, ACCOUNTING_LABEL
from admission.utils import format_academic_year
from admission.ddd.admission.enums.document import (
    DocumentsIdentification,
    DocumentsEtudesSecondaires,
    DocumentsConnaissancesLangues,
    DocumentsCurriculum,
    DocumentsQuestionsSpecifiques,
    DocumentsComptabilite,
    DocumentsProjetRecherche,
    DocumentsCotutelle,
    DocumentsSupervision,
    DocumentsInterOnglets,
)
from admission.exports.admission_recap.constants import CURRICULUM_ACTIVITY_LABEL
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from osis_document.api.utils import get_raw_content_remotely
from osis_profile.models.enums.curriculum import TranscriptType, ActivityType
from osis_profile.models.enums.education import ForeignDiplomaTypes, Equivalence


class Attachment:
    def __init__(
        self,
        identifier,
        uuids: List[str],
        label='',
        sub_identifier='',
        sub_identifier_label='',
        required=False,
    ):
        self.identifier = f'{identifier.name}.{sub_identifier}' if sub_identifier else identifier.name
        self.label = (
            label
            if label
            else (f'{identifier.value} - {sub_identifier_label}' if sub_identifier_label else identifier.value)
        )
        self.uuids = [str(uuid) for uuid in uuids]
        self.required = required

    def get_raw(self, token: Optional[str], metadata: Optional[Dict], default_content: BytesIO) -> BytesIO:
        """
        Returns the raw content of an attachment if a token is specified and the mimetype is supported else a default
        content.
        """
        if token and metadata and metadata.get('mimetype') in DEFAULT_MIME_TYPES:
            raw_content = get_raw_content_remotely(token)
            if not raw_content:
                return default_content
            if metadata.get('mimetype') in IMAGE_MIME_TYPES:
                raw_content = img2pdf.convert(raw_content)
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
            identifier=DocumentsIdentification.PHOTO_IDENTITE,
            uuids=context.identification.photo_identite,
            required=True,
        )
    ]
    if context.identification.numero_carte_identite or context.identification.numero_registre_national_belge:
        attachments.append(
            Attachment(
                identifier=DocumentsIdentification.CARTE_IDENTITE,
                uuids=context.identification.carte_identite,
                required=True,
            )
        )
    if context.identification.numero_passeport:
        attachments.append(
            Attachment(
                identifier=DocumentsIdentification.PASSEPORT,
                uuids=context.identification.passeport,
                required=True,
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
            attachments.append(
                Attachment(
                    identifier=DocumentsEtudesSecondaires.DIPLOME_BELGE_DIPLOME,
                    uuids=context.etudes_secondaires.diplome_belge.diplome,
                    required=got_diploma == GotDiploma.YES.name
                    or bool(
                        # Required if it is specified but not the alternative field
                        got_diploma == GotDiploma.THIS_YEAR.name
                        and context.etudes_secondaires.diplome_belge.diplome
                        and not context.etudes_secondaires.diplome_belge.certificat_inscription
                    ),
                )
            )
            if context.etudes_secondaires.diplome_etudes_secondaires == GotDiploma.THIS_YEAR.name:
                attachments.append(
                    Attachment(
                        identifier=DocumentsEtudesSecondaires.DIPLOME_BELGE_CERTIFICAT_INSCRIPTION,
                        uuids=context.etudes_secondaires.diplome_belge.certificat_inscription,
                        required=bool(
                            # Required if it is specified but not the alternative field
                            context.etudes_secondaires.diplome_belge.certificat_inscription
                            and not context.etudes_secondaires.diplome_belge.diplome
                        ),
                    )
                )
        elif context.etudes_secondaires.diplome_etranger:
            if context.etudes_secondaires.diplome_etranger.type_diplome == ForeignDiplomaTypes.NATIONAL_BACHELOR.name:
                if ue_or_assimilated:
                    if context.etudes_secondaires.diplome_etranger.equivalence == Equivalence.YES.name:
                        attachments.append(
                            Attachment(
                                identifier=DocumentsEtudesSecondaires.DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE,
                                uuids=context.etudes_secondaires.diplome_etranger.decision_final_equivalence_ue,
                                required=True,
                            )
                        )
                    elif context.etudes_secondaires.diplome_etranger.equivalence == Equivalence.PENDING.name:
                        attachments.append(
                            Attachment(
                                identifier=DocumentsEtudesSecondaires.DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE,
                                uuids=context.etudes_secondaires.diplome_etranger.preuve_decision_equivalence,
                                required=True,
                            )
                        )
                else:
                    attachments.append(
                        Attachment(
                            identifier=DocumentsEtudesSecondaires.DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE,
                            uuids=context.etudes_secondaires.diplome_etranger.decision_final_equivalence_hors_ue,
                            required=True,
                        )
                    )

            attachments.append(
                Attachment(
                    identifier=DocumentsEtudesSecondaires.DIPLOME_ETRANGER_DIPLOME,
                    uuids=context.etudes_secondaires.diplome_etranger.diplome,
                    required=not ue_or_assimilated
                    or (got_diploma == GotDiploma.YES.name)
                    or bool(
                        got_diploma == GotDiploma.THIS_YEAR.name
                        and context.etudes_secondaires.diplome_etranger.diplome
                        and not context.etudes_secondaires.diplome_etranger.certificat_inscription
                    ),
                ),
            )

            if need_translations:
                attachments.append(
                    Attachment(
                        identifier=DocumentsEtudesSecondaires.DIPLOME_ETRANGER_TRADUCTION_DIPLOME,
                        uuids=context.etudes_secondaires.diplome_etranger.traduction_diplome,
                        required=not ue_or_assimilated
                        or (got_diploma == GotDiploma.YES.name)
                        or bool(
                            got_diploma == GotDiploma.THIS_YEAR.name
                            and context.etudes_secondaires.diplome_etranger.diplome
                        ),
                    )
                )

            if context.etudes_secondaires.diplome_etudes_secondaires == GotDiploma.THIS_YEAR.name and ue_or_assimilated:
                attachments.append(
                    Attachment(
                        identifier=DocumentsEtudesSecondaires.DIPLOME_ETRANGER_CERTIFICAT_INSCRIPTION,
                        uuids=context.etudes_secondaires.diplome_etranger.certificat_inscription,
                        required=bool(
                            context.etudes_secondaires.diplome_etranger.certificat_inscription
                            and not context.etudes_secondaires.diplome_etranger.diplome
                        ),
                    )
                )
                if need_translations:
                    attachments.append(
                        Attachment(
                            identifier=DocumentsEtudesSecondaires.DIPLOME_ETRANGER_TRADUCTION_CERTIFICAT_INSCRIPTION,
                            uuids=context.etudes_secondaires.diplome_etranger.traduction_certificat_inscription,
                            required=bool(context.etudes_secondaires.diplome_etranger.certificat_inscription),
                        )
                    )

            attachments.append(
                Attachment(
                    identifier=DocumentsEtudesSecondaires.DIPLOME_ETRANGER_RELEVE_NOTES,
                    uuids=context.etudes_secondaires.diplome_etranger.releve_notes,
                    required=True,
                )
            )
            if need_translations:
                attachments.append(
                    Attachment(
                        identifier=DocumentsEtudesSecondaires.DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES,
                        uuids=context.etudes_secondaires.diplome_etranger.traduction_releve_notes,
                        required=True,
                    )
                )

        elif context.etudes_secondaires.alternative_secondaires:
            attachments.append(
                Attachment(
                    identifier=DocumentsEtudesSecondaires.ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE,
                    uuids=context.etudes_secondaires.alternative_secondaires.examen_admission_premier_cycle,
                    required=not context.curriculum.candidat_est_potentiel_vae,
                )
            )

    attachments.extend(get_dynamic_questions_attachments(specific_questions))

    return attachments


def get_languages_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the languages attachments."""
    return [
        Attachment(
            identifier=DocumentsConnaissancesLangues.CERTIFICAT_CONNAISSANCE_LANGUE,
            sub_identifier=language.langue,
            sub_identifier_label=language.nom_langue,
            uuids=language.certificat,
            required=False,
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
                identifier=DocumentsCurriculum.DIPLOME_EQUIVALENCE,
                uuids=context.proposition.equivalence_diplome,
                required=require_equivalence,
            )
        )

    if display_curriculum:
        attachments.append(
            Attachment(
                identifier=DocumentsCurriculum.CURRICULUM,
                uuids=context.proposition.curriculum,
                required=require_curriculum,
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
                    identifier=DocumentsCurriculum.RELEVE_NOTES,
                    uuids=experience.releve_notes,
                    required=True,
                )
            )
            if translation_required:
                attachments.append(
                    Attachment(
                        identifier=DocumentsCurriculum.TRADUCTION_RELEVE_NOTES,
                        uuids=experience.traduction_releve_notes,
                        required=True,
                    )
                )
        elif experience.type_releve_notes == TranscriptType.ONE_A_YEAR.name:
            for annee in experience.annees:
                sub_identifier = str(annee.annee)
                attachments.append(
                    Attachment(
                        identifier=DocumentsCurriculum.RELEVE_NOTES_ANNUEL,
                        sub_identifier=sub_identifier,
                        sub_identifier_label=sub_identifier,
                        uuids=annee.releve_notes,
                        required=True,
                    )
                )
                if translation_required:
                    attachments.append(
                        Attachment(
                            identifier=DocumentsCurriculum.TRADUCTION_RELEVE_NOTES_ANNUEL,
                            sub_identifier=sub_identifier,
                            sub_identifier_label=sub_identifier,
                            uuids=annee.traduction_releve_notes,
                            required=True,
                        )
                    )

    if experience.a_obtenu_diplome:
        if context.est_proposition_doctorale:
            attachments.append(
                Attachment(
                    identifier=DocumentsCurriculum.RESUME_MEMOIRE,
                    uuids=experience.resume_memoire,
                    required=True,
                )
            )

        attachments.append(
            Attachment(
                identifier=DocumentsCurriculum.DIPLOME,
                uuids=experience.diplome,
                required=True,
            )
        )

        if translation_required:
            attachments.append(
                Attachment(
                    identifier=DocumentsCurriculum.TRADUCTION_DIPLOME,
                    uuids=experience.traduction_diplome,
                    required=True,
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
        if experience.type != ActivityType.OTHER.name:
            attachments.append(
                Attachment(
                    identifier=DocumentsCurriculum.CERTIFICAT_EXPERIENCE,
                    label=CURRICULUM_ACTIVITY_LABEL[experience.type],
                    uuids=experience.certificat,
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
                identifier=DocumentsQuestionsSpecifiques.COPIE_TITRE_SEJOUR,
                uuids=context.proposition.copie_titre_sejour,
            )
        )

    if eligible_for_reorientation and context.proposition.est_reorientation_inscription_externe:
        attachments.append(
            Attachment(
                identifier=DocumentsQuestionsSpecifiques.ATTESTATION_INSCRIPTION_REGULIERE,
                uuids=context.proposition.attestation_inscription_reguliere,
                required=True,
            )
        )
    if eligible_for_modification and context.proposition.est_modification_inscription_externe:
        attachments.append(
            Attachment(
                identifier=DocumentsQuestionsSpecifiques.FORMULAIRE_MODIFICATION_INSCRIPTION,
                uuids=context.proposition.formulaire_modification_inscription,
                required=True,
            )
        )
    attachments.extend(get_dynamic_questions_attachments(specific_questions))
    return attachments


def get_accounting_attachments(
    context: ResumePropositionDTO,
    last_fr_institutes: DerniersEtablissementsSuperieursCommunauteFrancaiseFrequentes,
    with_assimilation: bool,
    formatted_relationship: str,
) -> List[Attachment]:
    """Returns the accounting attachments."""
    attachments = []

    if last_fr_institutes:
        identifier = DocumentsComptabilite.ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT
        attachments.append(
            Attachment(
                identifier=identifier,
                label=ngettext(
                    'Certificate stating the absence of debts towards the institution attended '
                    'during the academic year %(academic_year)s: %(names)s',
                    'Certificates stating the absence of debts towards the institutions attended '
                    'during the academic year %(academic_year)s: %(names)s',
                    len(last_fr_institutes.noms),
                )
                % {
                    'academic_year': format_academic_year(last_fr_institutes.annee),
                    'names': ', '.join(last_fr_institutes.noms),
                },
                uuids=context.comptabilite.attestation_absence_dette_etablissement,
                required=True,
            )
        )

    if getattr(context.comptabilite, 'enfant_personnel', None):
        attachments.append(
            Attachment(
                identifier=DocumentsComptabilite.ATTESTATION_ENFANT_PERSONNEL,
                uuids=context.comptabilite.attestation_enfant_personnel,
            )
        )

    if with_assimilation:
        fields = recuperer_champs_requis_dto(
            nom_champ='type_situation_assimilation',
            comptabilite=context.comptabilite,
        )
        for field in fields:
            field_id = field.upper()
            if hasattr(DocumentsComptabilite, field_id):
                identifier = DocumentsComptabilite[field_id]
                attachments.append(
                    Attachment(
                        identifier=identifier,
                        label=identifier.value % {'person_concerned': formatted_relationship},
                        uuids=getattr(context.comptabilite, field),
                        required=True,
                    )
                )

    return attachments


def get_research_project_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the research project attachments."""
    attachments = []
    if context.proposition.type_financement == ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name:
        attachments.append(
            Attachment(
                identifier=DocumentsProjetRecherche.PREUVE_BOURSE,
                uuids=context.proposition.bourse_preuve,
            )
        )

    attachments += [
        Attachment(
            identifier=DocumentsProjetRecherche.DOCUMENTS_PROJET,
            uuids=context.proposition.documents_projet,
            required=True,
        ),
        Attachment(
            identifier=DocumentsProjetRecherche.PROPOSITION_PROGRAMME_DOCTORAL,
            uuids=context.proposition.proposition_programme_doctoral,
            required=True,
        ),
        Attachment(
            identifier=DocumentsProjetRecherche.PROJET_FORMATION_COMPLEMENTAIRE,
            uuids=context.proposition.projet_formation_complementaire,
        ),
        Attachment(
            identifier=DocumentsProjetRecherche.GRAPHE_GANTT,
            uuids=context.proposition.graphe_gantt,
        ),
        Attachment(
            identifier=DocumentsProjetRecherche.LETTRES_RECOMMANDATION,
            uuids=context.proposition.lettres_recommandation,
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
                identifier=DocumentsCotutelle.DEMANDE_OUVERTURE,
                uuids=context.groupe_supervision.cotutelle.demande_ouverture,
                required=True,
            ),
            Attachment(
                identifier=DocumentsCotutelle.CONVENTION,
                uuids=context.groupe_supervision.cotutelle.convention,
            ),
            Attachment(
                identifier=DocumentsCotutelle.AUTRES_DOCUMENTS,
                uuids=context.groupe_supervision.cotutelle.autres_documents,
            ),
        ]
    return attachments


def get_supervision_group_attachments(context: ResumePropositionDTO) -> List[Attachment]:
    """Returns the supervision group attachments."""
    attachments = []
    base_identifier = DocumentsSupervision.APPROBATION_PDF
    for supervision_member in context.groupe_supervision.signatures_promoteurs:
        if supervision_member.pdf and supervision_member.statut == ChoixEtatSignature.APPROVED.name:
            attachments.append(
                Attachment(
                    identifier=base_identifier,
                    sub_identifier=supervision_member.promoteur.uuid,
                    sub_identifier_label=f'{supervision_member.promoteur.prenom} {supervision_member.promoteur.nom}',
                    uuids=supervision_member.pdf,
                )
            )
    for supervision_member in context.groupe_supervision.signatures_membres_CA:
        if supervision_member.pdf and supervision_member.statut == ChoixEtatSignature.APPROVED.name:
            attachments.append(
                Attachment(
                    identifier=base_identifier,
                    sub_identifier=supervision_member.membre_CA.uuid,
                    sub_identifier_label=f'{supervision_member.membre_CA.prenom} {supervision_member.membre_CA.nom}',
                    uuids=supervision_member.pdf,
                )
            )
    return attachments


def get_dynamic_questions_attachments(specific_questions: List[QuestionSpecifiqueDTO]):
    """Returns the dynamic questions attachments."""
    return [
        Attachment(
            identifier=DocumentsInterOnglets.QUESTION_SPECIFIQUE,
            sub_identifier=question.uuid,
            label=question.label,
            uuids=question.valeur or [],
            required=question.requis,
        )
        for question in specific_questions
        if question.type == TypeItemFormulaire.DOCUMENT.name
    ]


def get_training_choice_attachments(specific_questions: List[QuestionSpecifiqueDTO]) -> List[Attachment]:
    """Returns the training choice attachments."""
    return get_dynamic_questions_attachments(specific_questions)
