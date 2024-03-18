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
from admission.ddd.admission.formation_generale.commands import *
from admission.ddd.admission.formation_generale.test.factory.repository.paiement_frais_dossier import (
    PaiementFraisDossierInMemoryRepositoryFactory,
)
from admission.ddd.admission.formation_generale.use_case.read import *
from admission.ddd.admission.formation_generale.use_case.read.recuperer_pdf_temporaire_decision_sic_service import (
    recuperer_pdf_temporaire_decision_sic,
)
from admission.ddd.admission.formation_generale.use_case.write import *
from admission.ddd.admission.formation_generale.use_case.write.approuver_admission_par_sic_service import (
    approuver_admission_par_sic,
)
from admission.ddd.admission.formation_generale.use_case.write.approuver_inscription_par_sic_service import (
    approuver_inscription_par_sic,
)
from admission.ddd.admission.formation_generale.use_case.write.modifier_checklist_choix_formation_service import (
    modifier_checklist_choix_formation,
)
from admission.ddd.admission.formation_generale.use_case.write.refuser_admission_par_sic_service import (
    refuser_admission_par_sic,
)
from admission.ddd.admission.formation_generale.use_case.write.refuser_inscription_par_sic_service import (
    refuser_inscription_par_sic,
)
from admission.ddd.admission.formation_generale.use_case.write.specifier_financabilite_regle_service import (
    specifier_financabilite_regle,
)
from admission.ddd.admission.formation_generale.use_case.write.specifier_financabilite_resultat_calcul_service import (
    specifier_financabilite_resultat_calcul,
)
from admission.ddd.admission.formation_generale.use_case.write.specifier_besoin_de_derogation_service import (
    specifier_besoin_de_derogation,
)
from admission.ddd.admission.formation_generale.use_case.write.specifier_informations_acceptation_proposition_par_sic_service import (
    specifier_informations_acceptation_proposition_par_sic,
)
from admission.ddd.admission.formation_generale.use_case.write.specifier_motifs_refus_proposition_par_sic_service import (
    specifier_motifs_refus_proposition_par_sic,
)
from admission.ddd.admission.use_case.read import (
    recuperer_questions_specifiques_proposition,
)
from admission.ddd.admission.use_case.write import (
    initialiser_emplacement_document_libre_non_reclamable,
    initialiser_emplacement_document_a_reclamer,
    annuler_reclamation_emplacement_document,
    modifier_reclamation_emplacement_document,
    supprimer_emplacement_document,
    remplacer_emplacement_document,
    remplir_emplacement_document_par_gestionnaire,
    initialiser_emplacement_document_libre_a_reclamer,
)
from admission.infrastructure.admission.domain.service.in_memory.annee_inscription_formation import (
    AnneeInscriptionFormationInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.bourse import BourseInMemoryTranslator
from admission.infrastructure.admission.domain.service.in_memory.calendrier_inscription import (
    CalendrierInscriptionInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.elements_confirmation import (
    ElementsConfirmationInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.historique import (
    HistoriqueInMemory as HistoriqueGlobalInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.maximum_propositions import (
    MaximumPropositionsAutoriseesInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.poste_diplomatique import (
    PosteDiplomatiqueInMemoryFactory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.domain.service.in_memory.recuperer_documents_proposition import (
    EmplacementsDocumentsPropositionInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.titres_acces import TitresAccesInMemory
from admission.infrastructure.admission.domain.service.in_memory.unites_enseignement_translator import (
    UnitesEnseignementInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.comptabilite import (
    ComptabiliteInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.historique import (
    HistoriqueInMemory as HistoriqueFormationGeneraleInMemory,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.inscription_tardive import (
    InscriptionTardiveInMemory,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.notification import (
    NotificationInMemory,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.pdf_generation import (
    PDFGenerationInMemory,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.question_specifique import (
    QuestionSpecifiqueInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.reference import (
    ReferenceInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from admission.infrastructure.admission.repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from admission.infrastructure.admission.shared_kernel.email_destinataire.repository.in_memory.email_destinataire import \
    EmailDestinataireInMemoryRepository
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)

_formation_generale_translator = FormationGeneraleInMemoryTranslator()
_annee_inscription_formation_translator = AnneeInscriptionFormationInMemoryTranslator()
_proposition_repository = PropositionInMemoryRepository()
_bourse_translator = BourseInMemoryTranslator()
_titres_acces = TitresAccesInMemory()
_profil_candidat_translator = ProfilCandidatInMemoryTranslator()
_question_specific_translator = QuestionSpecifiqueInMemoryTranslator()
_academic_year_repository = AcademicYearInMemoryRepository()
_comptabilite_translator = ComptabiliteInMemoryTranslator()
_maximum_propositions_autorisees = MaximumPropositionsAutoriseesInMemory()
_historique_global = HistoriqueGlobalInMemory()
_historique_formation_generale = HistoriqueFormationGeneraleInMemory()
_emplacements_documents_demande_translator = EmplacementsDocumentsPropositionInMemoryTranslator()
_emplacement_document_repository = emplacement_document_in_memory_repository
_personne_connue_ucl_translator = PersonneConnueUclInMemoryTranslator()
_paiement_frais_dossier = PaiementFraisDossierInMemoryRepositoryFactory()
_notification = NotificationInMemory()
_pdf_generation = PDFGenerationInMemory()
_unites_enseignement_translator = UnitesEnseignementInMemoryTranslator()
_poste_diplomatique_translator = PosteDiplomatiqueInMemoryFactory()
_titre_acces_selectionnable_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
_reference_translator = ReferenceInMemoryTranslator()
_email_destinataire_repository = EmailDestinataireInMemoryRepository()


COMMAND_HANDLERS = {
    RechercherFormationGeneraleQuery: lambda msg_bus, cmd: rechercher_formations(
        cmd,
        formation_generale_translator=_formation_generale_translator,
        annee_inscription_formation_translator=_annee_inscription_formation_translator,
    ),
    InitierPropositionCommand: lambda msg_bus, cmd: initier_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_generale_translator,
        bourse_translator=_bourse_translator,
        maximum_propositions_service=_maximum_propositions_autorisees,
        historique=_historique_global,
    ),
    ListerPropositionsCandidatQuery: lambda msg_bus, cmd: lister_propositions_candidat(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    RecupererPropositionQuery: lambda msg_bus, cmd: recuperer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    ModifierChoixFormationCommand: lambda msg_bus, cmd: modifier_choix_formation(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_generale_translator,
        bourse_translator=_bourse_translator,
    ),
    ModifierChecklistChoixFormationCommand: lambda msg_bus, cmd: modifier_checklist_choix_formation(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_generale_translator,
    ),
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique_global,
    ),
    VerifierPropositionQuery: lambda msg_bus, cmd: verifier_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_generale_translator,
        titres_acces=_titres_acces,
        profil_candidat_translator=_profil_candidat_translator,
        calendrier_inscription=CalendrierInscriptionInMemory(),
        academic_year_repository=_academic_year_repository,
        questions_specifiques_translator=_question_specific_translator,
        maximum_propositions_service=_maximum_propositions_autorisees,
    ),
    SoumettrePropositionCommand: lambda msg_bus, cmd: soumettre_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_generale_translator,
        titres_acces=_titres_acces,
        profil_candidat_translator=_profil_candidat_translator,
        calendrier_inscription=CalendrierInscriptionInMemory(),
        academic_year_repository=_academic_year_repository,
        questions_specifiques_translator=_question_specific_translator,
        element_confirmation=ElementsConfirmationInMemory(),
        notification=_notification,
        maximum_propositions_service=_maximum_propositions_autorisees,
        inscription_tardive_service=InscriptionTardiveInMemory(),
        paiement_frais_dossier_service=_paiement_frais_dossier,
        historique=_historique_global,
    ),
    CompleterCurriculumCommand: lambda msg_bus, cmd: completer_curriculum(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    CompleterComptabilitePropositionCommand: lambda msg_bus, cmd: completer_comptabilite_proposition(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    GetComptabiliteQuery: lambda msg_bus, cmd: recuperer_comptabilite(
        cmd,
        comptabilite_translator=_comptabilite_translator,
    ),
    VerifierCurriculumQuery: lambda msg_bus, cmd: verifier_curriculum(
        cmd,
        proposition_repository=_proposition_repository,
        profil_candidat_translator=_profil_candidat_translator,
        academic_year_repository=_academic_year_repository,
        formation_translator=_formation_generale_translator,
    ),
    DeterminerAnneeAcademiqueEtPotQuery: lambda msg_bus, cmd: determiner_annee_academique_et_pot(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_generale_translator,
        titres_acces=_titres_acces,
        profil_candidat_translator=_profil_candidat_translator,
        calendrier_inscription=CalendrierInscriptionInMemory(),
    ),
    RecupererElementsConfirmationQuery: lambda msg_bus, cmd: recuperer_elements_confirmation(
        cmd,
        proposition_repository=_proposition_repository,
        element_confirmation=ElementsConfirmationInMemory(),
        formation_translator=_formation_generale_translator,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    RecupererResumePropositionQuery: lambda msg_bus, cmd: recuperer_resume_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        i_profil_candidat_translator=_profil_candidat_translator,
        i_comptabilite_translator=_comptabilite_translator,
        academic_year_repository=_academic_year_repository,
    ),
    RecupererPropositionGestionnaireQuery: lambda msg_bus, cmd: recuperer_proposition_gestionnaire(
        cmd,
        proposition_repository=_proposition_repository,
        unites_enseignement_translator=_unites_enseignement_translator,
    ),
    RecupererDocumentsPropositionQuery: lambda msg_bus, cmd: recuperer_documents_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        profil_candidat_translator=_profil_candidat_translator,
        comptabilite_translator=_comptabilite_translator,
        question_specifique_translator=_question_specific_translator,
        emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
        academic_year_repository=_academic_year_repository,
        personne_connue_translator=_personne_connue_ucl_translator,
    ),
    RecupererQuestionsSpecifiquesQuery: lambda msg_bus, cmd: recuperer_questions_specifiques_proposition(
        cmd,
        question_specifique_translator=_question_specific_translator,
    ),
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand: (
        lambda msg_bus, cmd: recalculer_emplacements_documents_non_libres_proposition(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            comptabilite_translator=_comptabilite_translator,
            question_specifique_translator=_question_specific_translator,
            academic_year_repository=_academic_year_repository,
            emplacement_document_repository=_emplacement_document_repository,
        )
    ),
    ReclamerDocumentsAuCandidatParSICCommand: lambda msg_bus, cmd: reclamer_documents_au_candidat_par_sic(
        cmd,
        proposition_repository=_proposition_repository,
        emplacement_document_repository=_emplacement_document_repository,
        notification=_notification,
        historique=_historique_global,
    ),
    ReclamerDocumentsAuCandidatParFACCommand: lambda msg_bus, cmd: reclamer_documents_au_candidat_par_fac(
        cmd,
        proposition_repository=_proposition_repository,
        emplacement_document_repository=_emplacement_document_repository,
        notification=_notification,
        historique=_historique_global,
    ),
    RecupererDocumentsReclamesPropositionQuery: lambda msg_bus, cmd: recuperer_documents_reclames_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        profil_candidat_translator=_profil_candidat_translator,
        comptabilite_translator=_comptabilite_translator,
        question_specifique_translator=_question_specific_translator,
        emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
        academic_year_repository=_academic_year_repository,
        personne_connue_translator=_personne_connue_ucl_translator,
    ),
    CompleterEmplacementsDocumentsParCandidatCommand: lambda msg_bus, cmd: (
        completer_emplacements_documents_par_candidat(
            cmd,
            proposition_repository=_proposition_repository,
            emplacement_document_repository=_emplacement_document_repository,
            historique=_historique_global,
            profil_candidat_translator=_profil_candidat_translator,
            comptabilite_translator=_comptabilite_translator,
            question_specifique_translator=_question_specific_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_ucl_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            notification=_notification,
        )
    ),
    InitialiserEmplacementDocumentLibreNonReclamableCommand: lambda msg_bus, cmd: (
        initialiser_emplacement_document_libre_non_reclamable(
            cmd,
            emplacement_document_repository=_emplacement_document_repository,
        )
    ),
    InitialiserEmplacementDocumentLibreAReclamerCommand: (
        lambda msg_bus, cmd: initialiser_emplacement_document_libre_a_reclamer(
            cmd,
            emplacement_document_repository=_emplacement_document_repository,
        )
    ),
    InitialiserEmplacementDocumentAReclamerCommand: lambda msg_bus, cmd: initialiser_emplacement_document_a_reclamer(
        cmd,
        emplacement_document_repository=_emplacement_document_repository,
    ),
    AnnulerReclamationEmplacementDocumentCommand: lambda msg_bus, cmd: annuler_reclamation_emplacement_document(
        cmd,
        emplacement_document_repository=_emplacement_document_repository,
    ),
    ModifierReclamationEmplacementDocumentCommand: lambda msg_bus, cmd: modifier_reclamation_emplacement_document(
        cmd,
        emplacement_document_repository=_emplacement_document_repository,
    ),
    SupprimerEmplacementDocumentCommand: lambda msg_bus, cmd: supprimer_emplacement_document(
        cmd,
        emplacement_document_repository=_emplacement_document_repository,
    ),
    RemplacerEmplacementDocumentCommand: lambda msg_bus, cmd: remplacer_emplacement_document(
        cmd,
        emplacement_document_repository=_emplacement_document_repository,
    ),
    RemplirEmplacementDocumentParGestionnaireCommand: lambda msg_bus, cmd: (
        remplir_emplacement_document_par_gestionnaire(
            cmd,
            emplacement_document_repository=_emplacement_document_repository,
        )
    ),
    RecupererResumeEtEmplacementsDocumentsPropositionQuery: (
        lambda msg_bus, cmd: recuperer_resume_et_emplacements_documents_proposition(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            comptabilite_translator=_comptabilite_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_ucl_translator,
            question_specifique_translator=_question_specific_translator,
        )
    ),
    SpecifierPaiementNecessaireCommand: lambda msg_bus, cmd: specifier_paiement_necessaire(
        cmd,
        proposition_repository=_proposition_repository,
        notification=_notification,
        paiement_frais_dossier_service=_paiement_frais_dossier,
        historique=_historique_formation_generale,
    ),
    EnvoyerRappelPaiementCommand: lambda msg_bus, cmd: envoyer_rappel_paiement(
        cmd,
        proposition_repository=_proposition_repository,
        notification=_notification,
        paiement_frais_dossier_service=_paiement_frais_dossier,
        historique=_historique_formation_generale,
    ),
    SpecifierPaiementPlusNecessaireCommand: lambda msg_bus, cmd: specifier_paiement_plus_necessaire(
        cmd,
        proposition_repository=_proposition_repository,
        paiement_frais_dossier_service=_paiement_frais_dossier,
        historique=_historique_formation_generale,
    ),
    PayerFraisDossierPropositionSuiteSoumissionCommand: (
        lambda msg_bus, cmd: payer_frais_dossier_proposition_suite_soumission(
            msg_bus,
            cmd,
            proposition_repository=_proposition_repository,
            notification=_notification,
            paiement_frais_dossier_service=_paiement_frais_dossier,
            historique=_historique_formation_generale,
            reference_translator=_reference_translator,
        )
    ),
    PayerFraisDossierPropositionSuiteDemandeCommand: (
        lambda msg_bus, cmd: payer_frais_dossier_proposition_suite_demande(
            msg_bus,
            cmd,
            proposition_repository=_proposition_repository,
            paiement_frais_dossier_service=_paiement_frais_dossier,
            historique=_historique_formation_generale,
            reference_translator=_reference_translator,
        )
    ),
    EnvoyerPropositionAFacLorsDeLaDecisionFacultaireCommand: (
        lambda msg_bus, cmd: envoyer_proposition_a_fac_lors_de_la_decision_facultaire(
            cmd,
            proposition_repository=_proposition_repository,
            email_destinataire_repository=_email_destinataire_repository,
            notification=_notification,
            historique=_historique_formation_generale,
        )
    ),
    SpecifierMotifsRefusPropositionParFaculteCommand: (
        lambda msg_bus, cmd: specifier_motifs_refus_proposition_par_faculte(
            cmd,
            proposition_repository=_proposition_repository,
        )
    ),
    RefuserPropositionParFaculteCommand: lambda msg_bus, cmd: refuser_proposition_par_faculte(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique_formation_generale,
        pdf_generation=_pdf_generation,
        personne_connue_ucl_translator=_personne_connue_ucl_translator,
        unites_enseignement_translator=_unites_enseignement_translator,
    ),
    SpecifierInformationsAcceptationPropositionParFaculteCommand: (
        lambda msg_bus, cmd: specifier_informations_acceptation_proposition_par_faculte(
            cmd,
            proposition_repository=_proposition_repository,
        )
    ),
    ApprouverPropositionParFaculteCommand: lambda msg_bus, cmd: approuver_proposition_par_faculte(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique_formation_generale,
        pdf_generation=_pdf_generation,
        personne_connue_ucl_translator=_personne_connue_ucl_translator,
        unites_enseignement_translator=_unites_enseignement_translator,
        titre_acces_selectionnable_repository=_titre_acces_selectionnable_repository,
        profil_candidat_translator=_profil_candidat_translator,
        academic_year_repository=_academic_year_repository,
    ),
    CompleterQuestionsSpecifiquesCommand: lambda msg_bus, cmd: completer_questions_specifiques(
        cmd,
        proposition_repository=_proposition_repository,
        poste_diplomatique_translator=_poste_diplomatique_translator,
    ),
    SpecifierPaiementVaEtreOuvertParCandidatCommand: (
        lambda msg_bus, cmd: specifier_paiement_va_etre_ouvert_par_candidat(
            cmd,
            proposition_repository=_proposition_repository,
            paiement_frais_dossier_service=_paiement_frais_dossier,
        )
    ),
    RecupererListePaiementsPropositionQuery: lambda msg_bus, cmd: recuperer_liste_paiements_proposition(
        cmd,
        paiement_frais_dossier_service=_paiement_frais_dossier,
    ),
    ModifierChoixFormationParGestionnaireCommand: lambda msg_bus, cmd: modifier_choix_formation_par_gestionnaire(
        cmd,
        proposition_repository=_proposition_repository,
        bourse_translator=_bourse_translator,
    ),
    CompleterQuestionsSpecifiquesParGestionnaireCommand: (
        lambda msg_bus, cmd: completer_questions_specifiques_par_gestionnaire(
            cmd,
            proposition_repository=_proposition_repository,
            poste_diplomatique_translator=_poste_diplomatique_translator,
        )
    ),
    EnvoyerPropositionAuSicLorsDeLaDecisionFacultaireCommand: (
        lambda msg_bus, cmd: envoyer_proposition_au_sic_lors_de_la_decision_facultaire(
            cmd,
            proposition_repository=_proposition_repository,
            historique=_historique_formation_generale,
        )
    ),
    ModifierStatutChecklistParcoursAnterieurCommand: lambda msg_bus, cmd: modifier_statut_checklist_parcours_anterieur(
        cmd,
        proposition_repository=_proposition_repository,
        titre_acces_selectionnable_repository=_titre_acces_selectionnable_repository,
    ),
    SpecifierConditionAccesPropositionCommand: lambda msg_bus, cmd: specifier_condition_acces_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        titre_acces_selectionnable_repository=_titre_acces_selectionnable_repository,
    ),
    SpecifierEquivalenceTitreAccesEtrangerPropositionCommand: (
        lambda msg_bus, cmd: specifier_equivalence_titre_acces_etranger_proposition(
            cmd,
            proposition_repository=_proposition_repository,
        )
    ),
    SpecifierBesoinDeDerogationSicCommand: (
        lambda msg_bus, cmd: specifier_besoin_de_derogation(
            cmd,
            proposition_repository=_proposition_repository,
        )
    ),
    SpecifierExperienceEnTantQueTitreAccesCommand: lambda msg_bus, cmd: specifier_experience_en_tant_que_titre_acces(
        cmd,
        titre_acces_selectionnable_repository=_titre_acces_selectionnable_repository,
    ),
    RecupererTitresAccesSelectionnablesPropositionQuery: (
        lambda msg_bus, cmd: recuperer_titres_acces_selectionnables_proposition(
            cmd,
            titre_acces_selectionnable_repository=_titre_acces_selectionnable_repository,
        )
    ),
    SpecifierFinancabiliteResultatCalculCommand: lambda msg_bus, cmd: specifier_financabilite_resultat_calcul(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    SpecifierFinancabiliteRegleCommand: lambda msg_bus, cmd: specifier_financabilite_regle(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    ModifierStatutChecklistExperienceParcoursAnterieurCommand: (
        lambda msg_bus, cmd: modifier_statut_checklist_experience_parcours_anterieur(
            cmd,
            proposition_repository=_proposition_repository,
        )
    ),
    SpecifierInformationsAcceptationPropositionParSicCommand: (
        lambda msg_bus, cmd: specifier_informations_acceptation_proposition_par_sic(
            cmd,
            proposition_repository=_proposition_repository,
            historique=_historique_formation_generale,
            profil_candidat_translator=_profil_candidat_translator,
            comptabilite_translator=_comptabilite_translator,
            question_specifique_translator=_question_specific_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_ucl_translator,
        )
    ),
    ModifierAuthentificationExperienceParcoursAnterieurCommand: (
        lambda msg_bus, cmd: modifier_authentification_experience_parcours_anterieur(
            cmd,
            proposition_repository=_proposition_repository,
            notification=_notification,
            historique=_historique_formation_generale,
        )
    ),
    SpecifierMotifsRefusPropositionParSicCommand: (
        lambda msg_bus, cmd: specifier_motifs_refus_proposition_par_sic(
            cmd,
            proposition_repository=_proposition_repository,
            historique=_historique_formation_generale,
        )
    ),
    RefuserAdmissionParSicCommand: (
        lambda msg_bus, cmd: refuser_admission_par_sic(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            historique=_historique_formation_generale,
            notification=_notification,
            pdf_generation=_pdf_generation,
        )
    ),
    RefuserInscriptionParSicCommand: (
        lambda msg_bus, cmd: refuser_inscription_par_sic(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            historique=_historique_formation_generale,
            notification=_notification,
            pdf_generation=_pdf_generation,
        )
    ),
    ApprouverAdmissionParSicCommand: (
        lambda msg_bus, cmd: approuver_admission_par_sic(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            historique=_historique_formation_generale,
            notification=_notification,
            pdf_generation=_pdf_generation,
            emplacement_document_repository=_emplacement_document_repository,
            comptabilite_translator=_comptabilite_translator,
            question_specifique_translator=_question_specific_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_ucl_translator,
        )
    ),
    ApprouverInscriptionParSicCommand: (
        lambda msg_bus, cmd: approuver_inscription_par_sic(
            cmd,
            proposition_repository=_proposition_repository,
            historique=_historique_formation_generale,
            profil_candidat_translator=_profil_candidat_translator,
            comptabilite_translator=_comptabilite_translator,
            question_specifique_translator=_question_specific_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_ucl_translator,
        )
    ),
    RecupererPdfTemporaireDecisionSicQuery: (
        lambda msg_bus, cmd: recuperer_pdf_temporaire_decision_sic(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            pdf_generation=_pdf_generation,
        )
    ),
}
