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

from admission.ddd.admission.formation_continue.commands import *
from admission.ddd.admission.formation_continue.use_case.read import *
from admission.ddd.admission.formation_continue.use_case.write import *
from admission.infrastructure.admission.domain.service.in_memory.annee_inscription_formation import (
    AnneeInscriptionFormationInMemoryTranslator,
)
from admission.infrastructure.admission.domain.service.in_memory.calendrier_inscription import (
    CalendrierInscriptionInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.elements_confirmation import (
    ElementsConfirmationInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.maximum_propositions import (
    MaximumPropositionsAutoriseesInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.domain.service.in_memory.titres_acces import TitresAccesInMemory
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.comptabilite import (
    ComptabiliteInMemoryTranslator,
)
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.formation import (
    FormationContinueInMemoryTranslator,
)
from admission.infrastructure.admission.formation_continue.domain.service.in_memory.notification import (
    NotificationInMemory,
)
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)

_proposition_repository = PropositionInMemoryRepository()
_formation_continue_translator = FormationContinueInMemoryTranslator()
_annee_inscription_formation_translator = AnneeInscriptionFormationInMemoryTranslator()
_titres_acces = TitresAccesInMemory()
_profil_candidat_translator = ProfilCandidatInMemoryTranslator()
_comptabilite_translator = ComptabiliteInMemoryTranslator()
_maximum_propositions_autorisees = MaximumPropositionsAutoriseesInMemory()


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
    ),
    VerifierPropositionQuery: lambda msg_bus, cmd: verifier_proposition(
        cmd,
        proposition_repository=_proposition_repository,
        formation_translator=_formation_continue_translator,
        titres_acces=_titres_acces,
        profil_candidat_translator=_profil_candidat_translator,
        calendrier_inscription=CalendrierInscriptionInMemory(),
        maximum_propositions_service=_maximum_propositions_autorisees,
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
    CompleterComptabilitePropositionCommand: lambda msg_bus, cmd: completer_comptabilite_proposition(
        cmd,
        proposition_repository=_proposition_repository,
    ),
    GetComptabiliteQuery: lambda msg_bus, cmd: recuperer_comptabilite(
        cmd,
        comptabilite_translator=_comptabilite_translator,
    ),
    RecupererElementsConfirmationQuery: lambda msg_bus, cmd: recuperer_elements_confirmation(
        cmd,
        proposition_repository=_proposition_repository,
        element_confirmation=ElementsConfirmationInMemory(),
        formation_translator=_formation_continue_translator,
        profil_candidat_translator=_profil_candidat_translator,
    ),
}
