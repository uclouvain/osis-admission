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

from admission.ddd.admission.doctorat.preparation.commands import *
from admission.ddd.admission.doctorat.preparation.domain.model.enums import OngletsChecklist
from admission.ddd.admission.doctorat.preparation.use_case.read import *
from admission.ddd.admission.doctorat.preparation.use_case.write import *
from admission.ddd.admission.use_case.read import recuperer_questions_specifiques_proposition
from admission.ddd.admission.use_case.write import (
    initialiser_emplacement_document_libre_non_reclamable,
    initialiser_emplacement_document_libre_a_reclamer,
    annuler_reclamation_emplacement_document,
    modifier_reclamation_emplacement_document,
    supprimer_emplacement_document,
    remplacer_emplacement_document,
    remplir_emplacement_document_par_gestionnaire,
    initialiser_emplacement_document_a_reclamer,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator
from .domain.service.comptabilite import ComptabiliteTranslator
from .domain.service.doctorat import DoctoratTranslator
from .domain.service.historique import Historique
from .domain.service.membre_CA import MembreCATranslator
from .domain.service.notification import Notification
from .domain.service.promoteur import PromoteurTranslator
from .domain.service.question_specifique import QuestionSpecifiqueTranslator
from .repository.emplacement_document import EmplacementDocumentRepository
from .repository.groupe_de_supervision import GroupeDeSupervisionRepository
from .repository.proposition import PropositionRepository
from ..validation.repository.demande import DemandeRepository
from ...domain.service.calendrier_inscription import CalendrierInscription
from ...domain.service.elements_confirmation import ElementsConfirmation
from ...domain.service.emplacements_documents_proposition import EmplacementsDocumentsPropositionTranslator
from ...domain.service.historique import Historique as HistoriqueGlobal
from ...domain.service.maximum_propositions import MaximumPropositionsAutorisees
from ...domain.service.titres_acces import TitresAcces

COMMAND_HANDLERS = {
    InitierPropositionCommand: lambda msg_bus, cmd: initier_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        doctorat_translator=DoctoratTranslator(),
        historique=Historique(),
        maximum_propositions_service=MaximumPropositionsAutorisees(),
    ),
    CompleterPropositionCommand: lambda msg_bus, cmd: completer_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        doctorat_translator=DoctoratTranslator(),
        historique=Historique(),
    ),
    RechercherDoctoratQuery: lambda msg_bus, cmd: rechercher_doctorats(
        cmd,
        doctorat_translator=DoctoratTranslator(),
        annee_inscription_formation_translator=AnneeInscriptionFormationTranslator(),
    ),
    IdentifierPromoteurCommand: lambda msg_bus, cmd: identifier_promoteur(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        historique=Historique(),
    ),
    IdentifierMembreCACommand: lambda msg_bus, cmd: identifier_membre_ca(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        membre_ca_translator=MembreCATranslator(),
        historique=Historique(),
    ),
    ModifierMembreSupervisionExterneCommand: lambda msg_bus, cmd: modifier_membre_supervision_externe(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        membre_ca_translator=MembreCATranslator(),
    ),
    DemanderSignaturesCommand: lambda msg_bus, cmd: demander_signatures(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        historique=Historique(),
        notification=Notification(),
    ),
    RenvoyerInvitationSignatureExterneCommand: lambda msg_bus, cmd: renvoyer_invitation_signature_externe(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        notification=Notification(),
    ),
    VerifierPropositionQuery: lambda msg_bus, cmd: verifier_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        academic_year_repository=AcademicYearRepository(),
        titres_acces=TitresAcces(),
        questions_specifiques_translator=QuestionSpecifiqueTranslator(),
        formation_translator=DoctoratTranslator(),
        calendrier_inscription=CalendrierInscription(),
        maximum_propositions_service=MaximumPropositionsAutorisees(),
    ),
    VerifierProjetQuery: lambda msg_bus, cmd: verifier_projet(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        questions_specifiques_translator=QuestionSpecifiqueTranslator(),
    ),
    SupprimerPromoteurCommand: lambda msg_bus, cmd: supprimer_promoteur(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    DesignerPromoteurReferenceCommand: lambda msg_bus, cmd: designer_promoteur_reference(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
    ),
    SupprimerMembreCACommand: lambda msg_bus, cmd: supprimer_membre_CA(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    ApprouverPropositionCommand: lambda msg_bus, cmd: approuver_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    RefuserPropositionCommand: lambda msg_bus, cmd: refuser_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    SoumettrePropositionCommand: lambda msg_bus, cmd: soumettre_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        demande_repository=DemandeRepository(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        academic_year_repository=AcademicYearRepository(),
        historique=Historique(),
        notification=Notification(),
        titres_acces=TitresAcces(),
        questions_specifiques_translator=QuestionSpecifiqueTranslator(),
        doctorat_translator=DoctoratTranslator(),
        calendrier_inscription=CalendrierInscription(),
        element_confirmation=ElementsConfirmation(),
        maximum_propositions_service=MaximumPropositionsAutorisees(),
    ),
    DefinirCotutelleCommand: lambda msg_bus, cmd: definir_cotutelle(
        cmd,
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        proposition_repository=PropositionRepository(),
        historique=Historique(),
    ),
    ListerPropositionsCandidatQuery: lambda msg_bus, cmd: lister_propositions_candidat(
        cmd,
        proposition_repository=PropositionRepository(),
    ),
    ListerPropositionsSuperviseesQuery: lambda msg_bus, cmd: lister_propositions_supervisees(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
    ),
    GetPropositionCommand: lambda msg_bus, cmd: recuperer_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
    ),
    GetGroupeDeSupervisionCommand: lambda msg_bus, cmd: recuperer_groupe_de_supervision(
        cmd,
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        membre_ca_translator=MembreCATranslator(),
    ),
    GetCotutelleCommand: lambda msg_bus, cmd: recuperer_cotutelle(
        cmd,
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
    ),
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        historique=Historique(),
    ),
    ApprouverPropositionParPdfCommand: lambda msg_bus, cmd: approuver_proposition_par_pdf(
        cmd,
        proposition_repository=PropositionRepository(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        historique=Historique(),
    ),
    CompleterComptabilitePropositionCommand: lambda msg_bus, cmd: completer_comptabilite_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
    ),
    GetComptabiliteQuery: lambda msg_bus, cmd: recuperer_comptabilite(
        cmd,
        comptabilite_translator=ComptabiliteTranslator(),
    ),
    ModifierTypeAdmissionCommand: lambda msg_bus, cmd: modifier_type_admission(
        cmd,
        proposition_repository=PropositionRepository(),
        doctorat_translator=DoctoratTranslator(),
    ),
    CompleterCurriculumCommand: lambda msg_bus, cmd: completer_curriculum(
        cmd,
        proposition_repository=PropositionRepository(),
    ),
    VerifierCurriculumQuery: lambda msg_bus, cmd: verifier_curriculum(
        cmd,
        proposition_repository=PropositionRepository(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        academic_year_repository=AcademicYearRepository(),
    ),
    DeterminerAnneeAcademiqueEtPotQuery: lambda msg_bus, cmd: determiner_annee_academique_et_pot(
        cmd,
        proposition_repository=PropositionRepository(),
        titres_acces=TitresAcces(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        calendrier_inscription=CalendrierInscription(),
    ),
    RecupererElementsConfirmationQuery: lambda msg_bus, cmd: recuperer_elements_confirmation(
        cmd,
        proposition_repository=PropositionRepository(),
        element_confirmation=ElementsConfirmation(),
        formation_translator=DoctoratTranslator(),
        profil_candidat_translator=ProfilCandidatTranslator(),
    ),
    RecupererResumePropositionQuery: lambda msg_bus, cmd: recuperer_resume_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        i_profil_candidat_translator=ProfilCandidatTranslator(),
        i_comptabilite_translator=ComptabiliteTranslator(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        membre_ca_translator=MembreCATranslator(),
        academic_year_repository=AcademicYearRepository(),
    ),
    RecupererQuestionsSpecifiquesQuery: lambda msg_bus, cmd: recuperer_questions_specifiques_proposition(
        cmd,
        question_specifique_translator=QuestionSpecifiqueTranslator(),
    ),
    RecupererDocumentsPropositionQuery: lambda msg_bus, cmd: recuperer_documents_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        comptabilite_translator=ComptabiliteTranslator(),
        question_specifique_translator=QuestionSpecifiqueTranslator(),
        emplacements_documents_demande_translator=EmplacementsDocumentsPropositionTranslator(),
        academic_year_repository=AcademicYearRepository(),
        personne_connue_translator=PersonneConnueUclTranslator(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        membre_ca_translator=MembreCATranslator(),
    ),
    RecupererDocumentsReclamesPropositionQuery: lambda msg_bus, cmd: recuperer_documents_reclames_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        comptabilite_translator=ComptabiliteTranslator(),
        question_specifique_translator=QuestionSpecifiqueTranslator(),
        emplacements_documents_demande_translator=EmplacementsDocumentsPropositionTranslator(),
        academic_year_repository=AcademicYearRepository(),
        personne_connue_translator=PersonneConnueUclTranslator(),
        groupe_supervision_repository=GroupeDeSupervisionRepository(),
        promoteur_translator=PromoteurTranslator(),
        membre_ca_translator=MembreCATranslator(),
    ),
    AnnulerReclamationDocumentsAuCandidatCommand: (
        lambda msg_bus, cmd: annuler_reclamation_documents_au_candidat(
            cmd,
            proposition_repository=PropositionRepository(),
            emplacement_document_repository=EmplacementDocumentRepository(),
            historique=HistoriqueGlobal(),
            profil_candidat_translator=ProfilCandidatTranslator(),
            question_specifique_translator=QuestionSpecifiqueTranslator(),
            academic_year_repository=AcademicYearRepository(),
            personne_connue_translator=PersonneConnueUclTranslator(),
            emplacements_documents_demande_translator=EmplacementsDocumentsPropositionTranslator(),
            comptabilite_translator=ComptabiliteTranslator(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            promoteur_translator=PromoteurTranslator(),
            membre_ca_translator=MembreCATranslator(),
        )
    ),
    CompleterEmplacementsDocumentsParCandidatCommand: lambda msg_bus, cmd: (
        completer_emplacements_documents_par_candidat(
            cmd,
            proposition_repository=PropositionRepository(),
            emplacement_document_repository=EmplacementDocumentRepository(),
            historique=HistoriqueGlobal(),
            profil_candidat_translator=ProfilCandidatTranslator(),
            question_specifique_translator=QuestionSpecifiqueTranslator(),
            academic_year_repository=AcademicYearRepository(),
            personne_connue_translator=PersonneConnueUclTranslator(),
            emplacements_documents_demande_translator=EmplacementsDocumentsPropositionTranslator(),
            notification=Notification(),
            comptabilite_translator=ComptabiliteTranslator(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            promoteur_translator=PromoteurTranslator(),
            membre_ca_translator=MembreCATranslator(),
        )
    ),
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand: (
        lambda msg_bus, cmd: recalculer_emplacements_documents_non_libres_proposition(
            cmd,
            proposition_repository=PropositionRepository(),
            profil_candidat_translator=ProfilCandidatTranslator(),
            question_specifique_translator=QuestionSpecifiqueTranslator(),
            academic_year_repository=AcademicYearRepository(),
            emplacement_document_repository=EmplacementDocumentRepository(),
            comptabilite_translator=ComptabiliteTranslator(),
            groupe_supervision_repository=GroupeDeSupervisionRepository(),
            promoteur_translator=PromoteurTranslator(),
            membre_ca_translator=MembreCATranslator(),
        )
    ),
    InitialiserEmplacementDocumentLibreNonReclamableCommand: lambda msg_bus, cmd: (
        initialiser_emplacement_document_libre_non_reclamable(
            cmd,
            emplacement_document_repository=EmplacementDocumentRepository(),
        )
    ),
    InitialiserEmplacementDocumentLibreAReclamerCommand: (
        lambda msg_bus, cmd: initialiser_emplacement_document_libre_a_reclamer(
            cmd,
            emplacement_document_repository=EmplacementDocumentRepository(),
            classe_enumeration_onglets_checklist=OngletsChecklist,
        )
    ),
    InitialiserEmplacementDocumentAReclamerCommand: lambda msg_bus, cmd: initialiser_emplacement_document_a_reclamer(
        cmd,
        emplacement_document_repository=EmplacementDocumentRepository(),
    ),
    AnnulerReclamationEmplacementDocumentCommand: lambda msg_bus, cmd: annuler_reclamation_emplacement_document(
        cmd,
        emplacement_document_repository=EmplacementDocumentRepository(),
    ),
    ModifierReclamationEmplacementDocumentCommand: lambda msg_bus, cmd: modifier_reclamation_emplacement_document(
        cmd,
        emplacement_document_repository=EmplacementDocumentRepository(),
    ),
    SupprimerEmplacementDocumentCommand: lambda msg_bus, cmd: supprimer_emplacement_document(
        cmd,
        emplacement_document_repository=EmplacementDocumentRepository(),
    ),
    RemplacerEmplacementDocumentCommand: lambda msg_bus, cmd: remplacer_emplacement_document(
        cmd,
        emplacement_document_repository=EmplacementDocumentRepository(),
    ),
    RemplirEmplacementDocumentParGestionnaireCommand: (
        lambda msg_bus, cmd: remplir_emplacement_document_par_gestionnaire(
            cmd,
            emplacement_document_repository=EmplacementDocumentRepository(),
        )
    ),
    ReclamerDocumentsAuCandidatCommand: lambda msg_bus, cmd: reclamer_documents_au_candidat(
        cmd,
        proposition_repository=PropositionRepository(),
        emplacement_document_repository=EmplacementDocumentRepository(),
        notification=Notification(),
        historique=HistoriqueGlobal(),
    ),
    RetyperDocumentCommand: lambda msg_bus, cmd: retyper_document(
        cmd,
        emplacement_document_repository=EmplacementDocumentRepository(),
    ),
}
