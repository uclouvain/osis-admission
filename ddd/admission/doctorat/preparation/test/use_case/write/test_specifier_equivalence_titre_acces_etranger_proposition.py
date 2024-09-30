# ##############################################################################
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
# ##############################################################################
import datetime

from django.test import SimpleTestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    SpecifierEquivalenceTitreAccesEtrangerPropositionCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    PropositionNonTrouveeException,
)
from admission.ddd.admission.domain.model.enums.equivalence import (
    TypeEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    EtatEquivalenceTitreAcces,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance


class TestSpecifierEquivalenceTitreAccesEtrangerProposition(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)

        self.message_bus = message_bus_in_memory_instance

    def test_should_specifier_equivalence_titre_acces_etranger(self):
        proposition_id = self.message_bus.invoke(
            SpecifierEquivalenceTitreAccesEtrangerPropositionCommand(
                uuid_proposition='uuid-SC3DP-confirmee',
                type_equivalence_titre_acces=TypeEquivalenceTitreAcces.EQUIVALENCE_CESS.name,
                statut_equivalence_titre_acces=StatutEquivalenceTitreAcces.COMPLETE.name,
                etat_equivalence_titre_acces=EtatEquivalenceTitreAcces.DEFINITIVE.name,
                date_prise_effet_equivalence_titre_acces=datetime.date(2021, 1, 1),
                gestionnaire='0123456789',
            )
        )
        proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(proposition.type_equivalence_titre_acces, TypeEquivalenceTitreAcces.EQUIVALENCE_CESS)
        self.assertEqual(proposition.statut_equivalence_titre_acces, StatutEquivalenceTitreAcces.COMPLETE)
        self.assertEqual(proposition.etat_equivalence_titre_acces, EtatEquivalenceTitreAcces.DEFINITIVE)
        self.assertEqual(proposition.date_prise_effet_equivalence_titre_acces, datetime.date(2021, 1, 1))

    def test_should_empecher_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                SpecifierEquivalenceTitreAccesEtrangerPropositionCommand(
                    uuid_proposition='INCONNUE',
                    gestionnaire='0123456789',
                )
            )
