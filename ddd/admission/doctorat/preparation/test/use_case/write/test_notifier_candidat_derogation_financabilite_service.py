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

import freezegun
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    NotifierCandidatDerogationFinancabiliteCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import DerogationFinancement
from admission.ddd.admission.doctorat.preparation.domain.model.proposition import PropositionIdentity
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


@freezegun.freeze_time('2020-11-01')
class TestNotifierCandidatDerogationFinancabilite(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.academic_year_repository = AcademicYearInMemoryRepository()
        for annee in range(2016, 2023):
            cls.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )
        cls.message_bus = message_bus_in_memory_instance

    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.candidat = self.candidat_translator.profil_candidats[1]
        self.proposition = self.proposition_repository.get(
            PropositionIdentity(
                uuid='uuid-SC3DP-confirmee',
            ),
        )

    def test_should_notifier_candidat_etre_ok(self):
        command = NotifierCandidatDerogationFinancabiliteCommand(
            uuid_proposition='uuid-SC3DP-confirmee',
            gestionnaire='0123456789',
            objet_message='foo',
            corps_message='bar',
        )

        proposition_id = self.message_bus.invoke(command)

        proposition = self.proposition_repository.get(proposition_id)

        # Résultat de la commande
        self.assertEqual(proposition_id.uuid, proposition.entity_id.uuid)

        # Proposition mise à jour
        self.assertEqual(proposition.financabilite_derogation_statut, DerogationFinancement.CANDIDAT_NOTIFIE)
