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

import mock
from django.test import SimpleTestCase

from admission.ddd.projet_doctoral.preparation.commands import SoumettrePropositionCommand
from admission.ddd.projet_doctoral.preparation.domain.model._enums import (
    ChoixStatutProposition,
)
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import IdentificationNonCompleteeException
from admission.ddd.projet_doctoral.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
    PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from admission.infrastructure.projet_doctoral.preparation.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.projet_doctoral.preparation.repository.in_memory.groupe_de_supervision import (
    GroupeDeSupervisionInMemoryRepository,
)
from admission.infrastructure.projet_doctoral.preparation.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


class TestVerifierPropositionServiceCommun(SimpleTestCase):
    def setUp(self) -> None:
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.proposition_repository = PropositionInMemoryRepository()
        self.groupe_supervision_repository = GroupeDeSupervisionInMemoryRepository()
        self.current_candidat = self.candidat_translator.profil_candidats[0]
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

        # Mock datetime to return the 2020 year as the current year
        for date_patch in [
            'admission.ddd.projet_doctoral.preparation.use_case.write.soumettre_proposition_service.datetime',
            'admission.ddd.projet_doctoral.preparation.domain.model.proposition.datetime',
        ]:
            patcher = mock.patch(date_patch)
            self.addCleanup(patcher.stop)
            self.mock_foo = patcher.start()
            self.today_date = datetime.date(2020, 11, 1)
            self.mock_foo.date.today.return_value = self.today_date

    def test_should_soumettre_proposition_etre_ok_si_admission_complete(self):
        proposition = PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory()

        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(uuid_proposition=proposition.entity_id.uuid),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutProposition.SUBMITTED)
        self.assertEqual(updated_proposition.date_soumission_admission, self.today_date)
        self.assertIsNone(updated_proposition.date_soumission_pre_admission)

    def test_should_soumettre_proposition_etre_ok_si_preadmission_complete(self):
        proposition = PropositionPreAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory()

        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(uuid_proposition=proposition.entity_id.uuid),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutProposition.SUBMITTED)
        self.assertEqual(updated_proposition.date_soumission_pre_admission, self.today_date)
        self.assertIsNone(updated_proposition.date_soumission_admission)

    def test_should_retourner_erreur_si_identification_non_completee(self):
        with mock.patch.multiple(self.current_candidat, prenom=''):
            proposition = PropositionAdmissionSC3DPAvecPromoteursEtMembresCADejaApprouvesFactory()

            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(
                    self.message_bus.invoke(
                        SoumettrePropositionCommand(uuid_proposition=proposition.entity_id.uuid),
                    )
                )
            self.assertIsInstance(context.exception.exceptions.pop(), IdentificationNonCompleteeException)
