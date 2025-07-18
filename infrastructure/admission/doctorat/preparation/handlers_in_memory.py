# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    OngletsChecklist,
)
from admission.ddd.admission.doctorat.preparation.use_case.read import *
from admission.ddd.admission.doctorat.preparation.use_case.read.recuperer_doctorat_service import (
    recuperer_doctorat,
)
from admission.ddd.admission.doctorat.preparation.use_case.write import *
from admission.ddd.admission.doctorat.preparation.use_case.write.demander_candidat_modifier_ca_service import (
    demander_candidat_modifier_ca,
)
from admission.ddd.admission.doctorat.preparation.use_case.write.redonner_la_main_au_candidat_service import (
    redonner_la_main_au_candidat,
)
from admission.ddd.admission.doctorat.preparation.use_case.write.soumettre_ca_service import (
    soumettre_ca,
)
from admission.ddd.admission.use_case.read import (
    recuperer_questions_specifiques_proposition,
)
from admission.ddd.admission.use_case.write import (
    annuler_reclamation_emplacement_document,
    initialiser_emplacement_document_a_reclamer,
    initialiser_emplacement_document_libre_a_reclamer,
    initialiser_emplacement_document_libre_non_reclamable,
    modifier_reclamation_emplacement_document,
    remplacer_emplacement_document,
    remplir_emplacement_document_par_gestionnaire,
    supprimer_emplacement_document,
)
from admission.infrastructure.admission.domain.service.in_memory.annee_inscription_formation import (
    AnneeInscriptionFormationInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from infrastructure.financabilite.domain.service.in_memory.financabilite import (
    FinancabiliteInMemoryFetcher,
)
from infrastructure.reference.domain.service.in_memory.bourse import (
    BourseInMemoryTranslator,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import (
    AcademicYearInMemoryRepository,
)
from infrastructure.shared_kernel.campus.repository.in_memory.campus import (
    UclouvainCampusInMemoryRepository,
)
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)
from infrastructure.shared_kernel.profil.domain.service.in_memory.parcours_interne import (
    ExperienceParcoursInterneInMemoryTranslator,
)
from .domain.service.in_memory.comptabilite import ComptabiliteInMemoryTranslator
from .domain.service.in_memory.doctorat import DoctoratInMemoryTranslator
from .domain.service.in_memory.historique import HistoriqueInMemory
from .domain.service.in_memory.lister_demandes import ListerDemandesInMemoryService
from .domain.service.in_memory.membre_CA import MembreCAInMemoryTranslator
from .domain.service.in_memory.notification import NotificationInMemory
from .domain.service.in_memory.pdf_generation import PDFGenerationInMemory
from .domain.service.in_memory.promoteur import PromoteurInMemoryTranslator
from .domain.service.in_memory.question_specifique import (
    QuestionSpecifiqueInMemoryTranslator,
)
from .repository.doctorat import DoctoratRepository
from .repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from .repository.in_memory.proposition import PropositionInMemoryRepository
from ..validation.repository.in_memory.demande import DemandeInMemoryRepository
from ...domain.service.in_memory.calendrier_inscription import (
    CalendrierInscriptionInMemory,
)
from ...domain.service.in_memory.elements_confirmation import (
    ElementsConfirmationInMemory,
)
from ...domain.service.in_memory.historique import (
    HistoriqueInMemory as HistoriqueGlobalInMemory,
)
from ...domain.service.in_memory.maximum_propositions import (
    MaximumPropositionsAutoriseesInMemory,
)
from ...domain.service.in_memory.raccrocher_experiences_curriculum import (
    RaccrocherExperiencesCurriculumInMemory,
)
from ...domain.service.in_memory.recuperer_documents_proposition import (
    EmplacementsDocumentsPropositionInMemoryTranslator,
)
from ...domain.service.in_memory.titres_acces import TitresAccesInMemory
from ...domain.service.in_memory.unites_enseignement_translator import (
    UnitesEnseignementInMemoryTranslator,
)
from ...repository.in_memory.emplacement_document import (
    emplacement_document_in_memory_repository,
)
from ...repository.in_memory.titre_acces_selectionnable import (
    TitreAccesSelectionnableInMemoryRepositoryFactory,
)
from ...shared_kernel.domain.service.matricule_etudiant import MatriculeEtudiantService
from ...shared_kernel.email_destinataire.repository.in_memory import (
    EmailDestinataireInMemoryRepository,
)

_proposition_repository = PropositionInMemoryRepository()
_groupe_supervision_repository = GroupeDeSupervisionInMemoryRepository()
_demande_repository = DemandeInMemoryRepository()
_academic_year_repository = AcademicYearInMemoryRepository()
_profil_candidat_translator = ProfilCandidatInMemoryTranslator()
_promoteur_translator = PromoteurInMemoryTranslator()
_doctorat_translator = DoctoratInMemoryTranslator()
_doctorat_repository = DoctoratRepository()
_bourse_translator = BourseInMemoryTranslator()
_historique = HistoriqueInMemory()
_notification = NotificationInMemory()
_titres_acces = TitresAccesInMemory()
_membre_ca_translator = MembreCAInMemoryTranslator()
_comptabilite_translator = ComptabiliteInMemoryTranslator()
_maximum_propositions_autorisees = MaximumPropositionsAutoriseesInMemory()
_question_specific_translator = QuestionSpecifiqueInMemoryTranslator()
_emplacements_documents_demande_translator = EmplacementsDocumentsPropositionInMemoryTranslator()
_personne_connue_translator = PersonneConnueUclInMemoryTranslator()
_historique_global = HistoriqueGlobalInMemory()
_emplacement_document_repository = emplacement_document_in_memory_repository
_lister_demandes_service = ListerDemandesInMemoryService()
_unites_enseignement_translator = UnitesEnseignementInMemoryTranslator()
_pdf_generation = PDFGenerationInMemory()
_campus_repository = UclouvainCampusInMemoryRepository()
_email_destinataire_repository = EmailDestinataireInMemoryRepository()
_personne_connue_ucl_translator = PersonneConnueUclInMemoryTranslator()
_titre_acces_selectionnable_repository = TitreAccesSelectionnableInMemoryRepositoryFactory()
_experience_parcours_interne_translator = ExperienceParcoursInterneInMemoryTranslator()
_matricule_etudiant_service = MatriculeEtudiantService()
_financabilite_fetcher = FinancabiliteInMemoryFetcher()
_raccrocher_experiences_curriculum = RaccrocherExperiencesCurriculumInMemory()


COMMAND_HANDLERS = {
    InitierPropositionCommand: lambda msg_bus, cmd: initier_proposition(
        msg_bus,
        cmd,
        proposition_repository=_proposition_repository,
        doctorat_translator=_doctorat_translator,
        historique=_historique,
        maximum_propositions_service=_maximum_propositions_autorisees,
        groupe_supervision_repository=_groupe_supervision_repository,
    ),
    CompleterPropositionCommand: lambda msg_bus, cmd: completer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
    ),
    RechercherDoctoratQuery: lambda msg_bus, cmd: rechercher_doctorats(
        cmd,
        doctorat_translator=_doctorat_translator,
        annee_inscription_formation_translator=AnneeInscriptionFormationInMemoryTranslator(),
    ),
    IdentifierPromoteurCommand: lambda msg_bus, cmd: identifier_promoteur(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        promoteur_translator=_promoteur_translator,
        historique=_historique,
    ),
    IdentifierMembreCACommand: lambda msg_bus, cmd: identifier_membre_ca(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        membre_ca_translator=_membre_ca_translator,
        historique=_historique,
    ),
    ModifierMembreSupervisionExterneCommand: lambda msg_bus, cmd: modifier_membre_supervision_externe(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        promoteur_translator=_promoteur_translator,
        membre_ca_translator=_membre_ca_translator,
        historique=_historique,
    ),
    DemanderSignaturesCommand: lambda msg_bus, cmd: demander_signatures(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        promoteur_translator=_promoteur_translator,
        historique=_historique,
        notification=_notification,
        academic_year_repository=_academic_year_repository,
        profil_candidat_translator=_profil_candidat_translator,
        raccrocher_experiences_curriculum=_raccrocher_experiences_curriculum,
    ),
    RenvoyerInvitationSignatureExterneCommand: lambda msg_bus, cmd: renvoyer_invitation_signature_externe(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        notification=_notification,
    ),
    VerifierPropositionQuery: lambda msg_bus, cmd: verifier_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        profil_candidat_translator=_profil_candidat_translator,
        academic_year_repository=_academic_year_repository,
        titres_acces=_titres_acces,
        questions_specifiques_translator=_question_specific_translator,
        formation_translator=_doctorat_translator,
        calendrier_inscription=CalendrierInscriptionInMemory(),
        maximum_propositions_service=_maximum_propositions_autorisees,
    ),
    VerifierProjetQuery: lambda msg_bus, cmd: verifier_projet(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        promoteur_translator=_promoteur_translator,
        questions_specifiques_translator=_question_specific_translator,
        academic_year_repository=_academic_year_repository,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    SupprimerPromoteurCommand: lambda msg_bus, cmd: supprimer_promoteur(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
        notification=_notification,
    ),
    DesignerPromoteurReferenceCommand: lambda msg_bus, cmd: designer_promoteur_reference(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
    ),
    SupprimerMembreCACommand: lambda msg_bus, cmd: supprimer_membre_CA(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
        notification=_notification,
    ),
    ApprouverPropositionCommand: lambda msg_bus, cmd: approuver_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
        notification=_notification,
    ),
    RefuserPropositionCommand: lambda msg_bus, cmd: refuser_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
        notification=_notification,
        raccrocher_experiences_curriculum=_raccrocher_experiences_curriculum,
    ),
    SoumettrePropositionCommand: lambda msg_bus, cmd: soumettre_proposition(
        msg_bus,
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        demande_repository=_demande_repository,
        profil_candidat_translator=_profil_candidat_translator,
        academic_year_repository=_academic_year_repository,
        historique=_historique,
        notification=_notification,
        titres_acces=_titres_acces,
        questions_specifiques_translator=_question_specific_translator,
        doctorat_translator=_doctorat_translator,
        calendrier_inscription=CalendrierInscriptionInMemory(),
        element_confirmation=ElementsConfirmationInMemory(),
        maximum_propositions_service=_maximum_propositions_autorisees,
        financabilite_fetcher=_financabilite_fetcher,
    ),
    DefinirCotutelleCommand: lambda msg_bus, cmd: definir_cotutelle(
        cmd,
        groupe_supervision_repository=_groupe_supervision_repository,
        proposition_repository=_proposition_repository,
        historique=_historique,
    ),
    ListerPropositionsCandidatQuery: lambda msg_bus, cmd: lister_propositions_candidat(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    ListerPropositionsSuperviseesQuery: lambda msg_bus, cmd: lister_propositions_supervisees(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
    ),
    GetPropositionCommand: lambda msg_bus, cmd: recuperer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    GetGroupeDeSupervisionCommand: lambda msg_bus, cmd: recuperer_groupe_de_supervision(
        cmd,
        groupe_supervision_repository=_groupe_supervision_repository,
    ),
    GetCotutelleCommand: lambda msg_bus, cmd: recuperer_cotutelle(
        cmd,
        groupe_supervision_repository=_groupe_supervision_repository,
    ),
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        raccrocher_experiences_curriculum=_raccrocher_experiences_curriculum,
    ),
    ApprouverPropositionParPdfCommand: lambda msg_bus, cmd: approuver_proposition_par_pdf(
        cmd,
        proposition_repository=_proposition_repository,
        groupe_supervision_repository=_groupe_supervision_repository,
        historique=_historique,
    ),
    CompleterComptabilitePropositionCommand: lambda msg_bus, cmd: completer_comptabilite_proposition(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    GetComptabiliteQuery: lambda msg_bus, cmd: recuperer_comptabilite(
        cmd,
        comptabilite_translator=_comptabilite_translator,
    ),
    ModifierTypeAdmissionCommand: lambda msg_bus, cmd: modifier_type_admission(
        cmd,
        proposition_repository=_proposition_repository,
        doctorat_translator=_doctorat_translator,
    ),
    CompleterCurriculumCommand: lambda msg_bus, cmd: completer_curriculum(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    VerifierCurriculumQuery: lambda msg_bus, cmd: verifier_curriculum(
        cmd,
        proposition_repository=_proposition_repository,
        profil_candidat_translator=_profil_candidat_translator,
        academic_year_repository=_academic_year_repository,
    ),
    RecupererElementsConfirmationQuery: lambda msg_bus, cmd: recuperer_elements_confirmation(
        cmd,
        proposition_repository=_proposition_repository,
        element_confirmation=ElementsConfirmationInMemory(),
        formation_translator=_doctorat_translator,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    RecupererResumePropositionQuery: lambda msg_bus, cmd: recuperer_resume_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        i_profil_candidat_translator=_profil_candidat_translator,
        i_comptabilite_translator=_comptabilite_translator,
        groupe_supervision_repository=_groupe_supervision_repository,
        academic_year_repository=_academic_year_repository,
        question_specifique_translator=_question_specific_translator,
    ),
    RecupererQuestionsSpecifiquesQuery: lambda msg_bus, cmd: recuperer_questions_specifiques_proposition(
        cmd,
        question_specifique_translator=_question_specific_translator,
    ),
    RecupererDocumentsPropositionQuery: lambda msg_bus, cmd: recuperer_documents_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        profil_candidat_translator=_profil_candidat_translator,
        comptabilite_translator=_comptabilite_translator,
        question_specifique_translator=_question_specific_translator,
        emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
        academic_year_repository=_academic_year_repository,
        personne_connue_translator=_personne_connue_translator,
        groupe_supervision_repository=_groupe_supervision_repository,
    ),
    RecupererDocumentsReclamesPropositionQuery: lambda msg_bus, cmd: recuperer_documents_reclames_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        profil_candidat_translator=_profil_candidat_translator,
        comptabilite_translator=_comptabilite_translator,
        question_specifique_translator=_question_specific_translator,
        emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
        academic_year_repository=_academic_year_repository,
        personne_connue_translator=_personne_connue_translator,
        groupe_supervision_repository=_groupe_supervision_repository,
    ),
    AnnulerReclamationDocumentsAuCandidatCommand: (
        lambda msg_bus, cmd: annuler_reclamation_documents_au_candidat(
            cmd,
            proposition_repository=_proposition_repository,
            emplacement_document_repository=_emplacement_document_repository,
            historique=_historique_global,
            profil_candidat_translator=_profil_candidat_translator,
            question_specifique_translator=_question_specific_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            comptabilite_translator=_comptabilite_translator,
            groupe_supervision_repository=_groupe_supervision_repository,
        )
    ),
    CompleterEmplacementsDocumentsParCandidatCommand: lambda msg_bus, cmd: (
        completer_emplacements_documents_par_candidat(
            cmd,
            proposition_repository=_proposition_repository,
            emplacement_document_repository=_emplacement_document_repository,
            historique=_historique_global,
            profil_candidat_translator=_profil_candidat_translator,
            question_specifique_translator=_question_specific_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            notification=_notification,
            comptabilite_translator=_comptabilite_translator,
            groupe_supervision_repository=_groupe_supervision_repository,
        )
    ),
    RecalculerEmplacementsDocumentsNonLibresPropositionCommand: (
        lambda msg_bus, cmd: recalculer_emplacements_documents_non_libres_proposition(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            question_specifique_translator=_question_specific_translator,
            academic_year_repository=_academic_year_repository,
            emplacement_document_repository=_emplacement_document_repository,
            comptabilite_translator=_comptabilite_translator,
            groupe_supervision_repository=_groupe_supervision_repository,
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
            classe_enumeration_onglets_checklist=OngletsChecklist,
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
    RemplirEmplacementDocumentParGestionnaireCommand: (
        lambda msg_bus, cmd: remplir_emplacement_document_par_gestionnaire(
            cmd,
            emplacement_document_repository=_emplacement_document_repository,
        )
    ),
    ReclamerDocumentsAuCandidatCommand: lambda msg_bus, cmd: reclamer_documents_au_candidat(
        cmd,
        proposition_repository=_proposition_repository,
        emplacement_document_repository=_emplacement_document_repository,
        notification=_notification,
        historique=_historique_global,
    ),
    RetyperDocumentCommand: lambda msg_bus, cmd: retyper_document(
        cmd,
        emplacement_document_repository=_emplacement_document_repository,
    ),
    ListerDemandesQuery: lambda msg_bus, cmd: lister_demandes(
        cmd,
        lister_demandes_service=_lister_demandes_service,
    ),
    RecupererPropositionGestionnaireQuery: lambda msg_bus, cmd: recuperer_proposition_gestionnaire(
        cmd,
        proposition_repository=_proposition_repository,
        unites_enseignement_translator=_unites_enseignement_translator,
    ),
    ModifierChoixFormationParGestionnaireCommand: lambda msg_bus, cmd: modifier_choix_formation_par_gestionnaire(
        msg_bus,
        cmd,
        proposition_repository=_proposition_repository,
        doctorat_translator=_doctorat_translator,
    ),
    EnvoyerMessageCandidatCommand: lambda msg_bus, cmd: envoyer_message_au_candidat(
        cmd,
        proposition_repository=_proposition_repository,
        notification=_notification,
        historique=_historique,
    ),
    RecupererResumeEtEmplacementsDocumentsPropositionQuery: (
        lambda msg_bus, cmd: recuperer_resume_et_emplacements_documents_proposition(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            comptabilite_translator=_comptabilite_translator,
            question_specifique_translator=_question_specific_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_translator,
            groupe_supervision_repository=_groupe_supervision_repository,
            unites_enseignement_translator=_unites_enseignement_translator,
        )
    ),
    RecupererPdfTemporaireDecisionSicQuery: (
        lambda msg_bus, cmd: recuperer_pdf_temporaire_decision_sic(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            campus_repository=_campus_repository,
            pdf_generation=_pdf_generation,
        )
    ),
    EnvoyerPropositionACddLorsDeLaDecisionCddCommand: (
        lambda msg_bus, cmd: envoyer_proposition_a_cdd_lors_de_la_decision_cdd(
            cmd,
            proposition_repository=_proposition_repository,
            historique=_historique,
        )
    ),
    SpecifierMotifsRefusPropositionParCDDCommand: lambda msg_bus, cmd: specifier_motifs_refus_proposition_par_cdd(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    RefuserPropositionParCddCommand: lambda msg_bus, cmd: refuser_proposition_par_cdd(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        personne_connue_ucl_translator=_personne_connue_ucl_translator,
        unites_enseignement_translator=_unites_enseignement_translator,
        pdf_generation=_pdf_generation,
    ),
    SpecifierInformationsAcceptationPropositionParCddCommand: (
        lambda msg_bus, cmd: specifier_informations_acceptation_proposition_par_cdd(
            cmd,
            proposition_repository=_proposition_repository,
        )
    ),
    ApprouverPropositionParCddCommand: lambda msg_bus, cmd: approuver_proposition_par_cdd(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        pdf_generation=_pdf_generation,
        personne_connue_ucl_translator=_personne_connue_ucl_translator,
        unites_enseignement_translator=_unites_enseignement_translator,
        titre_acces_selectionnable_repository=_titre_acces_selectionnable_repository,
        profil_candidat_translator=_profil_candidat_translator,
        academic_year_repository=_academic_year_repository,
        experience_parcours_interne_translator=_experience_parcours_interne_translator,
        groupe_supervision_repository=_groupe_supervision_repository,
        notification=_notification,
    ),
    CloturerPropositionParCddCommand: lambda msg_bus, cmd: cloturer_proposition_par_cdd(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
    ),
    PasserEtatPrisEnChargeDecisionCddCommand: lambda msg_bus, cmd: passer_etat_pris_en_charge_decision_cdd(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    PasserEtatATraiterDecisionCddCommand: lambda msg_bus, cmd: passer_etat_a_traiter_decision_cdd(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    PasserEtatACompleterParSicDecisionCddCommand: lambda msg_bus, cmd: passer_etat_a_completer_par_sic_decision_cdd(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    EnvoyerPropositionAuSicLorsDeLaDecisionCddCommand: (
        lambda msg_bus, cmd: envoyer_proposition_au_sic_lors_de_la_decision_cdd(
            cmd,
            proposition_repository=_proposition_repository,
            historique=_historique,
        )
    ),
    ModifierStatutChecklistParcoursAnterieurCommand: lambda msg_bus, cmd: modifier_statut_checklist_parcours_anterieur(
        cmd,
        proposition_repository=_proposition_repository,
        titre_acces_selectionnable_repository=_titre_acces_selectionnable_repository,
        experience_parcours_interne_translator=_experience_parcours_interne_translator,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    SpecifierConditionAccesPropositionCommand: lambda msg_bus, cmd: specifier_condition_acces_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        titre_acces_selectionnable_repository=_titre_acces_selectionnable_repository,
        experience_parcours_interne_translator=_experience_parcours_interne_translator,
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
    SpecifierFinancabiliteResultatCalculCommand: lambda msg_bus, cmd: specifier_financabilite_resultat_calcul(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    SpecifierFinancabiliteRegleCommand: lambda msg_bus, cmd: specifier_financabilite_regle(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    SpecifierFinancabiliteNonConcerneeCommand: lambda msg_bus, cmd: specifier_financabilite_non_concernee(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    ModifierStatutChecklistExperienceParcoursAnterieurCommand: (
        lambda msg_bus, cmd: modifier_statut_checklist_experience_parcours_anterieur(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            doctorat_translator=_doctorat_translator,
        )
    ),
    SpecifierInformationsAcceptationPropositionParSicCommand: (
        lambda msg_bus, cmd: specifier_informations_acceptation_proposition_par_sic(
            cmd,
            proposition_repository=_proposition_repository,
            historique=_historique,
            profil_candidat_translator=_profil_candidat_translator,
            comptabilite_translator=_comptabilite_translator,
            question_specifique_translator=_question_specific_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_ucl_translator,
            groupe_supervision_repository=_groupe_supervision_repository,
        )
    ),
    ModifierAuthentificationExperienceParcoursAnterieurCommand: (
        lambda msg_bus, cmd: modifier_authentification_experience_parcours_anterieur(
            cmd,
            proposition_repository=_proposition_repository,
            notification=_notification,
            historique=_historique,
            personne_connue_ucl_translator=_personne_connue_ucl_translator,
        )
    ),
    SpecifierMotifsRefusPropositionParSicCommand: (
        lambda msg_bus, cmd: specifier_motifs_refus_proposition_par_sic(
            cmd,
            proposition_repository=_proposition_repository,
            historique=_historique,
        )
    ),
    ApprouverAdmissionParSicCommand: (
        lambda msg_bus, cmd: approuver_admission_par_sic(
            message_bus=msg_bus,
            cmd=cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            historique=_historique,
            notification=_notification,
            pdf_generation=_pdf_generation,
            emplacement_document_repository=_emplacement_document_repository,
            comptabilite_translator=_comptabilite_translator,
            question_specifique_translator=_question_specific_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_ucl_translator,
            experience_parcours_interne_translator=_experience_parcours_interne_translator,
            matricule_etudiant_service=_matricule_etudiant_service,
            groupe_supervision_repository=_groupe_supervision_repository,
        )
    ),
    ApprouverInscriptionParSicCommand: (
        lambda msg_bus, cmd: approuver_inscription_par_sic(
            message_bus=msg_bus,
            cmd=cmd,
            proposition_repository=_proposition_repository,
            historique=_historique,
            profil_candidat_translator=_profil_candidat_translator,
            comptabilite_translator=_comptabilite_translator,
            question_specifique_translator=_question_specific_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_ucl_translator,
            experience_parcours_interne_translator=_experience_parcours_interne_translator,
            groupe_supervision_repository=_groupe_supervision_repository,
        )
    ),
    RefuserPropositionParSicCommand: lambda msg_bus, cmd: refuser_proposition_par_sic(
        cmd,
        proposition_repository=_proposition_repository,
        profil_candidat_translator=_profil_candidat_translator,
        historique=_historique,
        notification=_notification,
        pdf_generation=_pdf_generation,
        campus_repository=_campus_repository,
    ),
    EnvoyerEmailApprobationInscriptionAuCandidatCommand: (
        lambda msg_bus, cmd: envoyer_email_approbation_inscription_au_candidat(
            message_bus=msg_bus,
            cmd=cmd,
            notification=_notification,
            historique=_historique,
            matricule_etudiant_service=_matricule_etudiant_service,
        )
    ),
    SpecifierInformationsAcceptationInscriptionParSicCommand: (
        lambda msg_bus, cmd: specifier_informations_acceptation_inscription_par_sic(
            cmd,
            proposition_repository=_proposition_repository,
        )
    ),
    SpecifierDerogationFinancabiliteCommand: (
        lambda msg_bus, cmd: specifier_derogation_financabilite(
            cmd,
            proposition_repository=_proposition_repository,
            historique=_historique,
        )
    ),
    NotifierCandidatDerogationFinancabiliteCommand: (
        lambda msg_bus, cmd: notifier_candidat_derogation_financabilite(
            cmd,
            proposition_repository=_proposition_repository,
            notification=_notification,
            historique=_historique,
        )
    ),
    VerifierCurriculumApresSoumissionQuery: (
        lambda msg_bus, cmd: verifier_curriculum_apres_soumission(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            experience_parcours_interne_translator=_experience_parcours_interne_translator,
            doctorat_translator=_doctorat_translator,
        )
    ),
    VerifierExperienceCurriculumApresSoumissionQuery: (
        lambda msg_bus, cmd: verifier_experience_curriculum_apres_soumission(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            doctorat_translator=_doctorat_translator,
        )
    ),
    ModifierChecklistChoixFormationCommand: lambda msg_bus, cmd: modifier_checklist_choix_formation(
        msg_bus,
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_doctorat_translator,
    ),
    RedonnerLaMainAuCandidatCommand: lambda msg_bus, cmd: redonner_la_main_au_candidat(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        raccrocher_experiences_curriculum=_raccrocher_experiences_curriculum,
    ),
    RecupererAdmissionDoctoratQuery: lambda msg_bus, cmd: recuperer_doctorat(
        cmd,
        doctorat_repository=_doctorat_repository,
    ),
    DemanderCandidatModificationCACommand: lambda msg_bus, cmd: demander_candidat_modifier_ca(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        notification=_notification,
    ),
    SoumettreCACommand: lambda msg_bus, cmd: soumettre_ca(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        groupe_supervision_repository=_groupe_supervision_repository,
    ),
    RechercherPromoteursQuery: lambda msg_bus, cmd: rechercher_promoteurs(
        cmd,
        promoteur_translator=_promoteur_translator,
    ),
}
