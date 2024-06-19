# ##############################################################################
#
#    OSIS stands for Open Student Information System. Its an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import json
import logging
import re

import requests
import waffle
from django.conf import settings

from admission.ddd.admission.domain.service.i_digit import IDigitService
from base.business.student import find_student_by_discriminating
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.models.student import Student

MOCK_DIGIT_SERVICE_CALL = settings.MOCK_DIGIT_SERVICE_CALL
logger = logging.getLogger(settings.DEFAULT_LOGGER)


TEMPORARY_ACCOUNT_GLOBAL_ID_PREFIX = ['8', '9']

class DigitService(IDigitService):
    @classmethod
    def rechercher_compte_existant(
            cls,
            matricule: str,
            nom: str,
            prenom: str,
            autres_prenoms: str,
            genre: str,
            date_naissance: str,
            niss: str
    ):
        if not waffle.switch_is_active('fusion-digit') or matricule[0] not in TEMPORARY_ACCOUNT_GLOBAL_ID_PREFIX:
            return []

        original_person = Person.objects.get(global_id=matricule)

        person_merge_proposal, created = PersonMergeProposal.objects.get_or_create(
            original_person=original_person,
            defaults={
                "last_similarity_result_update": datetime.datetime.now()
            },
        )

        if person_merge_proposal.status in [PersonMergeStatus.IN_PROGRESS.name, PersonMergeStatus.MERGED.name]:
            return []

        if niss:
            # keep only digits in niss
            niss = re.sub(r'\D', '', niss)

        data = {
            "lastname": nom, "firstname": prenom, "birthdate": date_naissance,
            "sex": genre, "nationalRegister": niss, "otherFirstName": autres_prenoms,
        }
        logger.info(
            f"DIGIT search existing person: "
            f'{json.dumps(data)}'
        )

        if MOCK_DIGIT_SERVICE_CALL:
            similarity_data = _mock_search_digit_account_return_response()
        else:
            response = requests.post(
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': settings.ESB_AUTHORIZATION,
                },
                data=json.dumps(data),
                url=f"{settings.ESB_API_URL}/{settings.DIGIT_ACCOUNT_SEARCH_URL}"
            )
            similarity_data = response.json()

        logger.info(f"DIGIT Response: {similarity_data}")

        similarity_data = _clean_data_from_duplicate_registration_ids(similarity_data)

        PersonMergeProposal.objects.update_or_create(
            original_person=original_person,
            defaults={
                "status": _get_status_from_digit_response(similarity_data),
                "similarity_result": similarity_data,
                "last_similarity_result_update": datetime.datetime.now(),
            }
        )

        similarity_data = person_merge_proposal.similarity_result

        return similarity_data


def _get_status_from_digit_response(similarity_data):
    if settings.MOCK_DIGIT_SERVICE_CALL:
        return PersonMergeStatus.MATCH_FOUND.name
    if similarity_data:
        if type(similarity_data) != list and "status" in similarity_data.keys() and similarity_data["status"] == 500:
            return PersonMergeStatus.ERROR.name
        else:
            return PersonMergeStatus.MATCH_FOUND.name
    else:
        return PersonMergeStatus.NO_MATCH.name


def _clean_data_from_duplicate_registration_ids(similarity_data):
    if not similarity_data:
        return similarity_data

    registration_ids_by_matricule = {}

    for result in similarity_data:
        matricule = result['person']['matricule']

        # get registration_ids from DigIT response (registration_id == sourceId)
        registration_ids = [account['sourceId'] for account in result['applicationAccounts'] if account['source'] == 'ETU']

        if len(registration_ids) > 1:
            logger.info(f"DUPLICATE REGISTRATION IDs: {registration_ids} for {matricule}")
            captured_noma = _discriminate_registration_id(registration_ids)
            logger.info(f"DEDUPLICATING: kept {captured_noma}")

            # overwrite applicationAccounts in response to keep one registration_id
            result['applicationAccounts'] = [a for a in result['applicationAccounts'] if a['sourceId'] == captured_noma]

        registration_ids_by_matricule[matricule] = registration_ids

    return similarity_data


def _discriminate_registration_id(registration_ids):
    qs = Student.objects.filter(registration_id__in=registration_ids)
    student = find_student_by_discriminating(qs)
    return student.registration_id


def _mock_search_digit_account_return_response():
    return json.loads(
        """
            [
                  {
                    "person" : {
                      "matricule" : "12345678" ,
                      "lastName" : "Nom" ,
                      "firstName" : "Prenom" ,
                      "birthDate" : "2000-02-02" ,
                      "gender" : "M" ,
                      "nationalRegister" : "12345678910" ,
                      "nationality" : "BE" ,
                      "deceased" : false
                    },
                    "similarityRate" : 1000.0
                  },
                  {
                    "person" : {
                      "matricule" : "9870653" ,
                      "lastName" : "Test" ,
                      "firstName" : "Test" ,
                      "birthDate" : "1930-01-01" ,
                      "gender" : "M" ,
                      "nationalRegister" : "098764432112" ,
                      "nationality" : "BE" ,
                      "deceased" : false
                    },
                    "similarityRate" : 50.0
                  }
                ]
        """
        )
