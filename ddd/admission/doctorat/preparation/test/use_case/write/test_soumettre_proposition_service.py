# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import mock
from django.test import TestCase

from admission.ddd.admission.doctorat.preparation.commands import (
    SoumettrePropositionCommand,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.doctorat.preparation.domain.validator.exceptions import (
    IdentificationNonCompleteeException,
)
from admission.ddd.admission.doctorat.preparation.test.factory.proposition import (
    PropositionAdmissionSC3DPConfirmeeFactory,
)
from admission.ddd.admission.domain.model.enums.authentification import (
    EtatAuthentificationParcours,
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
from admission.infrastructure.message_bus_in_memory import (
    message_bus_in_memory_instance,
)
from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from ddd.logic.financabilite.dtos.catalogue import FormationDTO
from ddd.logic.financabilite.dtos.parcours import (
    ParcoursAcademiqueExterneDTO,
    ParcoursAcademiqueInterneDTO,
    ParcoursDTO,
)
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import (
    AcademicYear,
    AcademicYearIdentity,
)
from infrastructure.financabilite.domain.service.in_memory.financabilite import (
    FinancabiliteInMemoryFetcher,
)
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import (
    AcademicYearInMemoryRepository,
)


@freezegun.freeze_time('2020-11-01')
class TestVerifierPropositionServiceCommun(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.financabilite_fetcher = FinancabiliteInMemoryFetcher()
        cls.financabilite_fetcher.save(
            ParcoursDTO(
                matricule_fgs='0123456789',
                parcours_academique_interne=ParcoursAcademiqueInterneDTO(programmes_cycles=[]),
                parcours_academique_externe=ParcoursAcademiqueExterneDTO(experiences=[]),
                annee_diplome_etudes_secondaires=2015,
                nombre_tentative_de_passer_concours_pass_et_las=0,
            )
        )
        cls.financabilite_fetcher.formations.append(
            FormationDTO(
                sigle='SC3DP',
                annee=2020,
                type=TrainingType.PHD.name,
                grade_academique='',
                credits=0,
                cycle=3,
            )
        )

    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.proposition = PropositionAdmissionSC3DPConfirmeeFactory(
            statut=ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE
        )
        self.proposition_repository.save(self.proposition)
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
            uuid_proposition=self.proposition.entity_id.uuid,
            pool=AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT.name,
            annee=2020,
            elements_confirmation=ElementsConfirmationInMemory.get_elements_for_tests(),
        )

        # Mock publish
        patcher = mock.patch('infrastructure.utils.MessageBus.publish')
        self.mock_publish = patcher.start()
        self.addCleanup(patcher.stop)

    def test_should_soumettre_proposition_etre_ok_si_admission_complete(self):
        proposition_id = self.message_bus.invoke(self.base_cmd)

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)

        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC)

        # Check the checklist values
        self.assertEqual(
            updated_proposition.checklist_initiale.donnees_personnelles.statut,
            ChoixStatutChecklist.INITIAL_CANDIDAT,
        )
        self.assertEqual(
            updated_proposition.checklist_initiale.assimilation.statut,
            ChoixStatutChecklist.INITIAL_NON_CONCERNE,
        )
        self.assertEqual(
            updated_proposition.checklist_initiale.parcours_anterieur.statut,
            ChoixStatutChecklist.INITIAL_CANDIDAT,
        )
        self.assertEqual(
            len(updated_proposition.checklist_initiale.parcours_anterieur.enfants),
            4,
        )

        experience_ids = []
        for experience_checklist in updated_proposition.checklist_initiale.parcours_anterieur.enfants:
            self.assertEqual(experience_checklist.statut, ChoixStatutChecklist.INITIAL_CANDIDAT)
            self.assertEqual(
                experience_checklist.extra,
                {
                    'identifiant': mock.ANY,
                    'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
                },
            )
            experience_ids.append(experience_checklist.extra['identifiant'])

        self.assertCountEqual(
            experience_ids,
            [
                '0cbdf4db-2454-4cbf-9e48-55d2a9881ee1',
                '9cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
                '9cbdf4db-2454-4cbf-9e48-55d2a9881ee1',
                '0cbdf4db-2454-4cbf-9e48-55d2a9881ee2',
            ],
        )

        self.assertEqual(
            updated_proposition.checklist_initiale.financabilite.statut,
            ChoixStatutChecklist.INITIAL_NON_CONCERNE,
        )
        self.assertEqual(
            updated_proposition.checklist_initiale.choix_formation.statut,
            ChoixStatutChecklist.INITIAL_CANDIDAT,
        )
        self.assertEqual(
            updated_proposition.checklist_initiale.projet_recherche.statut,
            ChoixStatutChecklist.INITIAL_CANDIDAT,
        )
        self.assertEqual(
            updated_proposition.checklist_initiale.decision_cdd.statut,
            ChoixStatutChecklist.INITIAL_CANDIDAT,
        )
        self.assertEqual(
            updated_proposition.checklist_initiale.decision_sic.statut,
            ChoixStatutChecklist.INITIAL_CANDIDAT,
        )
        self.assertEqual(updated_proposition.checklist_initiale, updated_proposition.checklist_actuelle)

    @mock.patch(
        'admission.infrastructure.admission.domain.service.in_memory.profil_candidat.ProfilCandidatInMemoryTranslator.'
        'get_identification'
    )
    def test_should_initialize_checklist_hue_candidate(self, mock_identification):
        mock_identification.return_value.pays_nationalite_europeen = False

        proposition_id = self.message_bus.invoke(self.base_cmd)

        updated_proposition = self.proposition_repository.get(proposition_id)

        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)

        self.assertEqual(
            updated_proposition.checklist_initiale.assimilation.statut,
            ChoixStatutChecklist.INITIAL_CANDIDAT,
        )

    def test_should_soumettre_proposition_etre_ok_si_preadmission_complete(self):
        proposition_id = self.message_bus.invoke(self.base_cmd)

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC)

    def test_should_soumettre_proposition_en_nettoyant_reponses_questions_specifiques(self):
        proposition = self.proposition_repository.get(self.proposition.entity_id)

        proposition.reponses_questions_specifiques = {
            '06de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
            # A default value will be set
            # '06de0c3d-3c06-4c93-8eb4-c8648f04f141': 'My response 1',
            '06de0c3d-3c06-4c93-8eb4-c8648f04f142': 'My response 2',
            '06de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
            # Will be deleted as it's a readonly element
            '06de0c3d-3c06-4c93-8eb4-c8648f04f145': 'MESSAGE',
            # Will be deleted as it's not interesting for this admission
            '36de0c3d-3c06-4c93-8eb4-c8648f04f140': 'Not interesting response 0',
            '36de0c3d-3c06-4c93-8eb4-c8648f04f141': 'Not interesting response 1',
        }

        self.proposition_repository.save(proposition)

        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(
                uuid_proposition=self.proposition.entity_id.uuid,
                pool=AcademicCalendarTypes.DOCTORATE_EDUCATION_ENROLLMENT.name,
                annee=2020,
                elements_confirmation=ElementsConfirmationInMemory.get_elements_for_tests(proposition),
            ),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)

        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionDoctorale.TRAITEMENT_FAC)
        self.maxDiff = None
        self.assertEqual(
            updated_proposition.reponses_questions_specifiques,
            {
                '06de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
                '06de0c3d-3c06-4c93-8eb4-c8648f04f141': '',
                '06de0c3d-3c06-4c93-8eb4-c8648f04f142': 'My response 2',
                '06de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
            },
        )
