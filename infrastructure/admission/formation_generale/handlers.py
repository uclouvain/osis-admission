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
from admission.infrastructure.admission.domain.service.elements_confirmation import ElementsConfirmation
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from admission.infrastructure.admission.domain.service.bourse import BourseTranslator
from admission.infrastructure.admission.domain.service.calendrier_inscription import CalendrierInscription
from admission.infrastructure.admission.domain.service.maximum_propositions import MaximumPropositionsAutorisees
from admission.infrastructure.admission.domain.service.profil_candidat import ProfilCandidatTranslator
from admission.infrastructure.admission.domain.service.titres_acces import TitresAcces
from admission.infrastructure.admission.formation_generale.domain.service.comptabilite import ComptabiliteTranslator
from admission.infrastructure.admission.formation_generale.domain.service.formation import FormationGeneraleTranslator
from admission.infrastructure.admission.formation_generale.domain.service.notification import Notification
from admission.infrastructure.admission.formation_generale.domain.service.question_specifique import (
    QuestionSpecifiqueTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.proposition import PropositionRepository
from infrastructure.shared_kernel.academic_year.repository.academic_year import AcademicYearRepository

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
    SupprimerPropositionCommand: lambda msg_bus, cmd: supprimer_proposition(
        cmd,
        proposition_repository=PropositionRepository(),
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
}
