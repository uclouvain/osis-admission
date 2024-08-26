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

from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.enums import TypeItemFormulaire
from admission.ddd.admission.enums.valorisation_experience import ExperiencesCVRecuperees
from admission.ddd.admission.formation_generale.commands import (
    ApprouverAdmissionParSicCommand,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.service.emplacement_document import EmplacementDocumentService
from admission.ddd.admission.formation_generale.domain.service.i_historique import IHistorique
from admission.ddd.admission.formation_generale.domain.service.i_pdf_generation import IPDFGeneration
from admission.ddd.admission.formation_generale.events import AdmissionApprouveeParSicEvent
from admission.ddd.admission.formation_generale.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository


def approuver_admission_par_sic(
    message_bus,
    cmd: ApprouverAdmissionParSicCommand,
    proposition_repository: 'IPropositionRepository',
    profil_candidat_translator: 'IProfilCandidatTranslator',
    historique: 'IHistorique',
    notification: 'INotification',
    pdf_generation: 'IPDFGeneration',
    emplacement_document_repository: 'IEmplacementDocumentRepository',
    comptabilite_translator: 'IComptabiliteTranslator',
    question_specifique_translator: 'IQuestionSpecifiqueTranslator',
    emplacements_documents_demande_translator: 'IEmplacementsDocumentsPropositionTranslator',
    academic_year_repository: 'IAcademicYearRepository',
    personne_connue_translator: 'IPersonneConnueUclTranslator',
    digit_repository: 'IDigitRepository',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    proposition_dto = proposition_repository.get_dto(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))
    identification = profil_candidat_translator.get_identification(proposition.matricule_candidat)
    comptabilite_dto = comptabilite_translator.get_comptabilite_dto(proposition_uuid=cmd.uuid_proposition)
    resume_dto = ResumeProposition.get_resume(
        profil_candidat_translator=profil_candidat_translator,
        academic_year_repository=academic_year_repository,
        proposition_dto=proposition_dto,
        comptabilite_dto=comptabilite_dto,
        experiences_cv_recuperees=ExperiencesCVRecuperees.SEULEMENT_VALORISEES_PAR_ADMISSION,
    )
    questions_specifiques_dtos = question_specifique_translator.search_dto_by_proposition(
        proposition_uuid=cmd.uuid_proposition,
        type=TypeItemFormulaire.DOCUMENT.name,
    )
    documents_dto = emplacements_documents_demande_translator.recuperer_emplacements_dto(
        personne_connue_translator=personne_connue_translator,
        resume_dto=resume_dto,
        questions_specifiques=questions_specifiques_dtos,
        avec_documents_libres=False,
    )

    # WHEN
    proposition.approuver_par_sic(auteur_modification=cmd.auteur, documents_dto=documents_dto)

    # THEN
    pdf_generation.generer_attestation_accord_sic(
        proposition_repository=proposition_repository,
        profil_candidat_translator=profil_candidat_translator,
        proposition=proposition,
        gestionnaire=cmd.auteur,
    )
    pdf_generation.generer_attestation_accord_annexe_sic(
        proposition_repository=proposition_repository,
        profil_candidat_translator=profil_candidat_translator,
        proposition=proposition,
        gestionnaire=cmd.auteur,
    )

    proposition_repository.save(entity=proposition)

    EmplacementDocumentService.initier_emplacements_documents_approbation_sic(
        proposition=proposition,
        emplacement_document_repository=emplacement_document_repository,
        auteur=cmd.auteur,
    )
    message = notification.accepter_proposition_par_sic(
        proposition_uuid=proposition.entity_id.uuid,
        objet_message=cmd.objet_message,
        corps_message=cmd.corps_message,
        digit_repository=digit_repository,
    )
    historique.historiser_acceptation_sic(
        proposition=proposition,
        message=message,
        gestionnaire=cmd.auteur,
    )

    message_bus.publish(
        AdmissionApprouveeParSicEvent(
            entity_id=proposition.entity_id,
            matricule=proposition.matricule_candidat,
            nom=identification.nom,
            prenom=identification.prenom,
            autres_prenoms=identification.autres_prenoms,
            date_naissance=str(identification.date_naissance),
            genre=identification.genre,
            niss=identification.numero_registre_national_belge,
            annee=proposition.annee_calculee,
        )
    )
    return proposition.entity_id
