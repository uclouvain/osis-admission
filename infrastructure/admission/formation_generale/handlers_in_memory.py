##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.use_case.read import recuperer_questions_specifiques_demande
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
from admission.infrastructure.admission.domain.service.in_memory.historique import HistoriqueInMemory
from admission.infrastructure.admission.domain.service.in_memory.maximum_propositions import (
    MaximumPropositionsAutoriseesInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.domain.service.in_memory.recuperer_documents_demande import (
    RecupererDocumentsDemandeInMemoryTranslator, EmplacementsDocumentsDemandeInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.titres_acces import TitresAccesInMemory
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.comptabilite import (
    ComptabiliteInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.inscription_tardive import (
    InscriptionTardiveInMemory,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.notification import (
    NotificationInMemory,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.question_specifique import (
    QuestionSpecifiqueInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.repository.in_memory.emplacement_document import (
    EmplacementDocumentInMemoryRepository,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository

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
_historique = HistoriqueInMemory()
_emplacements_documents_demande_translator = EmplacementsDocumentsDemandeInMemoryTranslator()
_emplacement_document_repository = EmplacementDocumentInMemoryRepository()


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
        historique=_historique,
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
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        historique=_historique,
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
        notification=NotificationInMemory(),
        maximum_propositions_service=_maximum_propositions_autorisees,
        inscription_tardive_service=InscriptionTardiveInMemory(),
        historique=_historique,
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
    ),
    RecupererDocumentsDemandeQuery: lambda msg_bus, cmd: recuperer_documents_demande(
        cmd,
        proposition_repository=_proposition_repository,
        profil_candidat_translator=_profil_candidat_translator,
        comptabilite_translator=_comptabilite_translator,
        question_specifique_translator=_question_specific_translator,
        emplacements_documents_demande_translator=_emplacements_documents_demande_translator,
        academic_year_repository=_academic_year_repository,
    ),
    RecupererQuestionsSpecifiquesQuery: lambda msg_bus, cmd: recuperer_questions_specifiques_demande(
        cmd,
        question_specifique_translator=_question_specific_translator,
    ),
    DeterminerEmplacementsDocumentsDemandeCommand: lambda msg_bus, cmd: determiner_emplacements_documents_demande(
        cmd,
        proposition_repository=_proposition_repository,
        profil_candidat_translator=_profil_candidat_translator,
        comptabilite_translator=_comptabilite_translator,
        question_specifique_translator=_question_specific_translator,
        academic_year_repository=_academic_year_repository,
        emplacement_document_repository=_emplacement_document_repository,
    ),
}
