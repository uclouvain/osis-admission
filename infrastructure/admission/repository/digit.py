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
from typing import Optional

import requests
from django.conf import settings
from requests import RequestException

from admission.ddd.admission.repository.i_digit import IDigitRepository
from base.business.student import find_student_by_discriminating
from base.models.person import Person
from base.models.student import Student


# TODO: Use query to ask gestion_des_comptes context
class DigitRepository(IDigitRepository):
    @classmethod
    def get_registration_id_sent_to_digit(cls, global_id: str) -> Optional[str]:
        candidate = Person.objects.get(global_id=global_id)

        # Check if already a personmergeproposal with generated noma
        if hasattr(candidate, 'personmergeproposal') and candidate.personmergeproposal.registration_id_sent_to_digit:
            return candidate.personmergeproposal.registration_id_sent_to_digit

        # Check if person is already know in OSIS side
        student = find_student_by_discriminating(qs=Student.objects.filter(person=candidate))
        if student is not None and student.registration_id:
            return student.registration_id

        # Check person in EPC
        noma_from_epc = _find_student_registration_id_in_epc(matricule=candidate.global_id)
        if noma_from_epc:
            return noma_from_epc


def _find_student_registration_id_in_epc(matricule):
    try:
        url = f"{settings.ESB_STUDENT_API}/{matricule}"
        response = requests.get(url, headers={"Authorization": settings.ESB_AUTHORIZATION})
        result = response.json()
        if response.status_code == 200 and result.get('lireDossierEtudiantResponse'):
            if result['lireDossierEtudiantResponse'].get('return'):
                return _format_registration_id(str(result['lireDossierEtudiantResponse']['return'].get('noma')))
    except (RequestException, ValueError) as e:
        return None


def _format_registration_id(registration_id):
    prefix_registration_id = (8 - len(registration_id)) * '0'
    registration_id = ''.join([prefix_registration_id, registration_id])
    return registration_id
