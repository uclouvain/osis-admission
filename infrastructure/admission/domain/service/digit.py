# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
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
from typing import Dict, List, Optional

import requests
from django.conf import settings
from django.db import models
from django.db.models import (
    Exists,
    OuterRef,
    Subquery,
    Prefetch,
    F,
    Value,
    Case,
    When,
    ExpressionWrapper,
    Q,
    BooleanField,
)
from django.db.models.functions import ExtractYear, ExtractMonth, Concat
from django.utils.translation import get_language

from admission.contrib.models import GeneralEducationAdmission
from admission.contrib.models.base import BaseAdmission
from admission.ddd import LANGUES_OBLIGATOIRES_DOCTORAT
from admission.ddd import NB_MOIS_MIN_VAE
from admission.ddd.admission.doctorat.preparation.dtos import ConditionsComptabiliteDTO, CurriculumDTO
from admission.ddd.admission.doctorat.preparation.dtos.connaissance_langue import ConnaissanceLangueDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import (
    AnneeExperienceAcademiqueDTO,
    ExperienceAcademiqueDTO,
    CurriculumAExperiencesDTO,
    ExperienceNonAcademiqueDTO,
)
from admission.ddd.admission.domain.service.i_digit import IDigitService
from admission.ddd.admission.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.admission.domain.validator._should_identification_candidat_etre_completee import BE_ISO_CODE
from admission.ddd.admission.dtos import AdressePersonnelleDTO, CoordonneesDTO, EtudesSecondairesDTO, IdentificationDTO
from admission.ddd.admission.dtos.etudes_secondaires import (
    DiplomeBelgeEtudesSecondairesDTO,
    DiplomeEtrangerEtudesSecondairesDTO,
    AlternativeSecondairesDTO,
)
from admission.ddd.admission.dtos.resume import ResumeCandidatDTO
from admission.infrastructure.admission.domain.service.annee_inscription_formation import (
    AnneeInscriptionFormationTranslator,
)
from base.models.enums.community import CommunityEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.person_address_type import PersonAddressType
from base.models.person import Person
from base.models.person_address import PersonAddress
from base.models.person_merge_proposal import PersonMergeProposal, PersonMergeStatus
from base.tasks.synchronize_entities_addresses import UCLouvain_acronym
from osis_profile.models import (
    EducationalExperienceYear,
    ProfessionalExperience,
    EducationalExperience,
)
from osis_profile.models.education import LanguageKnowledge


class DigitService(IDigitService):

    @classmethod
    def rechercher_compte_existant(cls, matricule: str, nom: str, prenom: str, date_naissance: str,) -> str:
        mock = True

        if mock:
            response = _mock_search_digit_account_return_response()
        else:
            response = requests.post(
                headers={'Content-Type': 'application/json'},
                data=json.dumps({
                    "last_name": nom,
                    "first_name": prenom,
                    "birth_date": date_naissance,
                }),
                url=settings.DIGIT_ACCOUNT_SEARCH_URL,
            )

        original_person = Person.objects.get(global_id=matricule)

        PersonMergeProposal.objects.update_or_create(
            original_person=original_person,
            defaults={
                "status": PersonMergeStatus.MATCH_FOUND.name,
                "similarity_result": str(response),
                "last_similarity_result_update": datetime.datetime.now(),
            }
        )

        return response


def _mock_search_digit_account_return_response():
    return json.loads(
            '['
            '      {'
            '        "person" : {'
            '          "matricule" : "12345678" ,'
            '          "lastName" : "Nom" ,'
            '          "firstName" : "Prenom" ,'
            '          "birthDate" : "2000-02-02" ,'
            '          "gender" : "M" ,'
            '          "nationalRegister" : "12345678910" ,'
            '          "nationality" : "BE" ,'
            '          "deceased" : false ,'
            '        },'
            '        "similarityRate" : 1000.0 ,'
            '      }'
            '    ]'
    )

