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
from unittest.mock import MagicMock

from django.test import TestCase

from admission.ddd.admission.domain.service.i_question_specifique import ISuperQuestionSpecifiqueTranslator
from admission.ddd.admission.enums import TypeItemFormulaire


class QuestionSpecifiquesTestCase(TestCase):
    def test_clean_specific_question_answers(self):
        self.assertEqual(
            ISuperQuestionSpecifiqueTranslator.clean_specific_question_answers(
                [],
                {},
            ),
            {},
        )

        self.assertEqual(
            ISuperQuestionSpecifiqueTranslator.clean_specific_question_answers(
                [
                    MagicMock(entity_id=MagicMock(uuid='D1'), type=TypeItemFormulaire.DOCUMENT),
                    MagicMock(entity_id=MagicMock(uuid='D2'), type=TypeItemFormulaire.DOCUMENT),
                    MagicMock(entity_id=MagicMock(uuid='T1'), type=TypeItemFormulaire.TEXTE),
                    MagicMock(entity_id=MagicMock(uuid='T2'), type=TypeItemFormulaire.TEXTE),
                    MagicMock(entity_id=MagicMock(uuid='S1'), type=TypeItemFormulaire.SELECTION),
                    MagicMock(entity_id=MagicMock(uuid='S2'), type=TypeItemFormulaire.SELECTION),
                ],
                {
                    'D1': ['D1_ANSWER'],
                    'D3': ['D3_ANSWER'],
                    'T1': 'T1_ANSWER',
                    'T3': 'T3_ANSWER',
                    'S1': 'S1_ANSWER',
                    'S3': 'S3_ANSWER',
                },
            ),
            {
                'D1': ['D1_ANSWER'],
                'D2': [],
                'T1': 'T1_ANSWER',
                'T2': '',
                'S1': 'S1_ANSWER',
                'S2': '',
            },
        )
