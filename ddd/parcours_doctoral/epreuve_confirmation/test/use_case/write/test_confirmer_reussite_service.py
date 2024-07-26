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
from django.test import TestCase

from admission.ddd.parcours_doctoral.commands import RecupererAdmissionDoctoratQuery
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.parcours_doctoral.epreuve_confirmation.commands import (
    ConfirmerReussiteCommand,
)
from admission.ddd.parcours_doctoral.epreuve_confirmation.validators.exceptions import (
    EpreuveConfirmationNonCompleteePourEvaluationException,
    EpreuveConfirmationNonTrouveeException,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions


class TestConfirmerReussite(TestCase):
    def setUp(self):
        self.message_bus = message_bus_in_memory_instance

    def test_should_generer_exception_si_confirmation_inconnue(self):
        with self.assertRaises(EpreuveConfirmationNonTrouveeException):
            self.message_bus.invoke(ConfirmerReussiteCommand(uuid='inconnue'))

    def test_should_generer_exception_si_date_epreuve_confirmation_non_specifiee(self):
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(ConfirmerReussiteCommand(uuid='c1'))
        self.assertIsInstance(e.exception.exceptions.pop(), EpreuveConfirmationNonCompleteePourEvaluationException)

    def test_should_generer_exception_si_proces_verbal_non_specifie(self):
        with self.assertRaises(MultipleBusinessExceptions) as e:
            self.message_bus.invoke(ConfirmerReussiteCommand(uuid='c0'))
        self.assertIsInstance(e.exception.exceptions.pop(), EpreuveConfirmationNonCompleteePourEvaluationException)

    def test_should_confirmer_reussite_epreuve_confirmation_si_valide(self):
        doctorat_id = self.message_bus.invoke(ConfirmerReussiteCommand(uuid='c2'))

        doctorat = self.message_bus.invoke(
            RecupererAdmissionDoctoratQuery(doctorat_uuid=doctorat_id.uuid),
        )

        self.assertEqual(doctorat.statut, ChoixStatutDoctorat.PASSED_CONFIRMATION.name)
