##############################################################################
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
##############################################################################
from admission.ddd.admission.formation_generale.commands import *
from admission.ddd.admission.formation_generale.use_case.read import *
from admission.ddd.admission.formation_generale.use_case.write import *
from admission.ddd.admission.formation_generale.use_case.write.modifier_checklist_choix_formation_service import (
    modifier_checklist_choix_formation,
)
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
from admission.infrastructure.admission.domain.service.bourse import BourseTranslator
from admission.infrastructure.admission.domain.service.calendrier_inscription import CalendrierInscription
from admission.infrastructure.admission.domain.service.elements_confirmation import ElementsConfirmation
from admission.infrastructure.admission.domain.service.emplacements_documents_proposition import (
    EmplacementsDocumentsPropositionTranslator,
)
from admission.infrastructure.admission.domain.service.historique import Historique as HistoriqueGlobal
from admission.infrastructure.admission.formation_generale.domain.service.historique import (
    Historique as HistoriqueFormationGenerale,
)
from admission.infrastructure.admission.domain.service.maximum_propositions import MaximumPropositionsAutorisees
from admission.infrastructure.admission.formation_generale.domain.service.paiement_frais_dossier import (
    PaiementFraisDossier,
)
from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.infrastructure.admission.domain.service.titres_acces import TitresAcces
from admission.infrastructure.admission.formation_generale.domain.service.comptabilite import ComptabiliteTranslator
from admission.infrastructure.admission.formation_generale.domain.service.formation import FormationGeneraleTranslator
from admission.infrastructure.admission.formation_generale.domain.service.inscription_tardive import InscriptionTardive
from admission.infrastructure.admission.formation_generale.domain.service.notification import Notification
from admission.infrastructure.admission.formation_generale.domain.service.question_specifique import (
    QuestionSpecifiqueTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.emplacement_document import (
    EmplacementDocumentRepository,
)
from admission.infrastructure.admission.formation_generale.repository.proposition import PropositionRepository
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository
from infrastructure.shared_kernel.personne_connue_ucl.personne_connue_ucl import PersonneConnueUclTranslator

COMMAND_HANDLERS = {
    RechercherFormationGeneraleQuery: lambda msg_bus, cmd: rechercher_formations(
        cmd,
        formation_generale_translator=FormationGeneraleTranslator(),
        annee_inscription_formation_translator=AnneeInscriptionFormationTranslator(),
    ),
    InitierPropositionCommand: lambda msg_bus, cmd: initier_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationGeneraleTranslator(),
        bourse_translator=BourseTranslator(),
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
        formation_translator=FormationGeneraleTranslator(),
        bourse_translator=BourseTranslator(),
    ),
    ModifierChecklistChoixFormationCommand: lambda msg_bus, cmd: modifier_checklist_choix_formation(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationGeneraleTranslator(),
    ),
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        historique=HistoriqueGlobal(),
    ),
    VerifierPropositionQuery: lambda msg_bus, cmd: verifier_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationGeneraleTranslator(),
        titres_acces=TitresAcces(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        calendrier_inscription=CalendrierInscription(),
        academic_year_repository=AcademicYearRepository(),
        questions_specifiques_translator=QuestionSpecifiqueTranslator(),
        maximum_propositions_service=MaximumPropositionsAutorisees(),
    ),
    SoumettrePropositionCommand: lambda msg_bus, cmd: soumettre_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationGeneraleTranslator(),
        titres_acces=TitresAcces(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        calendrier_inscription=CalendrierInscription(),
        academic_year_repository=AcademicYearRepository(),
        questions_specifiques_translator=QuestionSpecifiqueTranslator(),
        element_confirmation=ElementsConfirmation(),
        notification=Notification(),
        maximum_propositions_service=MaximumPropositionsAutorisees(),
        inscription_tardive_service=InscriptionTardive(),
        paiement_frais_dossier_service=PaiementFraisDossier(),
        historique=HistoriqueGlobal(),
    ),
    CompleterCurriculumCommand: lambda msg_bus, cmd: completer_curriculum(
        cmd,
        proposition_repository=PropositionRepository(),
    ),
    CompleterComptabilitePropositionCommand: lambda msg_bus, cmd: completer_comptabilite_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
    ),
    GetComptabiliteQuery: lambda msg_bus, cmd: recuperer_comptabilite(
        cmd,
        comptabilite_translator=ComptabiliteTranslator(),
    ),
    VerifierCurriculumQuery: lambda msg_bus, cmd: verifier_curriculum(
        cmd,
        proposition_repository=PropositionRepository(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        academic_year_repository=AcademicYearRepository(),
        formation_translator=FormationGeneraleTranslator(),
    ),
    DeterminerAnneeAcademiqueEtPotQuery: lambda msg_bus, cmd: determiner_annee_academique_et_pot(
        cmd,
        proposition_repository=PropositionRepository(),
        formation_translator=FormationGeneraleTranslator(),
        titres_acces=TitresAcces(),
        profil_candidat_translator=ProfilCandidatTranslator(),
        calendrier_inscription=CalendrierInscription(),
    ),
    RecupererElementsConfirmationQuery: lambda msg_bus, cmd: recuperer_elements_confirmation(
        cmd,
        proposition_repository=PropositionRepository(),
        element_confirmation=ElementsConfirmation(),
        formation_translator=FormationGeneraleTranslator(),
        profil_candidat_translator=ProfilCandidatTranslator(),
    ),
    RecupererResumePropositionQuery: lambda msg_bus, cmd: recuperer_resume_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
        i_profil_candidat_translator=ProfilCandidatTranslator(),
        i_comptabilite_translator=ComptabiliteTranslator(),
        academic_year_repository=AcademicYearRepository(),
    ),
    RecupererPropositionGestionnaireQuery: lambda msg_bus, cmd: recuperer_proposition_gestionnaire(
        cmd,
        proposition_repository=PropositionRepository(),
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
    ),
    RecupererQuestionsSpecifiquesQuery: lambda msg_bus, cmd: recuperer_questions_specifiques_proposition(
        cmd,
        question_specifique_translator=QuestionSpecifiqueTranslator(),
    ),
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand: (
        lambda msg_bus, cmd: recalculer_emplacements_documents_non_libres_proposition(
            cmd,
            proposition_repository=PropositionRepository(),
            profil_candidat_translator=ProfilCandidatTranslator(),
            comptabilite_translator=ComptabiliteTranslator(),
            question_specifique_translator=QuestionSpecifiqueTranslator(),
            academic_year_repository=AcademicYearRepository(),
            emplacement_document_repository=EmplacementDocumentRepository(),
        )
    ),
    ReclamerDocumentsAuCandidatParSICCommand: lambda msg_bus, cmd: reclamer_documents_au_candidat_par_sic(
        cmd,
        proposition_repository=PropositionRepository(),
        emplacement_document_repository=EmplacementDocumentRepository(),
        notification=Notification(),
        historique=HistoriqueGlobal(),
    ),
    ReclamerDocumentsAuCandidatParFACCommand: lambda msg_bus, cmd: reclamer_documents_au_candidat_par_fac(
        cmd,
        proposition_repository=PropositionRepository(),
        emplacement_document_repository=EmplacementDocumentRepository(),
        notification=Notification(),
        historique=HistoriqueGlobal(),
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
    ),
    CompleterEmplacementsDocumentsParCandidatCommand: lambda msg_bus, cmd: (
        completer_emplacements_documents_par_candidat(
            cmd,
            proposition_repository=PropositionRepository(),
            emplacement_document_repository=EmplacementDocumentRepository(),
            historique=HistoriqueGlobal(),
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
    RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery: (
        lambda msg_bus, cmd: recuperer_resume_et_emplacements_documents_non_libres_proposition(
            cmd,
            proposition_repository=PropositionRepository(),
            profil_candidat_translator=ProfilCandidatTranslator(),
            comptabilite_translator=ComptabiliteTranslator(),
            emplacements_documents_demande_translator=EmplacementsDocumentsPropositionTranslator(),
            academic_year_repository=AcademicYearRepository(),
            personne_connue_translator=PersonneConnueUclTranslator(),
            question_specifique_translator=QuestionSpecifiqueTranslator(),
        )
    ),
    SpecifierPaiementNecessaireCommand: lambda msg_bus, cmd: specifier_paiement_necessaire(
        cmd,
        proposition_repository=PropositionRepository(),
        notification=Notification(),
        paiement_frais_dossier_service=PaiementFraisDossier(),
        historique=HistoriqueFormationGenerale(),
    ),
    EnvoyerRappelPaiementCommand: lambda msg_bus, cmd: envoyer_rappel_paiement(
        cmd,
        proposition_repository=PropositionRepository(),
        notification=Notification(),
        paiement_frais_dossier_service=PaiementFraisDossier(),
        historique=HistoriqueFormationGenerale(),
    ),
    SpecifierPaiementPlusNecessaireCommand: lambda msg_bus, cmd: specifier_paiement_plus_necessaire(
        cmd,
        proposition_repository=PropositionRepository(),
        paiement_frais_dossier_service=PaiementFraisDossier(),
        historique=HistoriqueFormationGenerale(),
    ),
    PayerFraisDossierPropositionSuiteSoumissionCommand: (
        lambda msg_bus, cmd: payer_frais_dossier_proposition_suite_soumission(
            cmd,
            proposition_repository=PropositionRepository(),
            notification=Notification(),
            paiement_frais_dossier_service=PaiementFraisDossier(),
            historique=HistoriqueFormationGenerale(),
            profil_candidat_translator=ProfilCandidatTranslator(),
            questions_specifiques_translator=QuestionSpecifiqueTranslator(),
        )
    ),
    PayerFraisDossierPropositionSuiteDemandeCommand: (
        lambda msg_bus, cmd: payer_frais_dossier_proposition_suite_demande(
            cmd,
            proposition_repository=PropositionRepository(),
            paiement_frais_dossier_service=PaiementFraisDossier(),
            historique=HistoriqueFormationGenerale(),
        )
    ),
}
