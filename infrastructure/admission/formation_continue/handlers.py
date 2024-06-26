##############################################################################
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
##############################################################################

from admission.ddd.admission.formation_continue.commands import *
from admission.ddd.admission.formation_continue.use_case.read import *
from admission.ddd.admission.formation_continue.use_case.write import *
from admission.ddd.admission.use_case.read import recuperer_questions_specifiques_proposition
from admission.ddd.admission.use_case.write import (
    initialiser_emplacement_document_libre_non_reclamable,
    initialiser_emplacement_document_libre_a_reclamer,
    initialiser_emplacement_document_a_reclamer,
    annuler_reclamation_emplacement_document,
    modifier_reclamation_emplacement_document,
    supprimer_emplacement_document,
    remplacer_emplacement_document,
    remplir_emplacement_document_par_gestionnaire,
)
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.infrastructure.admission.domain.service.calendrier_inscription import CalendrierInscription
from admission.infrastructure.admission.domain.service.elements_confirmation import ElementsConfirmation
from admission.infrastructure.admission.domain.service.emplacements_documents_proposition import (
    EmplacementsDocumentsPropositionTranslator,
)
from admission.infrastructure.admission.domain.service.historique import Historique as HistoriqueGlobal
from admission.infrastructure.admission.domain.service.maximum_propositions import MaximumPropositionsAutorisees
from admission.infrastructure.admission.domain.service.titres_acces import TitresAcces
from admission.infrastructure.admission.formation_continue.domain.service.formation import FormationContinueTranslator
from admission.infrastructure.admission.formation_continue.domain.service.historique import Historique
from admission.infrastructure.admission.formation_continue.domain.service.lister_demandes import ListerDemandesService
from admission.infrastructure.admission.formation_continue.domain.service.notification import Notification
from admission.infrastructure.admission.formation_continue.domain.service.question_specifique import (
    QuestionSpecifiqueTranslator,
)
from admission.infrastructure.admission.formation_continue.repository.emplacement_document import (
    EmplacementDocumentRepository,
)
from admission.infrastructure.admission.formation_continue.repository.proposition import PropositionRepository
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator
from infrastructure.shared_kernel.profil.repository.profil import ProfilRepository

COMMAND_HANDLERS = {
    RechercherFormationContinueQuery: lambda msg_bus, cmd: rechercher_formations(
        cmd,
        formation_continue_translator=FormationContinueTranslator(),
        annee_inscription_formation_translator=AnneeInscriptionFormationTranslator(),
    ),
    RecupererFormationContinueQuery: lambda msg_bus, cmd: recuperer_formation(
        cmd,
        formation_continue_translator=FormationContinueTranslator(),
    ),
    InitierPropositionCommand: lambda msg_bus, cmd: initier_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationContinueTranslator(),
        maximum_propositions_service=MaximumPropositionsAutorisees(),
        historique=HistoriqueGlobal(),
    ),
    ListerPropositionsCandidatQuery: lambda msg_bus, cmd: lister_propositions_candidat(
        cmd,
        proposition_repository=PropositionRepository(),
    ),
    RecupererPropositionQuery: lambda msg_bus, cmd: recuperer_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
    ),
    ModifierChoixFormationCommand: lambda msg_bus, cmd: modifier_choix_formation(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationContinueTranslator(),
    ),
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        historique=HistoriqueGlobal(),
    ),
    VerifierPropositionQuery: lambda msg_bus, cmd: verifier_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationContinueTranslator(),
        titres_acces=TitresAcces(),
        profil_candidat_translator=ProfilRepository(),
        calendrier_inscription=CalendrierInscription(),
        maximum_propositions_service=MaximumPropositionsAutorisees(),
        questions_specifiques_translator=QuestionSpecifiqueTranslator(),
    ),
    SoumettrePropositionCommand: lambda msg_bus, cmd: soumettre_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationContinueTranslator(),
        titres_acces=TitresAcces(),
        profil_candidat_translator=ProfilRepository(),
        calendrier_inscription=CalendrierInscription(),
        element_confirmation=ElementsConfirmation(),
        notification=Notification(),
        maximum_propositions_service=MaximumPropositionsAutorisees(),
        questions_specifiques_translator=QuestionSpecifiqueTranslator(),
        historique=HistoriqueGlobal(),
    ),
    CompleterCurriculumCommand: lambda msg_bus, cmd: completer_curriculum(
        cmd,
        proposition_repository=PropositionRepository(),
    ),
    DeterminerAnneeAcademiqueEtPotQuery: lambda msg_bus, cmd: determiner_annee_academique_et_pot(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationContinueTranslator(),
        titres_acces=TitresAcces(),
        profil_candidat_translator=ProfilRepository(),
        calendrier_inscription=CalendrierInscription(),
    ),
    RecupererElementsConfirmationQuery: lambda msg_bus, cmd: recuperer_elements_confirmation(
        cmd,
        proposition_repository=PropositionRepository(),
        element_confirmation=ElementsConfirmation(),
        formation_translator=FormationContinueTranslator(),
        profil_candidat_translator=ProfilRepository(),
    ),
    CompleterQuestionsSpecifiquesCommand: lambda msg_bus, cmd: completer_questions_specifiques(
        cmd,
        proposition_repository=PropositionRepository(),
    ),
    RecupererResumePropositionQuery: lambda msg_bus, cmd: recuperer_resume_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        i_profil_candidat_translator=ProfilRepository(),
        academic_year_repository=AcademicYearRepository(),
    ),
    RecupererQuestionsSpecifiquesQuery: lambda msg_bus, cmd: recuperer_questions_specifiques_proposition(
        cmd,
        question_specifique_translator=QuestionSpecifiqueTranslator(),
    ),
    RecupererDocumentsPropositionQuery: lambda msg_bus, cmd: recuperer_documents_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        profil_candidat_translator=ProfilRepository(),
        question_specifique_translator=QuestionSpecifiqueTranslator(),
        emplacements_documents_demande_translator=EmplacementsDocumentsPropositionTranslator(),
        academic_year_repository=AcademicYearRepository(),
        personne_connue_translator=PersonneConnueUclTranslator(),
    ),
    RecupererDocumentsReclamesPropositionQuery: lambda msg_bus, cmd: recuperer_documents_reclames_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        profil_candidat_translator=ProfilRepository(),
        question_specifique_translator=QuestionSpecifiqueTranslator(),
        emplacements_documents_demande_translator=EmplacementsDocumentsPropositionTranslator(),
        academic_year_repository=AcademicYearRepository(),
        personne_connue_translator=PersonneConnueUclTranslator(),
    ),
    RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery: lambda msg_bus, cmd: recuperer_resume_et_emplacements_documents_non_libres_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        profil_candidat_translator=ProfilRepository(),
        emplacements_documents_demande_translator=EmplacementsDocumentsPropositionTranslator(),
        academic_year_repository=AcademicYearRepository(),
        personne_connue_translator=PersonneConnueUclTranslator(),
        question_specifique_translator=QuestionSpecifiqueTranslator(),
    ),
    RetyperDocumentCommand: (
        lambda msg_bus, cmd: retyper_document(
            cmd,
            emplacement_document_repository=EmplacementDocumentRepository(),
        )
    ),
    MettreEnAttenteCommand: lambda msg_bus, cmd: mettre_en_attente(
        cmd,
        proposition_repository=PropositionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    ApprouverParFacCommand: lambda msg_bus, cmd: approuver_par_fac(
        cmd,
        proposition_repository=PropositionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    RefuserPropositionCommand: lambda msg_bus, cmd: refuser_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    AnnulerPropositionCommand: lambda msg_bus, cmd: annuler_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    ValiderPropositionCommand: lambda msg_bus, cmd: valider_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        historique=Historique(),
        notification=Notification(),
    ),
    CloturerPropositionCommand: lambda msg_bus, cmd: cloturer_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        historique=Historique(),
    ),
    ListerDemandesQuery: lambda msg_bus, cmd: lister_demandes(
        cmd,
        lister_demandes_service=ListerDemandesService(),
    ),
    ModifierChoixFormationParGestionnaireCommand: lambda msg_bus, cmd: modifier_choix_formation_par_gestionnaire(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationContinueTranslator(),
    ),
    CompleterQuestionsSpecifiquesParGestionnaireCommand: (
        lambda msg_bus, cmd: completer_questions_specifiques_par_gestionnaire(
            cmd,
            proposition_repository=PropositionRepository(),
        )
    ),
    AnnulerReclamationDocumentsAuCandidatCommand: (
        lambda msg_bus, cmd: annuler_reclamation_documents_au_candidat(
            cmd,
            proposition_repository=PropositionRepository(),
            emplacement_document_repository=EmplacementDocumentRepository(),
            historique=HistoriqueGlobal(),
            profil_candidat_translator=ProfilRepository(),
            question_specifique_translator=QuestionSpecifiqueTranslator(),
            academic_year_repository=AcademicYearRepository(),
            personne_connue_translator=PersonneConnueUclTranslator(),
            emplacements_documents_demande_translator=EmplacementsDocumentsPropositionTranslator(),
        )
    ),
    CompleterEmplacementsDocumentsParCandidatCommand: lambda msg_bus, cmd: (
        completer_emplacements_documents_par_candidat(
            cmd,
            proposition_repository=PropositionRepository(),
            emplacement_document_repository=EmplacementDocumentRepository(),
            historique=HistoriqueGlobal(),
            profil_candidat_translator=ProfilRepository(),
            question_specifique_translator=QuestionSpecifiqueTranslator(),
            academic_year_repository=AcademicYearRepository(),
            personne_connue_translator=PersonneConnueUclTranslator(),
            emplacements_documents_demande_translator=EmplacementsDocumentsPropositionTranslator(),
            notification=Notification(),
        )
    ),
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand: (
        lambda msg_bus, cmd: recalculer_emplacements_documents_non_libres_proposition(
            cmd,
            proposition_repository=PropositionRepository(),
            profil_candidat_translator=ProfilRepository(),
            question_specifique_translator=QuestionSpecifiqueTranslator(),
            academic_year_repository=AcademicYearRepository(),
            emplacement_document_repository=EmplacementDocumentRepository(),
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
}
