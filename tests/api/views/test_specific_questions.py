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

import datetime
import uuid
from unittest.mock import patch

import freezegun
from django.shortcuts import resolve_url
from django.utils.translation import gettext
from rest_framework import status
from rest_framework.test import APITestCase

from admission.contrib.models import ContinuingEducationAdmission, GeneralEducationAdmission
from admission.ddd import BE_ISO_CODE, EN_ISO_CODE, FR_ISO_CODE
from admission.ddd.admission.domain.validator.exceptions import PosteDiplomatiqueNonTrouveException
from admission.ddd.admission.enums import CritereItemFormulaireNationaliteDiplome
from admission.ddd.admission.enums.question_specifique import (
    CritereItemFormulaireFormation,
    CritereItemFormulaireLangueEtudes,
    CritereItemFormulaireNationaliteCandidat,
    CritereItemFormulaireVIP,
    Onglets,
    TypeItemFormulaire,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixInscriptionATitre,
    ChoixTypeAdresseFacturation,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.calendar import AdmissionAcademicCalendarFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.diplomatic_post import DiplomaticPostFactory
from admission.tests.factories.form_item import (
    AdmissionFormItemInstantiationFactory,
    DocumentAdmissionFormItemFactory,
    MessageAdmissionFormItemFactory,
    TextAdmissionFormItemFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory
from admission.tests.factories.scholarship import InternationalScholarshipFactory
from admission.tests.factories.secondary_studies import BelgianHighSchoolDiplomaFactory, ForeignHighSchoolDiplomaFactory
from admission.tests.factories.supervision import PromoterFactory
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import EntityType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.person import PersonFactory
from osis_profile.models import EducationalExperience
from osis_profile.tests.factories.curriculum import EducationalExperienceFactory
from reference.tests.factories.country import CountryFactory
from reference.tests.factories.language import LanguageFactory


class BaseDoctorateSpecificQuestionListApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        cls.commission = EntityVersionFactory(
            entity_type=EntityType.DOCTORAL_COMMISSION.name,
            acronym='CDA',
        ).entity
        cls.promoter = PromoterFactory(actor_ptr__person__first_name="Joe")
        cls.message_item = MessageAdmissionFormItemFactory(
            uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
            internal_label='message_item.0',
            text={'en': 'My very short message.', 'fr-be': 'Mon très court message.'},
            configuration={},
        )
        TextAdmissionFormItemFactory(
            uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da552'),
            internal_label='text_item.0',
            title={'en': 'Text field', 'fr-be': 'Champ texte'},
            text={'en': 'Detailed data.', 'fr-be': 'Données détaillées.'},
            help_text={'en': 'Write here', 'fr-be': 'Ecrivez ici'},
            configuration={},
        )
        DocumentAdmissionFormItemFactory(
            uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da553'),
            internal_label='document_item.0',
            title={'en': 'Document field', 'fr-be': 'Champ document'},
            text={'en': 'Detailed data.', 'fr-be': 'Données détaillées.'},
            configuration={},
        )

        cls.be_country = CountryFactory(iso_code=BE_ISO_CODE, european_union=True)
        cls.fr_country = CountryFactory(iso_code=FR_ISO_CODE, european_union=True)
        cls.us_country = CountryFactory(iso_code='US', european_union=False)
        cls.en_country = CountryFactory(iso_code='EN', european_union=False)
        cls.it_country = CountryFactory(iso_code='IT', european_union=True)
        cls.fr_language = LanguageFactory(code=FR_ISO_CODE, name="Français")
        cls.en_language = LanguageFactory(code=EN_ISO_CODE, name="Anglais")
        cls.it_language = LanguageFactory(code='IT', name="Italien")

        # Users
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user

        # Users
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user

    def setUp(self) -> None:
        super().setUp()
        admission = DoctorateAdmissionFactory(
            training__management_entity=self.commission,
            training__academic_year__year=2020,
            supervision_group=self.promoter.actor_ptr.process,
        )
        self.admission = admission

        # Users
        self.candidate = admission.candidate

        # Target url
        self.url = resolve_url(
            "admission_api_v1:doctorate-specific-questions",
            uuid=admission.uuid,
            tab=Onglets.CHOIX_FORMATION.name,
        )


class DoctorateSpecificQuestionListApiTestCase(BaseDoctorateSpecificQuestionListApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.message_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=self.message_item,
            academic_year=self.admission.training.academic_year,
            weight=1,
            tab=Onglets.CHOIX_FORMATION.name,
        )

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'patch', 'post', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_with_other_candidate_user(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_with_valid_candidate_user(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    'uuid': 'fe254203-17c7-47d6-95e4-3c5c532da551',
                    'type': TypeItemFormulaire.MESSAGE.name,
                    'required': False,
                    'title': {},
                    'text': {'en': 'My very short message.', 'fr-be': 'Mon très court message.'},
                    'help_text': {},
                    'configuration': {},
                    'values': [],
                },
            ],
        )

    def test_retrieve_items_in_other_tab(self):
        self.client.force_authenticate(user=self.candidate.user)

        url = resolve_url(
            "admission_api_v1:doctorate-specific-questions",
            uuid=self.admission.uuid,
            tab=Onglets.CURRICULUM.name,
        )

        # The question is in the TRAINING_CHOICE tab -> no result
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The question is in the CURRICULUM tab -> return it
        self.message_instantiation.tab = Onglets.CURRICULUM.name
        self.message_instantiation.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0].get('uuid'), 'fe254203-17c7-47d6-95e4-3c5c532da551')

    def test_retrieve_active_items(self):
        self.client.force_authenticate(user=self.candidate.user)

        # The question is active -> one result
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The question is not active -> no result
        self.message_item.active = False
        self.message_item.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_of_the_training_academic_year(self):
        self.client.force_authenticate(user=self.candidate.user)

        # The question is associated to the training academic year -> one result
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The question is not associated with the training academic year -> no result
        self.message_instantiation.academic_year = AcademicYearFactory(year=2010)
        self.message_instantiation.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_related_to_every_nationality(self):
        self.client.force_authenticate(user=self.candidate.user)

        # The candidate has no nationality
        self.candidate.country_of_citizenship = None
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The candidate has a nationality
        self.candidate.country_of_citizenship = self.be_country
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_retrieve_items_related_to_the_admission(self):
        self.client.force_authenticate(user=self.candidate.user)

        # The question is related to another admission -> no result
        self.message_instantiation.display_according_education = CritereItemFormulaireFormation.UNE_SEULE_ADMISSION.name
        self.message_instantiation.admission_id = DoctorateAdmissionFactory().pk
        self.message_instantiation.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The question is related to the admission -> return it
        self.message_instantiation.admission_id = self.admission.pk
        self.message_instantiation.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0].get('uuid'), 'fe254203-17c7-47d6-95e4-3c5c532da551')

    def test_retrieve_items_related_to_be_diploma_nationality(self):
        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation.diploma_nationality = CritereItemFormulaireNationaliteDiplome.BELGE.name
        self.message_instantiation.save()

        # The candidate has no educational experience
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a belgian educational experience but without a diploma
        educational_experience = EducationalExperienceFactory(
            person=self.candidate,
            obtained_diploma=False,
            country=self.be_country,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a belgian educational experience with a diploma
        educational_experience.obtained_diploma = True
        educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The candidate has a foreign educational experience with a diploma
        educational_experience.country = self.fr_country
        educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_related_to_non_be_diploma_nationality(self):
        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation.diploma_nationality = CritereItemFormulaireNationaliteDiplome.NON_BELGE.name
        self.message_instantiation.save()

        # The candidate has no educational experience
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a belgian educational experience but without a diploma
        educational_experience = EducationalExperienceFactory(
            person=self.candidate,
            obtained_diploma=False,
            country=self.be_country,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a belgian educational experience with a diploma
        educational_experience.obtained_diploma = True
        educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a foreign educational experience with a diploma
        educational_experience.country = self.fr_country
        educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The candidate has a foreign educational experience but without a diploma
        educational_experience.obtained_diploma = False
        educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        educational_experience.obtained_diploma = True
        educational_experience.save()

        # The candidate also has a belgian educational experience but without a diploma
        second_educational_experience = EducationalExperienceFactory(
            person=self.candidate,
            obtained_diploma=False,
            country=self.be_country,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The candidate also has a belgian educational experience with a diploma
        second_educational_experience.obtained_diploma = True
        second_educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_related_to_eu_diploma_nationality(self):
        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation.diploma_nationality = CritereItemFormulaireNationaliteDiplome.UE.name
        self.message_instantiation.save()

        # The candidate has no educational experience
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a ue educational experience but without a diploma
        educational_experience = EducationalExperienceFactory(
            person=self.candidate,
            obtained_diploma=False,
            country=self.fr_country,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a ue educational experience with a diploma
        educational_experience.obtained_diploma = True
        educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The candidate has a non ue educational experience with a diploma
        educational_experience.country = self.us_country
        educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_related_to_not_eu_diploma_nationality(self):
        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation.diploma_nationality = CritereItemFormulaireNationaliteDiplome.NON_UE.name
        self.message_instantiation.save()

        # The candidate has no educational experience
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a non-ue educational experience but without a diploma
        educational_experience = EducationalExperienceFactory(
            person=self.candidate,
            obtained_diploma=False,
            country=self.us_country,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a non-ue educational experience with a diploma
        educational_experience.obtained_diploma = True
        educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The candidate has a ue educational experience with a diploma
        educational_experience.country = self.fr_country
        educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a non-ue educational experience but without a diploma
        educational_experience.obtained_diploma = False
        educational_experience.country = self.us_country
        educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        educational_experience.obtained_diploma = True
        educational_experience.save()

        # The candidate also has a ue educational experience but without a diploma
        second_educational_experience = EducationalExperienceFactory(
            person=self.candidate,
            obtained_diploma=False,
            country=self.be_country,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The candidate also has a ue educational experience with a diploma
        second_educational_experience.obtained_diploma = True
        second_educational_experience.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_related_to_be_nationality(self):
        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation.candidate_nationality = CritereItemFormulaireNationaliteCandidat.BELGE.name
        self.message_instantiation.save()

        # The candidate has no nationality
        self.candidate.country_of_citizenship = None
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has the be nationality
        self.candidate.country_of_citizenship = self.be_country
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The candidate has the fr nationality
        self.candidate.country_of_citizenship = self.fr_country
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_related_to_non_be_nationality(self):
        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation.candidate_nationality = CritereItemFormulaireNationaliteCandidat.NON_BELGE.name
        self.message_instantiation.save()

        # The candidate has no nationality
        self.candidate.country_of_citizenship = None
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has the be nationality
        self.candidate.country_of_citizenship = self.be_country
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has the fr nationality
        self.candidate.country_of_citizenship = self.fr_country
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_retrieve_items_related_to_ue_nationality(self):
        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation.candidate_nationality = CritereItemFormulaireNationaliteCandidat.UE.name
        self.message_instantiation.save()

        # The candidate has no nationality
        self.candidate.country_of_citizenship = None
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a eu nationality
        self.candidate.country_of_citizenship = self.fr_country
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # The candidate hasn't got a eu nationality
        self.candidate.country_of_citizenship = self.us_country
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_related_to_non_ue_nationality(self):
        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation.candidate_nationality = CritereItemFormulaireNationaliteCandidat.NON_UE.name
        self.message_instantiation.save()

        # The candidate has no nationality
        self.candidate.country_of_citizenship = None
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate has a eu nationality
        self.candidate.country_of_citizenship = self.fr_country
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

        # The candidate hasn't got a eu nationality
        self.candidate.country_of_citizenship = self.us_country
        self.candidate.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class DoctorateSpecificQuestionListWithItemsRelatedToNoStudiesInFrenchApiTestCase(
    BaseDoctorateSpecificQuestionListApiTestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=self.message_item,
            academic_year=self.admission.training.academic_year,
            weight=1,
            tab=Onglets.CHOIX_FORMATION.name,
            study_language=CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_FR.name,
        )

        self.belgian_diploma = BelgianHighSchoolDiplomaFactory()
        self.fr_foreign_diploma = ForeignHighSchoolDiplomaFactory(linguistic_regime=self.fr_language)
        self.en_foreign_diploma = ForeignHighSchoolDiplomaFactory(linguistic_regime=self.en_language)
        self.it_foreign_diploma = ForeignHighSchoolDiplomaFactory(linguistic_regime=self.it_language)

        EducationalExperience.objects.all().delete()

    def test_retrieve_items_without_diploma_or_study(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_retrieve_items_with_belgian_high_school_diploma(self):
        self.belgian_diploma.person = self.candidate
        self.belgian_diploma.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_with_foreign_and_french_high_school_diploma(self):
        self.fr_foreign_diploma.person = self.candidate
        self.fr_foreign_diploma.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_with_foreign_and_no_french_high_school_diploma(self):
        self.it_foreign_diploma.person = self.candidate
        self.it_foreign_diploma.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_retrieve_items_with_cv_experience_in_french(self):
        EducationalExperienceFactory(
            person=self.candidate,
            linguistic_regime=self.fr_language,
            obtained_diploma=True,
            country=self.fr_country,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_with_cv_experience_but_not_in_french(self):
        EducationalExperienceFactory(
            person=self.candidate,
            linguistic_regime=self.it_language,
            obtained_diploma=True,
            country=self.fr_country,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class DoctorateSpecificQuestionListWithItemsRelatedToNoStudiesInEnglishApiTestCase(
    BaseDoctorateSpecificQuestionListApiTestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=self.message_item,
            academic_year=self.admission.training.academic_year,
            weight=1,
            tab=Onglets.CHOIX_FORMATION.name,
            study_language=CritereItemFormulaireLangueEtudes.AUCUNE_ETUDE_EN.name,
        )

        self.belgian_diploma = BelgianHighSchoolDiplomaFactory()
        self.fr_foreign_diploma = ForeignHighSchoolDiplomaFactory(linguistic_regime=self.fr_language)
        self.en_foreign_diploma = ForeignHighSchoolDiplomaFactory(linguistic_regime=self.en_language)
        self.it_foreign_diploma = ForeignHighSchoolDiplomaFactory(linguistic_regime=self.it_language)

        EducationalExperience.objects.all().delete()

    def test_retrieve_items_without_diploma_or_study(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_retrieve_items_with_belgian_high_school_diploma(self):
        self.belgian_diploma.person = self.candidate
        self.belgian_diploma.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_with_foreign_and_english_high_school_diploma(self):
        self.en_foreign_diploma.person = self.candidate
        self.en_foreign_diploma.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_with_foreign_and_no_english_high_school_diploma(self):
        self.it_foreign_diploma.person = self.candidate
        self.it_foreign_diploma.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_retrieve_items_with_cv_experience_in_english(self):
        EducationalExperienceFactory(
            person=self.candidate,
            linguistic_regime=self.en_language,
            obtained_diploma=True,
            country=self.fr_country,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_with_cv_experience_but_not_in_english(self):
        EducationalExperienceFactory(
            person=self.candidate,
            linguistic_regime=self.it_language,
            obtained_diploma=True,
            country=self.fr_country,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class DoctorateSpecificQuestionListWithItemsRelatedToVIPCandidateApiTestCase(
    BaseDoctorateSpecificQuestionListApiTestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=self.message_item,
            academic_year=self.admission.training.academic_year,
            weight=1,
            tab=Onglets.CHOIX_FORMATION.name,
            vip_candidate=CritereItemFormulaireVIP.VIP.name,
        )

    def test_retrieve_items_without_any_scholarship(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_with_erasmus_scholarship(self):
        self.admission.international_scholarship = InternationalScholarshipFactory()
        self.admission.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class DoctorateSpecificQuestionListWithItemsRelatedToNonVIPCandidateApiTestCase(
    BaseDoctorateSpecificQuestionListApiTestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=self.message_item,
            academic_year=self.admission.training.academic_year,
            weight=1,
            tab=Onglets.CHOIX_FORMATION.name,
            vip_candidate=CritereItemFormulaireVIP.NON_VIP.name,
        )

    def test_retrieve_items_without_any_scholarship(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_retrieve_items_with_erasmus_scholarship(self):
        self.admission.international_scholarship = InternationalScholarshipFactory()
        self.admission.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)


class DoctorateSpecificQuestionListWithItemsRelatedToTheEducationApiTestCase(
    BaseDoctorateSpecificQuestionListApiTestCase
):
    def setUp(self) -> None:
        super().setUp()

        self.client.force_authenticate(user=self.candidate.user)

        self.message_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=self.message_item,
            academic_year=self.admission.training.academic_year,
            weight=1,
            tab=Onglets.CHOIX_FORMATION.name,
        )

    def test_retrieve_items_related_to_every_education(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_retrieve_items_related_to_an_education_group_type(self):
        self.message_instantiation.display_according_education = CritereItemFormulaireFormation.TYPE_DE_FORMATION.name
        # Education group type of the admission
        self.message_instantiation.education_group_type = self.admission.training.education_group_type
        self.message_instantiation.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # Other education group type
        self.message_instantiation.education_group_type = EducationGroupTypeFactory(
            name=TrainingType.MASTER_MA_120.name,
        )
        self.message_instantiation.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_retrieve_items_related_to_an_education_group(self):
        self.message_instantiation.display_according_education = CritereItemFormulaireFormation.UNE_FORMATION.name
        # Education group of the admission
        self.message_instantiation.education_group = self.admission.training.education_group
        self.message_instantiation.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

        # Other education group
        self.message_instantiation.education_group = EducationGroupFactory()
        self.message_instantiation.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)


class GeneralEducationSpecificQuestionListApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        cls.admission = GeneralEducationAdmissionFactory()

        cls.message_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=MessageAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='message_item',
                text={'en': 'My very short message.', 'fr-be': 'Mon très court message.'},
                configuration={},
            ),
            academic_year=cls.admission.training.academic_year,
            weight=1,
            tab=Onglets.CHOIX_FORMATION.name,
        )

        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user

        # Target url
        cls.url = resolve_url(
            "admission_api_v1:general-specific-questions",
            uuid=cls.admission.uuid,
            tab=Onglets.CHOIX_FORMATION.name,
        )

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'patch', 'post', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_with_other_candidate_user(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_with_valid_candidate_user(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    'uuid': 'fe254203-17c7-47d6-95e4-3c5c532da551',
                    'type': TypeItemFormulaire.MESSAGE.name,
                    'required': False,
                    'title': {},
                    'text': {'en': 'My very short message.', 'fr-be': 'Mon très court message.'},
                    'help_text': {},
                    'configuration': {},
                    'values': [],
                },
            ],
        )


class ContinuingEducationSpecificQuestionListApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        cls.admission = ContinuingEducationAdmissionFactory()

        cls.message_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=MessageAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='message_item',
                text={'en': 'My very short message.', 'fr-be': 'Mon très court message.'},
                configuration={},
            ),
            academic_year=cls.admission.training.academic_year,
            weight=1,
            tab=Onglets.CHOIX_FORMATION.name,
        )

        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user

        # Target url
        cls.url = resolve_url(
            "admission_api_v1:continuing-specific-questions",
            uuid=cls.admission.uuid,
            tab=Onglets.CHOIX_FORMATION.name,
        )

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'patch', 'post', 'put']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_with_other_candidate_user(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_with_valid_candidate_user(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    'uuid': 'fe254203-17c7-47d6-95e4-3c5c532da551',
                    'type': TypeItemFormulaire.MESSAGE.name,
                    'required': False,
                    'title': {},
                    'text': {'en': 'My very short message.', 'fr-be': 'Mon très court message.'},
                    'help_text': {},
                    'configuration': {},
                    'values': [],
                },
            ],
        )


class GeneralEducationSpecificQuestionUpdateApiTestCase(APITestCase):
    def setUp(self):
        # Mock osis-document
        self.confirm_remote_upload_patcher = patch('osis_document.api.utils.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'

        patcher = patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, att_values, __: ['4bdffb42-552d-415d-9e4c-725f10dce228' for value in att_values]
        self.addCleanup(patcher.stop)

        self.get_remote_metadata_patcher = patch('osis_document.api.utils.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf"}

        patcher = patch("osis_document.api.utils.declare_remote_files_as_deleted")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_several_remote_metadata",
            side_effect=lambda tokens: {token: {"name": "test.pdf"} for token in tokens},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.get_remote_token_patcher = patch('osis_document.api.utils.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'b-token'

        self.save_raw_content_remotely_patcher = patch('osis_document.utils.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'

    @classmethod
    def setUpTestData(cls):
        # Data
        cls.admission = GeneralEducationAdmissionFactory(training__academic_year__year=2020)

        cls.message_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year__year=2020,
            weight=1,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
        )

        cls.diplomatic_post = DiplomaticPostFactory()

        cls.update_data = {
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
            },
            'documents_additionnels': ['uuid'],
            'poste_diplomatique': cls.diplomatic_post.code,
        }

        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user

        # Target url
        cls.url = resolve_url("admission_api_v1:general_specific_question", uuid=cls.admission.uuid)

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.put(self.url, data=self.update_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'patch', 'post', 'get']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url, data=self.update_data)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_with_other_candidate_user(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.put(self.url, data=self.update_data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @freezegun.freeze_time('2020-11-01')
    def test_with_valid_candidate_user(self):
        AdmissionAcademicCalendarFactory.produce_all_required(current_year=2020)
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data=self.update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                'uuid': str(self.admission.uuid),
            },
        )

        admission = GeneralEducationAdmission.objects.get(uuid=self.admission.uuid)
        self.assertEqual(
            admission.specific_question_answers,
            {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
            },
        )
        self.assertEqual(
            str(admission.additional_documents[0]),
            '4bdffb42-552d-415d-9e4c-725f10dce228',
        )
        self.assertEqual(admission.diplomatic_post, self.diplomatic_post)
        self.assertEqual(admission.modified_at, datetime.datetime.today())
        self.assertEqual(admission.last_update_author, self.candidate.user.person)

        # Unknown diplomatic post
        response = self.client.put(
            self.url,
            data={
                **self.update_data,
                'poste_diplomatique': -1,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_result = response.json()

        self.assertIn('non_field_errors', json_result)
        self.assertIn(
            {
                'status_code': PosteDiplomatiqueNonTrouveException.status_code,
                'detail': gettext('No diplomatic post found.'),
            },
            json_result['non_field_errors'],
        )


@freezegun.freeze_time('2020-01-01')
class ContinuingEducationSpecificQuestionUpdateApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        cls.admission = ContinuingEducationAdmissionFactory(training__academic_year__year=2020)
        be_country = CountryFactory(iso_code=BE_ISO_CODE)
        AdmissionAcademicCalendarFactory.produce_all_required()

        cls.message_instantiation = AdmissionFormItemInstantiationFactory(
            form_item=TextAdmissionFormItemFactory(
                uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da551'),
                internal_label='text_item',
            ),
            academic_year__year=2020,
            weight=1,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
        )

        cls.update_data = {
            'reponses_questions_specifiques': {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
            },
            'copie_titre_sejour': ['uuid'],
            'documents_additionnels': ['uuid'],
        }

        cls.update_data_without_custom_address = {
            **cls.update_data,
            'inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
            'nom_siege_social': 'UCL',
            'numero_unique_entreprise': '1234',
            'numero_tva_entreprise': '1234A',
            'adresse_mail_professionnelle': 'john.doe@example.be',
            'type_adresse_facturation': ChoixTypeAdresseFacturation.RESIDENTIEL.name,
        }

        cls.update_data_with_custom_address = {
            **cls.update_data_without_custom_address,
            'type_adresse_facturation': ChoixTypeAdresseFacturation.AUTRE.name,
            'adresse_facturation_rue': 'rue du moulin',
            'adresse_facturation_numero_rue': '1',
            'adresse_facturation_code_postal': '1348',
            'adresse_facturation_ville': 'Louvain-la-Neuve',
            'adresse_facturation_pays': 'BE',
            'adresse_facturation_destinataire': 'John Doe',
            'adresse_facturation_boite_postale': 'B1',
        }
        AdmissionAcademicCalendarFactory.produce_all_required()

        # Users
        cls.candidate = cls.admission.candidate
        cls.other_candidate_user = CandidateFactory(person__first_name="Jim").person.user
        cls.no_role_user = PersonFactory(first_name="Joe").user

        # Target url
        cls.url = resolve_url("admission_api_v1:continuing_specific_question", uuid=cls.admission.uuid)

    def setUp(self):
        # Mock osis-document
        self.confirm_remote_upload_patcher = patch('osis_document.api.utils.confirm_remote_upload')
        patched = self.confirm_remote_upload_patcher.start()
        patched.return_value = '4bdffb42-552d-415d-9e4c-725f10dce228'

        self.get_remote_metadata_patcher = patch('osis_document.api.utils.get_remote_metadata')
        patched = self.get_remote_metadata_patcher.start()
        patched.return_value = {"name": "test.pdf"}

        patcher = patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, att_values, __: ['4bdffb42-552d-415d-9e4c-725f10dce228' for value in att_values]
        self.addCleanup(patcher.stop)

        patcher = patch("osis_document.api.utils.declare_remote_files_as_deleted")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_several_remote_metadata",
            side_effect=lambda tokens: {token: {"name": "test.pdf"} for token in tokens},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.get_remote_token_patcher = patch('osis_document.api.utils.get_remote_token')
        patched = self.get_remote_token_patcher.start()
        patched.return_value = 'b-token'

        self.save_raw_content_remotely_patcher = patch('osis_document.utils.save_raw_content_remotely')
        patched = self.save_raw_content_remotely_patcher.start()
        patched.return_value = 'a-token'

    def test_user_not_logged_assert_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.put(self.url, data=self.update_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assert_methods_not_allowed(self):
        self.client.force_authenticate(user=self.candidate.user)
        methods_not_allowed = ['delete', 'patch', 'post', 'get']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url, data=self.update_data)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_with_other_candidate_user(self):
        self.client.force_authenticate(user=self.other_candidate_user)
        response = self.client.put(self.url, data=self.update_data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @freezegun.freeze_time('2020-11-01')
    def test_with_valid_candidate_user_lite_data(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data=self.update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                'uuid': str(self.admission.uuid),
            },
        )

        admission = ContinuingEducationAdmission.objects.get(uuid=self.admission.uuid)
        self.assertEqual(
            admission.specific_question_answers,
            {
                'fe254203-17c7-47d6-95e4-3c5c532da551': 'My response',
            },
        )
        self.assertEqual(
            str(admission.residence_permit[0]),
            '4bdffb42-552d-415d-9e4c-725f10dce228',
        )
        self.assertEqual(
            str(admission.additional_documents[0]),
            '4bdffb42-552d-415d-9e4c-725f10dce228',
        )

    @freezegun.freeze_time('2020-11-01')
    def test_with_valid_candidate_user_full_data_without_custom_billing_address(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data=self.update_data_without_custom_address)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'uuid': str(self.admission.uuid)})

        admission = ContinuingEducationAdmission.objects.get(uuid=self.admission.uuid)

        self.assertEqual(
            admission.registration_as,
            self.update_data_without_custom_address['inscription_a_titre'],
        )
        self.assertEqual(
            admission.head_office_name,
            self.update_data_without_custom_address['nom_siege_social'],
        )
        self.assertEqual(
            admission.unique_business_number,
            self.update_data_without_custom_address['numero_unique_entreprise'],
        )
        self.assertEqual(
            admission.vat_number,
            self.update_data_without_custom_address['numero_tva_entreprise'],
        )
        self.assertEqual(
            admission.professional_email,
            self.update_data_without_custom_address['adresse_mail_professionnelle'],
        )
        self.assertEqual(
            admission.billing_address_type,
            self.update_data_without_custom_address['type_adresse_facturation'],
        )

    @freezegun.freeze_time('2020-11-01')
    def test_with_valid_candidate_user_full_data_with_custom_billing_address(self):
        self.client.force_authenticate(user=self.candidate.user)

        response = self.client.put(self.url, data=self.update_data_with_custom_address)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'uuid': str(self.admission.uuid)})

        admission = ContinuingEducationAdmission.objects.get(uuid=self.admission.uuid)

        self.assertEqual(
            admission.registration_as,
            self.update_data_with_custom_address['inscription_a_titre'],
        )
        self.assertEqual(
            admission.head_office_name,
            self.update_data_with_custom_address['nom_siege_social'],
        )
        self.assertEqual(
            admission.unique_business_number,
            self.update_data_with_custom_address['numero_unique_entreprise'],
        )
        self.assertEqual(
            admission.vat_number,
            self.update_data_with_custom_address['numero_tva_entreprise'],
        )
        self.assertEqual(
            admission.professional_email,
            self.update_data_with_custom_address['adresse_mail_professionnelle'],
        )
        self.assertEqual(
            admission.billing_address_type,
            self.update_data_with_custom_address['type_adresse_facturation'],
        )
        self.assertEqual(
            admission.billing_address_recipient,
            self.update_data_with_custom_address['adresse_facturation_destinataire'],
        )
        self.assertEqual(
            admission.billing_address_street,
            self.update_data_with_custom_address['adresse_facturation_rue'],
        )
        self.assertEqual(
            admission.billing_address_street_number,
            self.update_data_with_custom_address['adresse_facturation_numero_rue'],
        )
        self.assertEqual(
            admission.billing_address_postal_box,
            self.update_data_with_custom_address['adresse_facturation_boite_postale'],
        )
        self.assertEqual(
            admission.billing_address_postal_code,
            self.update_data_with_custom_address['adresse_facturation_code_postal'],
        )
        self.assertEqual(
            admission.billing_address_city,
            self.update_data_with_custom_address['adresse_facturation_ville'],
        )
        self.assertEqual(
            admission.billing_address_country.iso_code,
            self.update_data_with_custom_address['adresse_facturation_pays'],
        )
