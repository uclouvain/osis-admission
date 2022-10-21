# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

from django.shortcuts import resolve_url
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd import BE_ISO_CODE, FR_ISO_CODE, EN_ISO_CODE
from admission.ddd.admission.enums.question_specifique import (
    Onglets,
    CritereItemFormulaireFormation,
    CritereItemFormulaireNationaliteCandidat,
    CritereItemFormulaireLangueEtudes,
    CritereItemFormulaireVIP,
    TypeItemFormulaire,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.continuing_education import ContinuingEducationAdmissionFactory
from admission.tests.factories.form_item import (
    MessageAdmissionFormItemFactory,
    TextAdmissionFormItemFactory,
    DocumentAdmissionFormItemFactory,
    AdmissionFormItemInstantiationFactory,
)
from admission.tests.factories.general_education import GeneralEducationAdmissionFactory
from admission.tests.factories.roles import CandidateFactory, CddManagerFactory
from admission.tests.factories.scholarship import ErasmusMundusScholarshipFactory
from admission.tests.factories.secondary_studies import BelgianHighSchoolDiplomaFactory, ForeignHighSchoolDiplomaFactory
from admission.tests.factories.supervision import PromoterFactory
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


class BaseDoctorateSpecificQuestionApiTestCase(APITestCase):
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
            internal_label='message_item',
            text={'en': 'My very short message.', 'fr-be': 'Mon très court message.'},
            configuration={},
        )
        TextAdmissionFormItemFactory(
            uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da552'),
            internal_label='text_item',
            title={'en': 'Text field', 'fr-be': 'Champ texte'},
            text={'en': 'Detailed data.', 'fr-be': 'Données détaillées.'},
            help_text={'en': 'Write here', 'fr-be': 'Ecrivez ici'},
            configuration={},
        )
        DocumentAdmissionFormItemFactory(
            uuid=uuid.UUID('fe254203-17c7-47d6-95e4-3c5c532da553'),
            internal_label='document_item',
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
        cls.cdd_manager_user = CddManagerFactory(entity=cls.commission).person.user
        cls.other_cdd_manager_user = CddManagerFactory().person.user

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


class DoctorateSpecificQuestionApiTestCase(BaseDoctorateSpecificQuestionApiTestCase):
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


class DoctorateSpecificQuestionWithItemsRelatedToNoStudiesInFrenchApiTestCase(BaseDoctorateSpecificQuestionApiTestCase):
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


class DoctorateSpecificQuestionWithItemsRelatedToNoStudiesInEnglishApiTestCase(
    BaseDoctorateSpecificQuestionApiTestCase
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


class DoctorateSpecificQuestionWithItemsRelatedToVIPCandidateApiTestCase(BaseDoctorateSpecificQuestionApiTestCase):
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
        self.admission.erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory()
        self.admission.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class DoctorateSpecificQuestionWithItemsRelatedToNonVIPCandidateApiTestCase(BaseDoctorateSpecificQuestionApiTestCase):
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
        self.admission.erasmus_mundus_scholarship = ErasmusMundusScholarshipFactory()
        self.admission.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)


class DoctorateSpecificQuestionWithItemsRelatedToTheEducationApiTestCase(BaseDoctorateSpecificQuestionApiTestCase):
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
        self.message_instantiation.education_group_type = EducationGroupTypeFactory()
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


class GeneralEducationSpecificQuestionApiTestCase(APITestCase):
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
                },
            ],
        )


class ContinuingEducationSpecificQuestionApiTestCase(APITestCase):
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
                },
            ],
        )
