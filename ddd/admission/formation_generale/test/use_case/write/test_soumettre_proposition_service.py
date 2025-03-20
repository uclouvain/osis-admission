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
from unittest.mock import patch

import freezegun
import mock
from django.test import TestCase

from admission.ddd.admission.formation_generale.commands import SoumettrePropositionCommand
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutPropositionGenerale
from admission.ddd.admission.formation_generale.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.formation_generale.test.factory.proposition import PropositionFactory
from admission.infrastructure.admission.domain.service.in_memory.elements_confirmation import (
    ElementsConfirmationInMemory,
)
from admission.infrastructure.admission.domain.service.in_memory.profil_candidat import ProfilCandidatInMemoryTranslator
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.formation import (
    FormationGeneraleInMemoryTranslator,
)
from admission.infrastructure.admission.formation_generale.repository.in_memory.proposition import (
    PropositionInMemoryRepository,
)
from admission.infrastructure.message_bus_in_memory import message_bus_in_memory_instance
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from ddd.logic.financabilite.dtos.catalogue import FormationDTO
from ddd.logic.financabilite.dtos.parcours import (
    ParcoursDTO,
    ParcoursAcademiqueInterneDTO,
    ParcoursAcademiqueExterneDTO,
)
from ddd.logic.shared_kernel.academic_year.domain.model.academic_year import AcademicYear, AcademicYearIdentity
from infrastructure.financabilite.domain.service.in_memory.financabilite import FinancabiliteInMemoryFetcher
from infrastructure.shared_kernel.academic_year.repository.in_memory.academic_year import AcademicYearInMemoryRepository


class TestSoumettrePropositionGenerale(TestCase):
    def setUp(self) -> None:
        self.proposition_repository = PropositionInMemoryRepository()
        self.addCleanup(self.proposition_repository.reset)
        self.message_bus = message_bus_in_memory_instance
        self.academic_year_repository = AcademicYearInMemoryRepository()
        self.candidat_translator = ProfilCandidatInMemoryTranslator()
        self.candidat = self.candidat_translator.profil_candidats[1]
        self.financabilite_fetcher = FinancabiliteInMemoryFetcher()
        self.addCleanup(self.financabilite_fetcher.reset)

        for annee in range(2016, 2026):
            self.academic_year_repository.save(
                AcademicYear(
                    entity_id=AcademicYearIdentity(year=annee),
                    start_date=datetime.date(annee, 9, 15),
                    end_date=datetime.date(annee + 1, 9, 30),
                )
            )

        # Mock publish
        patcher = mock.patch(
            'infrastructure.utils.MessageBus.publish',
        )
        self.mock_publish = patcher.start()
        self.addCleanup(patcher.stop)

    @freezegun.freeze_time('2023-11-01')
    def test_should_soumettre_proposition_etre_ok_si_admission_complete(self):
        elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
            self.proposition_repository.get(PropositionIdentity("uuid-MASTER-SCI")),
            FormationGeneraleInMemoryTranslator(),
        )
        self.financabilite_fetcher.save(
            ParcoursDTO(
                matricule_fgs='0000000001',
                parcours_academique_interne=ParcoursAcademiqueInterneDTO(programmes_cycles=[]),
                parcours_academique_externe=ParcoursAcademiqueExterneDTO(experiences=[]),
                annee_diplome_etudes_secondaires=2015,
                nombre_tentative_de_passer_concours_pass_et_las=0,
            )
        )
        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(
                uuid_proposition="uuid-BACHELIER-FINANCABILITE",
                pool=AcademicCalendarTypes.ADMISSION_POOL_VIP.name,
                annee=2024,
                elements_confirmation=elements_confirmation,
            ),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)

        # Command result
        self.assertEqual(proposition_id.uuid, updated_proposition.entity_id.uuid)
        # Updated proposition
        self.assertEqual(updated_proposition.statut, ChoixStatutPropositionGenerale.CONFIRMEE)
        self.assertEqual(updated_proposition.est_inscription_tardive, False)
        self.assertEqual(updated_proposition.auteur_derniere_modification, self.candidat.matricule)

    @freezegun.freeze_time('22/10/2024')
    def test_should_soumettre_proposition_tardive(self):
        with patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2023,
            noma_derniere_inscription_ucl='00000001',
            pays_nationalite="AR",
        ):
            proposition = PropositionFactory(
                est_bachelier_en_reorientation=True,
                formation_id__sigle="ABCD2MC",
                formation_id__annee=2024,
                curriculum=['file1.pdf'],
                matricule_candidat=self.candidat.matricule,
                bourse_double_diplome_id=None,
                bourse_internationale_id=None,
                bourse_erasmus_mundus_id=None,
            )

            self.proposition_repository.save(proposition)

            self.financabilite_fetcher.save(
                ParcoursDTO(
                    matricule_fgs=proposition.matricule_candidat,
                    parcours_academique_interne=ParcoursAcademiqueInterneDTO(programmes_cycles=[]),
                    parcours_academique_externe=ParcoursAcademiqueExterneDTO(experiences=[]),
                    annee_diplome_etudes_secondaires=2015,
                    nombre_tentative_de_passer_concours_pass_et_las=0,
                )
            )

            elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
                self.proposition_repository.get(proposition.entity_id),
                FormationGeneraleInMemoryTranslator(),
                profil_translator=self.candidat_translator,
            )

            proposition_id = self.message_bus.invoke(
                SoumettrePropositionCommand(
                    uuid_proposition=proposition.entity_id.uuid,
                    pool=AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE.name,
                    annee=2024,
                    elements_confirmation=elements_confirmation,
                ),
            )

            proposition = self.proposition_repository.get(entity_id=proposition_id)
            self.assertEqual(proposition.est_inscription_tardive, True)

    @freezegun.freeze_time('22/09/2024')
    def test_should_soumettre_proposition_non_tardive_avant_limite(self):
        with patch.multiple(
            self.candidat,
            annee_derniere_inscription_ucl=2023,
            noma_derniere_inscription_ucl='00000001',
            pays_nationalite="AR",
        ):
            proposition = PropositionFactory(
                est_bachelier_en_reorientation=True,
                formation_id__sigle="ABCD2MC",
                formation_id__annee=2024,
                matricule_candidat=self.candidat.matricule,
                curriculum=['file1.pdf'],
                bourse_double_diplome_id=None,
                bourse_internationale_id=None,
                bourse_erasmus_mundus_id=None,
            )

            self.proposition_repository.save(proposition)

            self.financabilite_fetcher.save(
                ParcoursDTO(
                    matricule_fgs=proposition.matricule_candidat,
                    parcours_academique_interne=ParcoursAcademiqueInterneDTO(programmes_cycles=[]),
                    parcours_academique_externe=ParcoursAcademiqueExterneDTO(experiences=[]),
                    annee_diplome_etudes_secondaires=2015,
                    nombre_tentative_de_passer_concours_pass_et_las=0,
                )
            )

            elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
                self.proposition_repository.get(proposition.entity_id),
                FormationGeneraleInMemoryTranslator(),
                profil_translator=self.candidat_translator,
            )

            proposition_id = self.message_bus.invoke(
                SoumettrePropositionCommand(
                    uuid_proposition=proposition.entity_id.uuid,
                    pool=AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE.name,
                    annee=2024,
                    elements_confirmation=elements_confirmation,
                ),
            )

            proposition = self.proposition_repository.get(entity_id=proposition_id)
            self.assertEqual(proposition.est_inscription_tardive, False)

    @freezegun.freeze_time('22/10/2024')
    def test_should_soumettre_proposition_non_tardive_pot_sans_possibilite_inscription_tardive(self):
        elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
            self.proposition_repository.get(PropositionIdentity("uuid-MASTER-SCI")),
            FormationGeneraleInMemoryTranslator(),
        )
        self.financabilite_fetcher.save(
            ParcoursDTO(
                matricule_fgs='0000000001',
                parcours_academique_interne=ParcoursAcademiqueInterneDTO(programmes_cycles=[]),
                parcours_academique_externe=ParcoursAcademiqueExterneDTO(experiences=[]),
                annee_diplome_etudes_secondaires=2015,
                nombre_tentative_de_passer_concours_pass_et_las=0,
            )
        )
        proposition_id = self.message_bus.invoke(
            SoumettrePropositionCommand(
                uuid_proposition="uuid-BACHELIER-FINANCABILITE",
                pool=AcademicCalendarTypes.ADMISSION_POOL_VIP.name,
                annee=2024,
                elements_confirmation=elements_confirmation,
            ),
        )

        updated_proposition = self.proposition_repository.get(proposition_id)
        self.assertEqual(updated_proposition.est_inscription_tardive, False)

    @freezegun.freeze_time('22/09/2021')
    def test_should_soumettre_proposition_en_nettoyant_reponses_questions_specifiques(self):
        proposition = self.proposition_repository.get(PropositionIdentity("uuid-MASTER-SCI"))

        elements_confirmation = ElementsConfirmationInMemory.get_elements_for_tests(
            proposition,
            FormationGeneraleInMemoryTranslator(),
        )

        self.financabilite_fetcher.save(
            ParcoursDTO(
                matricule_fgs='0000000001',
                parcours_academique_interne=ParcoursAcademiqueInterneDTO(programmes_cycles=[]),
                parcours_academique_externe=ParcoursAcademiqueExterneDTO(experiences=[]),
                annee_diplome_etudes_secondaires=2015,
                nombre_tentative_de_passer_concours_pass_et_las=0,
            )
        )

        self.financabilite_fetcher.formations.append(
            FormationDTO(
                sigle='MASTER-SCI',
                annee=2021,
                type=TrainingType.MASTER_MC.name,
                grade_academique=TrainingType.MASTER_MC.name,
                credits=60,
                cycle=2,
            ),
        )

        proposition.reponses_questions_specifiques = {
            '16de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
            # A default value will be set
            # '16de0c3d-3c06-4c93-8eb4-c8648f04f141': 'My response 1',
            '16de0c3d-3c06-4c93-8eb4-c8648f04f142': 'My response 2',
            '16de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
            '16de0c3d-3c06-4c93-8eb4-c8648f04f144': 'My response 4',
            '16de0c3d-3c06-4c93-8eb4-c8648f04f145': ['24de0c3d-3c06-4c93-8eb4-c8648f04f144'],
            # A default value will be set
            # '16de0c3d-3c06-4c93-8eb4-c8648f04f146': ['24de0c3d-3c06-4c93-8eb4-c8648f04f145'],
            # Will be deleted as it's a readonly element
            '16de0c3d-3c06-4c93-8eb4-c8648f04f149': 'MESSAGE',
            # Will be deleted as it's not interesting for this admission
            '26de0c3d-3c06-4c93-8eb4-c8648f04f140': 'Not interesting response 0',
            '26de0c3d-3c06-4c93-8eb4-c8648f04f141': 'Not interesting response 1',
        }

        self.proposition_repository.save(proposition)

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

        self.assertEqual(
            updated_proposition.reponses_questions_specifiques,
            {
                '16de0c3d-3c06-4c93-8eb4-c8648f04f140': 'My response 0',
                '16de0c3d-3c06-4c93-8eb4-c8648f04f141': '',
                '16de0c3d-3c06-4c93-8eb4-c8648f04f142': 'My response 2',
                '16de0c3d-3c06-4c93-8eb4-c8648f04f143': 'My response 3',
                '16de0c3d-3c06-4c93-8eb4-c8648f04f144': 'My response 4',
                '16de0c3d-3c06-4c93-8eb4-c8648f04f145': ['24de0c3d-3c06-4c93-8eb4-c8648f04f144'],
                '16de0c3d-3c06-4c93-8eb4-c8648f04f146': [],
            },
        )
