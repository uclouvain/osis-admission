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
from unittest import TestCase
from unittest.mock import patch

import freezegun
import mock

from admission.ddd.admission.formation_generale.commands import SoumettrePropositionCommand
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.test.factory.proposition import PropositionFactory
from admission.infrastructure.admission.domain.service.in_memory.elements_confirmation import (
    ElementsConfirmationInMemory,
)
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository
from infrastructure.shared_kernel.profil.repository.in_memory.profil import ProfilInMemoryRepository


class TestSoumettrePropositionGenerale(TestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.academic_year_repository = AcademicYearInMemoryRepository()
        self.candidat_translator = ProfilInMemoryRepository()
        self.candidat = self.candidat_translator.profil[1]

        for annee in range(2016, 2023):
            self.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

    @freezegun.freeze_time('2020-11-01')
    @mock.patch('admission.infrastructure.admission.domain.service.digit.MOCK_DIGIT_SERVICE_CALL', True)
    def test_should_soumettre_proposition_etre_ok_si_admission_complete(self):
        elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
            self.proposition_repository.get(PropositionIdentity("uuid-MASTER-SCI")),
            FormationGeneraleInMemoryTranslator(),
        )
        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(
                uuid_proposition="uuid-MASTER-SCI",
                pool=AcademicCalendarTypes.ADMISSION_POOL_VIP.name,
                annee=2021,
                elements_confirmation=elements_confirmation,
            ),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionGenerale.CONFIRMEE)
        self.assertEqual(updated_proposition.est_inscription_tardive, False)

    @freezegun.freeze_time('22/10/2020')
    @mock.patch('admission.infrastructure.admission.domain.service.digit.MOCK_DIGIT_SERVICE_CALL', True)
    def test_should_soumettre_proposition_tardive(self):
        with patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2019,
            noma_derniere_inscription_ucl='00000001',
            pays_nationalite="AR",
        ):
            proposition = PropositionFactory(
                est_bachelier_en_reorientation=True,
                formation_id__sigle="BACHELIER-ECO",
                formation_id__annee=2020,
                matricule_candidat=self.candidat.matricule,
            )

            self.proposition_repository.save(proposition)

            elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
                self.proposition_repository.get(proposition.entity_id),
                FormationGeneraleInMemoryTranslator(),
                profil_translator=self.candidat_translator,
            )

            proposition_id = self.message_bus.invoke(
                SoumettrePropositionCommand(
                    uuid_proposition=proposition.entity_id.uuid,
                    pool=AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE.name,
                    annee=2020,
                    elements_confirmation=elements_confirmation,
                ),
            )

            proposition = self.proposition_repository.get(entity_id=proposition_id)
            self.assertEqual(proposition.est_inscription_tardive, True)

    @freezegun.freeze_time('22/09/2020')
    @mock.patch('admission.infrastructure.admission.domain.service.digit.MOCK_DIGIT_SERVICE_CALL', True)
    def test_should_soumettre_proposition_non_tardive_avant_limite(self):
        with patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2019,
            noma_derniere_inscription_ucl='00000001',
            pays_nationalite="AR",
        ):
            proposition = PropositionFactory(
                est_bachelier_en_reorientation=True,
                formation_id__sigle="BACHELIER-ECO",
                formation_id__annee=2020,
                matricule_candidat=self.candidat.matricule,
            )

            self.proposition_repository.save(proposition)

            elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
                self.proposition_repository.get(proposition.entity_id),
                FormationGeneraleInMemoryTranslator(),
                profil_translator=self.candidat_translator,
            )

            proposition_id = self.message_bus.invoke(
                SoumettrePropositionCommand(
                    uuid_proposition=proposition.entity_id.uuid,
                    pool=AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE.name,
                    annee=2020,
                    elements_confirmation=elements_confirmation,
                ),
            )

            proposition = self.proposition_repository.get(entity_id=proposition_id)
            self.assertEqual(proposition.est_inscription_tardive, False)

    @freezegun.freeze_time('22/10/2020')
    @mock.patch('admission.infrastructure.admission.domain.service.digit.MOCK_DIGIT_SERVICE_CALL', True)
    def test_should_soumettre_proposition_non_tardive_pot_sans_possibilite_inscription_tardive(self):
        elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
            self.proposition_repository.get(PropositionIdentity("uuid-MASTER-SCI")),
            FormationGeneraleInMemoryTranslator(),
        )
        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(
                uuid_proposition="uuid-MASTER-SCI",
                pool=AcademicCalendarTypes.ADMISSION_POOL_VIP.name,
                annee=2020,
                elements_confirmation=elements_confirmation,
            ),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(updated_proposition.est_inscription_tardive, False)
