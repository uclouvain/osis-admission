# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from unittest import TestCase
from unittest.mock import MagicMock

from base.models.enums.education_group_types import TrainingType
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import ValorisationEtudesSecondairesDTO


class ValorisationEtudesSecondairesDTOTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.diploma = MagicMock()

    def test_est_valorise(self):
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=True,
                types_formations_admissions_valorisees=[],
            ).est_valorise
        )
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[TrainingType.BACHELOR.name],
            ).est_valorise
        )
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=True,
                types_formations_admissions_valorisees=[TrainingType.BACHELOR.name],
            ).est_valorise
        )
        self.assertFalse(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ).est_valorise
        )

    def test_diplome_est_modifiable(self):
        # > BACHELIER => ok
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ).diplome_est_modifiable(diplome=None, formation=TrainingType.BACHELOR.name)
        )
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ).diplome_est_modifiable(diplome=self.diploma, formation=TrainingType.BACHELOR.name)
        )

        # > MASTER|IUFC > ok
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ).diplome_est_modifiable(diplome=None, formation=TrainingType.MASTER_M1.name)
        )
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[],
            ).diplome_est_modifiable(diplome=self.diploma, formation=TrainingType.MASTER_M1.name)
        )

        # BACHELIER > BACHELIER => ok si pas de diplôme, sinon ko
        self.assertFalse(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[TrainingType.BACHELOR.name],
            ).diplome_est_modifiable(diplome=self.diploma, formation=TrainingType.BACHELOR.name)
        )
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[TrainingType.BACHELOR.name],
            ).diplome_est_modifiable(diplome=None, formation=TrainingType.BACHELOR.name)
        )

        # BACHELIER > MASTER|IUFC => ko
        self.assertFalse(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[TrainingType.BACHELOR.name],
            ).diplome_est_modifiable(diplome=self.diploma, formation=TrainingType.MASTER_M1.name)
        )
        self.assertFalse(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[TrainingType.BACHELOR.name],
            ).diplome_est_modifiable(diplome=None, formation=TrainingType.MASTER_M1.name)
        )

        # MASTER|IUFC > MASTER|IUFC => ko
        self.assertFalse(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[TrainingType.MASTER_M1.name],
            ).diplome_est_modifiable(diplome=self.diploma, formation=TrainingType.MASTER_M1.name)
        )
        self.assertFalse(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[TrainingType.MASTER_M1.name],
            ).diplome_est_modifiable(diplome=None, formation=TrainingType.MASTER_M1.name)
        )

        # MASTER|IUFC > BACHELIER => ok
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[TrainingType.MASTER_M1.name],
            ).diplome_est_modifiable(diplome=self.diploma, formation=TrainingType.BACHELOR.name)
        )
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=False,
                types_formations_admissions_valorisees=[TrainingType.MASTER_M1.name],
            ).diplome_est_modifiable(diplome=None, formation=TrainingType.BACHELOR.name)
        )

        # EPC (avec diplôme) > MASTER|IUFC|BACHELIER => ko
        self.assertFalse(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=True,
                types_formations_admissions_valorisees=[],
            ).diplome_est_modifiable(diplome=self.diploma, formation=TrainingType.BACHELOR.name)
        )
        self.assertFalse(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=True,
                types_formations_admissions_valorisees=[],
            ).diplome_est_modifiable(diplome=self.diploma, formation=TrainingType.MASTER_M1.name)
        )

        # EPC (sans diplôme) > MASTER|IUFC => ko
        self.assertFalse(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=True,
                types_formations_admissions_valorisees=[],
            ).diplome_est_modifiable(diplome=None, formation=TrainingType.MASTER_M1.name)
        )

        # EPC (sans diplôme) > BACHELIER => ok
        self.assertTrue(
            ValorisationEtudesSecondairesDTO(
                est_valorise_par_epc=True,
                types_formations_admissions_valorisees=[],
            ).diplome_est_modifiable(diplome=None, formation=TrainingType.BACHELOR.name)
        )
