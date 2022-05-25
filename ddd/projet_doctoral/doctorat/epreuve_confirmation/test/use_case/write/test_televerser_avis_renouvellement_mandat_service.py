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
from django.test import SimpleTestCase

from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.builder.epreuve_confirmation_identity import (
    EpreuveConfirmationIdentityBuilder,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.commands import (
    TeleverserAvisRenouvellementMandatRechercheCommand,
)
from admission.ddd.projet_doctoral.doctorat.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.projet_doctoral.doctorat.epreuve_confirmation.repository.in_memory.epreuve_confirmation \
    import EpreuveConfirmationInMemoryRepository


class TestTeleverserAvisRenouvellementMandatRechercheCommand(SimpleTestCase):
    def setUp(self):
        self.message_bus = message_bus_in_memory_instance

    def test_should_pas_trouver_si_epreuve_confirmation_inconnue(self):
        with self.assertRaises(EpreuveConfirmationNonTrouveeException):
            self.message_bus.invoke(
                TeleverserAvisRenouvellementMandatRechercheCommand(
                    uuid='inconnue',
                    avis_renouvellement_mandat_recherche=['mon_fichier_3'],
                )
            )

    def test_should_modifier_epreuve_confirmation_connue(self):
        epreuve_confirmation_id = EpreuveConfirmationIdentityBuilder.build_from_uuid('c2')

        self.message_bus.invoke(
            TeleverserAvisRenouvellementMandatRechercheCommand(
                uuid='c2',
                avis_renouvellement_mandat_recherche=['demande_renouvellement_bourse'],
            )
        )

        epreuve_confirmation_mise_a_jour = EpreuveConfirmationInMemoryRepository.get(
            entity_id=epreuve_confirmation_id,
        )

        self.assertEqual(
            epreuve_confirmation_mise_a_jour.avis_renouvellement_mandat_recherche,
            ['demande_renouvellement_bourse'],
        )
