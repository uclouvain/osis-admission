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
from types import SimpleNamespace

import requests
from django.conf import settings

from admission.ddd.admission.domain.service.i_digit import IDigitService
from admission.ddd.admission.domain.validator.exceptions import PasDePropositionDeFusionTrouveeException
from admission.templatetags.admission import format_matricule
from base.business.student import find_student_by_discriminating
from base.models.person import Person
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.models.student import Student
from osis_common.utils.models import get_object_or_none

MOCK_DIGIT_SERVICE_CALL = settings.MOCK_DIGIT_SERVICE_CALL
logger = logging.getLogger(settings.DEFAULT_LOGGER)


TEMPORARY_ACCOUNT_GLOBAL_ID_PREFIX = ['8', '9']


class DigitService(IDigitService):
    @classmethod
    def rechercher_compte_existant(cls, matricule: str):
        original_person = Person.objects.get(global_id=matricule)
        person_merge_proposal, created = PersonMergeProposal.objects.get_or_create(
            original_person=original_person,
            defaults={
                "last_similarity_result_update": datetime.datetime.now()
            },
        )

        if person_merge_proposal.status in [
            PersonMergeStatus.PENDING.name,      # Cas gestionnaire en cours de résolution
            PersonMergeStatus.IN_PROGRESS.name,  # En attente du retour de fusion de DiGIT
            PersonMergeStatus.REFUSED.name,      # Gestionnaire refuse la proposition de fusion
        ]:
            logger.info(
                f"[Recherche doublon potentiel DigIT - {matricule} ] Recherche non effectuée car "
                f"état de la proposition de fusion est {person_merge_proposal.status}"
            )
            return None

        if not cls.correspond_a_compte_temporaire(matricule):
            person_merge_proposal.status = PersonMergeStatus.NO_MATCH.name
            person_merge_proposal.similarity_result = []
            person_merge_proposal.last_similarity_result_update = datetime.datetime.now()
            person_merge_proposal.save()
            logger.info(
                f"[Recherche doublon potentiel DigIT - {matricule} ] Recherche non effectuée car compte interne"
            )
            return None

        national_number_sanatized = None
        if original_person.national_number:
            # keep only digits in niss
            national_number_sanatized = re.sub(r'\D', '', original_person.national_number)

        data = {
            "lastname": original_person.last_name,
            "firstname": original_person.first_name,
            "birthdate": str(original_person.birth_date) if original_person.birth_date else "",
            "sex": original_person.sex,
            "nationalRegister": national_number_sanatized,
            "otherFirstName": original_person.middle_name,
        }
        logger.info(f"[Recherche doublon potentiel DigIT - {matricule}] Données envoyées à DigIT {json.dumps(data)}")

        if MOCK_DIGIT_SERVICE_CALL:
            similarity_data = _mock_search_digit_account_return_response()
        else:
            try:
                response = requests.post(
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': settings.ESB_AUTHORIZATION,
                    },
                    data=json.dumps(data),
                    url=f"{settings.ESB_API_URL}/{settings.DIGIT_ACCOUNT_SEARCH_URL}"
                )
                similarity_data = response.json()
                if not isinstance(similarity_data, list) and similarity_data.get('status') == 500:
                    raise Exception(f"Digit internal server error (payload: {str(similarity_data)})")
            except Exception:
                logger.exception(
                    f"[Recherche doublon potentiel DigIT - {matricule}] Une erreur est survenue avec DigIT"
                )
                PersonMergeProposal.objects.update_or_create(
                    original_person=original_person,
                    defaults={
                        "status": PersonMergeStatus.ERROR.name,
                        "similarity_result": [],
                        "last_similarity_result_update": datetime.datetime.now(),
                    }
                )
                return None

        logger.info(f"[Recherche doublon potentiel DigIT - {matricule}] Données recues de DigIT {similarity_data}")
        similarity_data = _clean_data_from_duplicate_registration_ids(similarity_data)
        similarity_data = _retrieve_private_email_in_data(similarity_data)
        PersonMergeProposal.objects.update_or_create(
            original_person=original_person,
            defaults={
                "status": _get_status_from_digit_response(similarity_data),
                "similarity_result": similarity_data,
                "last_similarity_result_update": datetime.datetime.now(),
            }
        )

    @classmethod
    def correspond_a_compte_temporaire(cls, matricule_candidat: str) -> bool:
        return matricule_candidat[0] in TEMPORARY_ACCOUNT_GLOBAL_ID_PREFIX

    @classmethod
    def recuperer_proposition_fusion(cls, matricule_candidat: str) -> SimpleNamespace:
        try:
            proposition_fusion = PersonMergeProposal.objects.get(original_person__global_id=matricule_candidat)
            return SimpleNamespace(
                statut=proposition_fusion.status,
                a_une_syntaxe_valide=proposition_fusion.validation.get('valid', False)
            )
        except PersonMergeProposal.DoesNotExist:
            raise PasDePropositionDeFusionTrouveeException


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
    for result in similarity_data:
        # for each global_id returned by DigIT (global_id == matricule)
        global_id = format_matricule(result['person']['matricule'])

        # get registration_ids from DigIT response (registration_id == sourceId)
        registration_ids = [
            account['sourceId'] for account in result['applicationAccounts'] if account['source'] == 'ETU'
        ]

        if len(registration_ids) > 1:
            logger.info(f"DUPLICATE REGISTRATION IDs: {registration_ids} for {global_id}")

            # discriminate registration_ids to keep only one
            captured_registration_id = _discriminate_registration_id(registration_ids)
            logger.info(f"DEDUPLICATING: kept {captured_registration_id}")

            if captured_registration_id:
                # overwrite applicationAccounts in response to keep one registration_id
                result['applicationAccounts'] = [
                    a for a in result['applicationAccounts'] if a['sourceId'] == captured_registration_id
                ]

    return similarity_data


def _discriminate_registration_id(registration_ids):
    qs = Student.objects.filter(registration_id__in=registration_ids)
    student = find_student_by_discriminating(qs)
    return student.registration_id if student else None


def _retrieve_private_email_in_data(similarity_data):
    for result in similarity_data:
        global_id = format_matricule(result['person']['matricule'])
        person = get_object_or_none(Person, global_id=global_id)
        result['person']['private_email'] = person.private_email if person and person.private_email else None
    return similarity_data


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
