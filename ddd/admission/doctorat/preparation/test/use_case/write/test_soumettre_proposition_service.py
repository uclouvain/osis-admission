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

import attr
import freezegun
import mock
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import SoumettrePropositionCommand
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import IdentificationNonCompleteeException
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.admission.doctorat.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.domain.service.in_memory.elements_confirmation import (
    ElementsConfirmationInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


@freezegun.freeze_time('2020-11-01')
class TestVerifierPropositionServiceCommun(TestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance

        self.academic_year_repository = AcademicYearInMemoryRepository()

        for annee in range(2016, 2021):
            self.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

        self.base_cmd = SoumettrePropositionCommand(
            uuid_proposition='',
            pool=AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT.name,
            annee=2020,
            elements_confirmation=ElementsConfirmationInMemory.get_elements_for_tests(),
        )

    @mock.patch('admission.infrastructure.admission.domain.service.digit.MOCK_DIGIT_SERVICE_CALL', True)
    def test_should_soumettre_proposition_etre_ok_si_admission_complete(self):
        proposition = PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory()

        proposition_id = self.message_bus.invoke(
            attr.evolve(self.base_cmd, uuid_proposition=proposition.entity_id.uuid),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionDoctorale.CONFIRMEE)

    def test_should_soumettre_proposition_etre_ok_si_preadmission_complete(self):
        proposition = PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory()

        proposition_id = self.message_bus.invoke(
            attr.evolve(self.base_cmd, uuid_proposition=proposition.entity_id.uuid),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionDoctorale.CONFIRMEE)

    def test_should_retourner_erreur_si_identification_non_completee(self):
        with mock.patch.multiple(ProfilCandidatInMemoryTranslator.profil_candidats[0], pays_naissance=''):
            proposition = PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory()

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(
                    attr.evolve(self.base_cmd, uuid_proposition=proposition.entity_id.uuid),
                )
            self.assertIsInstance(context.exception.exceptions.pop(), IdentificationNonCompleteeException)
