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
from django.test import TestCase

from admission.ddd.parcours_doctoral.epreuve_confirmation.builder.epreuve_confirmation_identity import (
    EpreuveConfirmationIdentityBuilder,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.commands import (
    CompleterEpreuveConfirmationParPromoteurCommand,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonTrouveeException,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.parcours_doctoral.epreuve_confirmation.repository.in_memory import (
    epreuve_confirmation,
)


class TestCompleterEpreuveConfirmationParPromoteur(TestCase):
    def setUp(self):
        self.epreuve_confirmation_id = EpreuveConfirmationIdentityBuilder.build_from_uuid('c2')
        self.message_bus = message_bus_in_memory_instance

    def test_should_generer_exception_si_confirmation_inconnue(self):
        with self.assertRaises(EpreuveConfirmationNonTrouveeException):
            self.message_bus.invoke(
                CompleterEpreuveConfirmationParPromoteurCommand(
                    uuid='inconnue',
                    proces_verbal_ca=['mon_fichier_2'],
                    avis_renouvellement_mandat_recherche=['mon_fichier_3'],
                )
            )

    def test_should_completer_epreuve_confirmation_si_valide(self):
        doctorat_id_resultat = self.message_bus.invoke(
            CompleterEpreuveConfirmationParPromoteurCommand(
                uuid='c2',
                proces_verbal_ca=['mon_fichier_4'],
                avis_renouvellement_mandat_recherche=['mon_fichier_5'],
            )
        )

        epreuve_confirmation_mise_a_jour = epreuve_confirmation.EpreuveConfirmationInMemoryRepository.get(
            entity_id=self.epreuve_confirmation_id,
        )

        self.assertEqual(epreuve_confirmation_mise_a_jour.doctorat_id, doctorat_id_resultat)
        self.assertEqual(epreuve_confirmation_mise_a_jour.proces_verbal_ca, ['mon_fichier_4'])
        self.assertEqual(epreuve_confirmation_mise_a_jour.avis_renouvellement_mandat_recherche, ['mon_fichier_5'])
