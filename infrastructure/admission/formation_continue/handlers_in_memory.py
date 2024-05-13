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
from admission.ddd.admission.formation_continue.use_case.write.annuler_proposition_service import (
    annuler_proposition,
)
from admission.ddd.admission.formation_continue.use_case.write.approuver_par_fac_service import (
    approuver_par_fac,
)
from admission.ddd.admission.formation_continue.use_case.write.cloturer_proposition_service import (
    cloturer_proposition,
)
from admission.ddd.admission.formation_continue.use_case.write.mettre_en_attente_service import (
    mettre_en_attente,
)
from admission.ddd.admission.formation_continue.use_case.write.refuser_proposition_service import (
    refuser_proposition,
)
from admission.ddd.admission.formation_continue.use_case.write.valider_proposition_service import (
    valider_proposition,
)
from admission.ddd.admission.use_case.read import recuperer_questions_specifiques_proposition
from admission.infrastructure.admission.domain.service.in_memory.annee_inscription_formation import (
    AnneeInscriptionFormationInMemoryTranslator,
)
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
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.domain.service.in_memory.recuperer_documents_proposition import (
    EmplacementsDocumentsPropositionInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.titres_acces import TitresAccesInMemory
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.formation import (
    FormationContinueInMemoryTranslator,
)
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.historique import HistoriqueInMemory
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.lister_demandes import (
    ListerDemandesInMemory,
)
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.notification import (
    NotificationInMemory,
)
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.question_specifique import (
    QuestionSpecifiqueInMemoryTranslator,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from infrastructure.shared_kernel.personne_connue_ucl.in_memory.personne_connue_ucl import (
    PersonneConnueUclInMemoryTranslator,
)

_proposition_repository = PropositionInMemoryRepository()
_formation_continue_translator = FormationContinueInMemoryTranslator()
_annee_inscription_formation_translator = AnneeInscriptionFormationInMemoryTranslator()
_titres_acces = TitresAccesInMemory()
_profil_candidat_translator = ProfilCandidatInMemoryTranslator()
_question_specific_translator = QuestionSpecifiqueInMemoryTranslator()
_maximum_propositions_autorisees = MaximumPropositionsAutoriseesInMemory()
_academic_year_repository = AcademicYearInMemoryRepository()
_emplacements_documents_demande_translator = EmplacementsDocumentsPropositionInMemoryTranslator()
_personne_connue_ucl_translator = PersonneConnueUclInMemoryTranslator()
_historique = HistoriqueInMemory()
_historique_global = HistoriqueGlobalInMemory()
_notification = NotificationInMemory()
_lister_demandes_service = ListerDemandesInMemory()


COMMAND_HANDLERS = {
    RechercherFormationContinueQuery: lambda msg_bus, cmd: rechercher_formations(
        cmd,
        formation_continue_translator=_formation_continue_translator,
        annee_inscription_formation_translator=_annee_inscription_formation_translator,
    ),
    InitierPropositionCommand: lambda msg_bus, cmd: initier_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_continue_translator,
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
        formation_translator=_formation_continue_translator,
    ),
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique_global,
    ),
    VerifierPropositionQuery: lambda msg_bus, cmd: verifier_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_continue_translator,
        titres_acces=_titres_acces,
        profil_candidat_translator=_profil_candidat_translator,
        calendrier_inscription=CalendrierInscriptionInMemory(),
        maximum_propositions_service=_maximum_propositions_autorisees,
        questions_specifiques_translator=_question_specific_translator,
    ),
    SoumettrePropositionCommand: lambda msg_bus, cmd: soumettre_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_continue_translator,
        titres_acces=_titres_acces,
        profil_candidat_translator=_profil_candidat_translator,
        calendrier_inscription=CalendrierInscriptionInMemory(),
        element_confirmation=ElementsConfirmationInMemory(),
        notification=NotificationInMemory(),
        maximum_propositions_service=_maximum_propositions_autorisees,
        questions_specifiques_translator=_question_specific_translator,
        historique=_historique_global,
    ),
    CompleterCurriculumCommand: lambda msg_bus, cmd: completer_curriculum(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    DeterminerAnneeAcademiqueEtPotQuery: lambda msg_bus, cmd: determiner_annee_academique_et_pot(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_continue_translator,
        titres_acces=_titres_acces,
        profil_candidat_translator=_profil_candidat_translator,
        calendrier_inscription=CalendrierInscriptionInMemory(),
    ),
    RecupererElementsConfirmationQuery: lambda msg_bus, cmd: recuperer_elements_confirmation(
        cmd,
        proposition_repository=_proposition_repository,
        element_confirmation=ElementsConfirmationInMemory(),
        formation_translator=_formation_continue_translator,
        profil_candidat_translator=_profil_candidat_translator,
    ),
    CompleterQuestionsSpecifiquesCommand: lambda msg_bus, cmd: completer_questions_specifiques(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    RecupererResumePropositionQuery: lambda msg_bus, cmd: recuperer_resume_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        i_profil_candidat_translator=_profil_candidat_translator,
        academic_year_repository=_academic_year_repository,
    ),
    RecupererQuestionsSpecifiquesQuery: lambda msg_bus, cmd: recuperer_questions_specifiques_proposition(
        cmd,
        question_specifique_translator=_question_specific_translator,
    ),
    RecupererDocumentsPropositionQuery: lambda msg_bus, cmd: recuperer_documents_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        profil_candidat_translator=_profil_candidat_translator,
        question_specifique_translator=_question_specific_translator,
        emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
        academic_year_repository=_academic_year_repository,
        personne_connue_translator=_personne_connue_ucl_translator,
    ),
    RecupererResumeEtEmplacementsDocumentsNonLibresPropositionQuery: (
        lambda msg_bus, cmd: recuperer_resume_et_emplacements_documents_non_libres_proposition(
            cmd,
            proposition_repository=_proposition_repository,
            profil_candidat_translator=_profil_candidat_translator,
            emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
            academic_year_repository=_academic_year_repository,
            personne_connue_translator=_personne_connue_ucl_translator,
            question_specifique_translator=_question_specific_translator,
        )
    ),
    ListerDemandesQuery: lambda msg_bus, cmd: lister_demandes(
        cmd,
        lister_demandes_service=_lister_demandes_service,
    ),
    MettreEnAttenteCommand: lambda msg_bus, cmd: mettre_en_attente(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        notification=_notification,
    ),
    ApprouverParFacCommand: lambda msg_bus, cmd: approuver_par_fac(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        notification=_notification,
    ),
    RefuserPropositionCommand: lambda msg_bus, cmd: refuser_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        notification=_notification,
    ),
    AnnulerPropositionCommand: lambda msg_bus, cmd: annuler_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        notification=_notification,
    ),
    ValiderPropositionCommand: lambda msg_bus, cmd: valider_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
        notification=_notification,
    ),
    CloturerPropositionCommand: lambda msg_bus, cmd: cloturer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
    ),
}
