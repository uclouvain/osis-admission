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

from django.test import TestCase

from admission.infrastructure.admission.repository.digit import DigitRepository, _sanitize_validation_ticket_response


class TestDigitRepository(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.repository = DigitRepository()

    def test_sanatize_validation_ticket_response_assert_bad_format_return_digit(self):
        digit_response = {}

        response_sanitized = _sanitize_validation_ticket_response(digit_response)

        expected_result = {"errors": [{"errorCode": "DIGIT_RETURN_BAD_FORMAT"}], "valid": False}
        self.assertDictEqual(response_sanitized, expected_result)

    def test_sanatize_validation_ticket_response_cas_error_to_ignore(self):
        digit_response = {
             "valid": False,
             "errors": [{
                "errorCode": "INISS0007",
                "description": "La date de naissance (04000009518), numéro national: (2004/01/01) "
                               "impossible à vérifier."
             }]
        }

        response_sanitized = _sanitize_validation_ticket_response(digit_response)

        expected_result = {"valid": True, "errors": []}
        self.assertDictEqual(response_sanitized, expected_result)

    def test_sanatize_validation_ticket_response(self):
        digit_response = {
            "valid": False,
            "errors": [{
                "errorCode": "INISS0007",
                "description": "La date de naissance (04000009518), numéro national: (2004/01/01) "
                               "impossible à vérifier."
            },
            {
                "errorCode": "ITEST001",
                "description": "Une autre erreur à conserver"
            }]
        }

        response_sanitized = _sanitize_validation_ticket_response(digit_response)

        expected_result = {
            "valid": False,
            "errors": [{
                "errorCode": "ITEST001",
                "description": "Une autre erreur à conserver"
            }]
        }
        self.assertDictEqual(response_sanitized, expected_result)
