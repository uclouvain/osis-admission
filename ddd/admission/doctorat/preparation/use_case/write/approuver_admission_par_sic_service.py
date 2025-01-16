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
from admission.ddd.admission.doctorat.events import AdmissionDoctoraleApprouveeParSicEvent
from admission.ddd.admission.doctorat.preparation.commands import (
    ApprouverAdmissionParSicCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.doctorat.preparation.domain.service.emplacement_document import EmplacementDocumentService
from admission.ddd.admission.doctorat.preparation.domain.service.i_comptabilite import IComptabiliteTranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_historique import IHistorique
from admission.ddd.admission.doctorat.preparation.domain.service.i_membre_CA import IMembreCATranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_notification import INotification
from admission.ddd.admission.doctorat.preparation.domain.service.i_pdf_generation import IPDFGeneration
from admission.ddd.admission.doctorat.preparation.domain.service.i_promoteur import IPromoteurTranslator
from admission.ddd.admission.doctorat.preparation.domain.service.i_question_specifique import (
    IQuestionSpecifiqueTranslator,
)
from admission.ddd.admission.doctorat.preparation.repository.i_groupe_de_supervision import (
    IGroupeDeSupervisionRepository,
)
from admission.ddd.admission.doctorat.preparation.repository.i_proposition import IPropositionRepository
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.domain.service.i_emplacements_documents_proposition import (
    IEmplacementsDocumentsPropositionTranslator,
)
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.service.resume_proposition import ResumeProposition
from admission.ddd.admission.repository.i_digit import IDigitRepository
from admission.ddd.admission.repository.i_emplacement_document import IEmplacementDocumentRepository
from ddd.logic.shared_kernel.academic_year.repository.i_academic_year import IAcademicYearRepository
from ddd.logic.shared_kernel.personne_connue_ucl.domain.service.personne_connue_ucl import IPersonneConnueUclTranslator
from ddd.logic.shared_kernel.profil.domain.service.parcours_interne import IExperienceParcoursInterneTranslator


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
    experience_parcours_interne_translator: 'IExperienceParcoursInterneTranslator',
    digit_repository: 'IDigitRepository',
    groupe_supervision_repository: 'IGroupeDeSupervisionRepository',
    promoteur_translator: 'IPromoteurTranslator',
    membre_ca_translator: 'IMembreCATranslator',
) -> PropositionIdentity:
    # GIVEN
    proposition = proposition_repository.get(entity_id=PropositionIdentity(uuid=cmd.uuid_proposition))

    resume_dto = ResumeProposition.get_resume_demande_doctorat(
        uuid_proposition=cmd.uuid_proposition,
        proposition_repository=proposition_repository,
        comptabilite_translator=comptabilite_translator,
        profil_candidat_translator=profil_candidat_translator,
        academic_year_repository=academic_year_repository,
        groupe_supervision_repository=groupe_supervision_repository,
        promoteur_translator=promoteur_translator,
        membre_ca_translator=membre_ca_translator,
        question_specifique_translator=question_specifique_translator,
    )
    documents_dto = emplacements_documents_demande_translator.recuperer_emplacements_dto(
        personne_connue_translator=personne_connue_translator,
        resume_dto=resume_dto,
        questions_specifiques=resume_dto.questions_specifiques_dtos,
        avec_documents_libres=False,
    )

    # WHEN
    proposition.approuver_par_sic(
        auteur_modification=cmd.auteur,
        documents_dto=documents_dto,
        curriculum_dto=resume_dto.curriculum,
        academic_year_repository=academic_year_repository,
        profil_candidat_translator=profil_candidat_translator,
        experience_parcours_interne_translator=experience_parcours_interne_translator,
    )

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
        AdmissionDoctoraleApprouveeParSicEvent(
            entity_id=proposition.entity_id,
            type_admission=proposition.type_admission.name,
            matricule=proposition.matricule_candidat,
            nom=resume_dto.identification.nom,
            prenom=resume_dto.identification.prenom,
            autres_prenoms=resume_dto.identification.autres_prenoms,
            date_naissance=str(resume_dto.identification.date_naissance),
            genre=resume_dto.identification.genre,
            niss=resume_dto.identification.numero_registre_national_belge,
            annee=proposition.annee_calculee,
        )
    )
    return proposition.entity_id
