# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

import mock
from django.test import SimpleTestCase

from admission.ddd.admission.formation_generale.commands import ModifierChecklistStatutExamenCommand
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    ExamenNonCompletesException,
    PropositionNonTrouveeException,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.modifier_checklist_experience_parcours_anterieur import (
    ValidationExperienceParcoursAnterieurInMemoryService,
)
from admission.infrastructure.admission.shared_kernel.domain.service.in_memory.profil_candidat import (
    ProfilCandidatInMemoryTranslator,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from ddd.logic.shared_kernel.profil.dtos.examens import ExamenDTO
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience


class TestModifierStatutChecklistExamen(SimpleTestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.proposition_identity = PropositionIdentity(uuid='uuid-MASTER-SCI-CONFIRMED')
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.validation_experience_service = ValidationExperienceParcoursAnterieurInMemoryService()
        self.mock_examen_dto = ExamenDTO(
            uuid=str(uuid.uuid4()),
            requis=True,
            titre='Title',
            attestation=['uuid-attestation'],
            annee=2020,
            formations=[],
        )
        self.mock_exam_path = (
            'admission.infrastructure.admission.shared_kernel.domain.service.in_memory.profil_candidat.'
            'ProfilCandidatInMemoryTranslator.get_examen'
        )

    def test_should_verifier_examen_complet_pour_passage_a_valide(self):
        with mock.patch(
            self.mock_exam_path,
            return_value=ExamenDTO(
                uuid='uuid',
                requis=True,
                titre='Title',
                attestation=['uuid-attestation'],
                annee=None,
                formations=[],
            ),
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                self.message_bus.invoke(
                    ModifierChecklistStatutExamenCommand(
                        uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                        uuid_experience=self.mock_examen_dto.uuid,
                        statut=ChoixStatutValidationExperience.VALIDEE.name,
                        gestionnaire='0123456789',
                    )
                )

            self.assertIsInstance(
                context.exception.exceptions.pop(),
                ExamenNonCompletesException,
            )

        with mock.patch(
            self.mock_exam_path,
            return_value=ExamenDTO(
                uuid='uuid',
                requis=True,
                titre='Title',
                attestation=[],
                annee=2025,
                formations=[],
            ),
        ):
            with self.assertRaises(MultipleBusinessExceptions) as context:
                proposition_id = self.message_bus.invoke(
                    ModifierChecklistStatutExamenCommand(
                        uuid_proposition='uuid-MASTER-SCI-CONFIRMED',
                        uuid_experience=self.mock_examen_dto.uuid,
                        statut=ChoixStatutValidationExperience.VALIDEE.name,
                        gestionnaire='0123456789',
                    )
                )

                self.assertEqual(proposition_id, self.proposition_identity)

            self.assertIsInstance(
                context.exception.exceptions.pop(),
                ExamenNonCompletesException,
            )

    def test_should_empecher_si_proposition_non_trouvee(self):
        with self.assertRaises(PropositionNonTrouveeException):
            self.message_bus.invoke(
                ModifierChecklistStatutExamenCommand(
                    uuid_proposition='INCONNUE',
                    uuid_experience=self.mock_examen_dto.uuid,
                    statut=ChoixStatutValidationExperience.A_COMPLETER.name,
                    gestionnaire='0123456789',
                )
            )
