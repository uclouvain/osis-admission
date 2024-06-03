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

from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutChecklist
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import ConfigurationStatutChecklist


class ConfigurationStatutChecklistTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_kwargs = {
            'identifiant': 'id-1',
            'libelle': 'label',
            'statut': ChoixStatutChecklist.GEST_REUSSITE,
            'extra': {},
        }

    def test_configuration_matches_other(self):
        configuration = ConfigurationStatutChecklist(**self.default_kwargs)

        # Check empty
        self.assertFalse(configuration.matches({}))

        # Check with other status
        self.assertFalse(
            configuration.matches(
                {
                    'statut': ChoixStatutChecklist.GEST_BLOCAGE.name,
                    'extra': {},
                }
            )
        )

        # Check with same status and no extra
        self.assertTrue(
            configuration.matches(
                {
                    'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                    'extra': {},
                }
            )
        )

        # Check with different values of extra
        self.assertTrue(
            configuration.matches(
                {
                    'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                    'extra': {'my_extra': 1},
                }
            )
        )

        configuration.extra = {'my_extra': 1}

        self.assertTrue(
            configuration.matches(
                {
                    'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                    'extra': {'my_extra': 1},
                }
            )
        )
        self.assertTrue(
            configuration.matches(
                {
                    'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                    'extra': {'my_extra': 1, 'my_extra_b': 2},
                }
            )
        )
        self.assertFalse(
            configuration.matches(
                {
                    'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                    'extra': {'my_extra': 2, 'my_extra_b': 1},
                }
            )
        )
        self.assertFalse(
            configuration.matches(
                {
                    'statut': ChoixStatutChecklist.GEST_REUSSITE.name,
                    'extra': {'my_extra_b': 1},
                }
            )
        )
