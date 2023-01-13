# ##############################################################################
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
# ##############################################################################
from unittest import TestCase, mock

from admission.ddd.admission.domain.validator.exceptions import (
    ConditionsAccessNonRempliesException,
    NombrePropositionsSoumisesDepasseException,
)
from admission.ddd.admission.formation_continue.commands import VerifierPropositionQuery
from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutProposition
from admission.infrastructure.admission.formation_continue.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestVerifierPropositionService(TestCase):
    def assertHasInstance(self, container, cls, msg=None):
        if not any(isinstance(obj, cls) for obj in container):
            self.fail(msg or f"No instance of '{cls}' has been found")

    def setUp(self) -> None:
        self.message_bus = message_bus_in_memory_instance
        self.proposition_repository = PropositionInMemoryRepository
        self.addCleanup(self.proposition_repository.reset)

    def test_should_verifier_etre_ok_si_complet(self):
        proposition_id = self.message_bus.invoke(VerifierPropositionQuery(uuid_proposition="uuid-ECGE3DP"))
        self.assertEqual(proposition_id.uuid, "uuid-ECGE3DP")

    def test_should_retourner_erreur_si_conditions_acces_non_remplies(self):
        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(VerifierPropositionQuery(uuid_proposition='uuid-SC3DP'))
        self.assertHasInstance(context.exception.exceptions, ConditionsAccessNonRempliesException)

    def test_should_verification_renvoyer_erreur_si_trop_de_demandes_envoyees(self):
        propositions = self.proposition_repository.search(matricule_candidat='0123456789')
        for proposition in propositions:
            proposition.statut = ChoixStatutProposition.IN_PROGRESS

        for proposition_index in range(2):
            propositions[proposition_index].statut = ChoixStatutProposition.SUBMITTED

        with self.assertRaises(MultipleBusinessExceptions) as context:
            self.message_bus.invoke(VerifierPropositionQuery(uuid_proposition=propositions[2].entity_id.uuid))

        self.assertHasInstance(context.exception.exceptions, NombrePropositionsSoumisesDepasseException)
