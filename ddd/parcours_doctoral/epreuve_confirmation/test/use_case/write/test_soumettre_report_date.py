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
import datetime

from django.test import TestCase

from admission.ddd.parcours_doctoral.epreuve_confirmation.builder.epreuve_confirmation_identity import (
    EpreuveConfirmationIdentityBuilder,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.commands import (
    RecupererEpreuvesConfirmationQuery,
    SoumettreReportDeDateCommand,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.validators.exceptions import (
    DemandeProlongationNonCompleteeException,
    EpreuveConfirmationNonTrouveeException,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestSoumettreReportDate(TestCase):
    def setUp(self):
        self.epreuve_confirmation_id = EpreuveConfirmationIdentityBuilder.build_from_uuid('c2')
        self.message_bus = message_bus_in_memory_instance

    def test_should_generer_exception_si_confirmation_inconnue(self):
        with self.assertRaises(EpreuveConfirmationNonTrouveeException):
            self.message_bus.invoke(
                SoumettreReportDeDateCommand(
                    uuid='inconnue',
                    nouvelle_echeance=datetime.date(2022, 4, 1),
                    justification_succincte='Ma raison',
                    lettre_justification=['mon_fichier_1'],
                )
            )

    def test_should_generer_exception_si_nouvelle_echeance_non_specifiee(self):
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(
                SoumettreReportDeDateCommand(
                    uuid=str(self.epreuve_confirmation_id.uuid),
                    **{
                        'nouvelle_echeance': None,
                        'justification_succincte': 'Ma raison',
                        'lettre_justification': ['mon_fichier_1'],
                    },
                )
            )
        self.assertIsInstance(e.exception.exceptions.pop(), DemandeProlongationNonCompleteeException)

    def test_should_generer_exception_si_justification_non_specifiee(self):
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(
                SoumettreReportDeDateCommand(
                    uuid=str(self.epreuve_confirmation_id.uuid),
                    **{
                        'nouvelle_echeance': datetime.date(2022, 4, 1),
                        'justification_succincte': '',
                        'lettre_justification': ['mon_fichier_1'],
                    },
                )
            )
        self.assertIsInstance(e.exception.exceptions.pop(), DemandeProlongationNonCompleteeException)

    def test_should_soumettre_report_date_si_valide(self):
        doctorat_id_resultat = self.message_bus.invoke(
            SoumettreReportDeDateCommand(
                uuid='c2',
                nouvelle_echeance=datetime.date(2022, 4, 1),
                justification_succincte='Ma raison',
                lettre_justification=['mon_fichier_1'],
            )
        )

        epreuve_confirmation_mise_a_jour = next(
            epreuve
            for epreuve in message_bus_in_memory_instance.invoke(
                RecupererEpreuvesConfirmationQuery(doctorat_uuid=doctorat_id_resultat.uuid)
            )
            if epreuve.uuid == 'c2'
        )

        self.assertIsNotNone(epreuve_confirmation_mise_a_jour.demande_prolongation)
        self.assertEqual(
            epreuve_confirmation_mise_a_jour.demande_prolongation.nouvelle_echeance,
            datetime.date(2022, 4, 1),
        )
        self.assertEqual(
            epreuve_confirmation_mise_a_jour.demande_prolongation.justification_succincte,
            'Ma raison',
        )
