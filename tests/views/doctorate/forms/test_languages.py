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

from django.db.models import QuerySet
from django.forms.widgets import HiddenInput
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixTypeAdmission,
    ChoixTypeContratTravail,
    ChoixTypeFinancement,
    ChoixStatutPropositionDoctorale,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.language import LanguageKnowledgeFactory
from admission.tests.factories.roles import (
    ProgramManagerRoleFactory,
    CentralManagerRoleFactory,
)
from base.forms.utils import FIELD_REQUIRED_MESSAGE
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from osis_profile.models.education import LanguageKnowledge
from osis_profile.models.enums.education import LanguageKnowledgeGrade
from reference.tests.factories.language import LanguageFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class DoctorateAdmissionLanguagesFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create some academic years
        academic_years = [AcademicYearFactory(year=year) for year in [2021, 2022]]

        # First entity
        first_doctoral_commission = EntityFactory()
        EntityVersionFactory(entity=first_doctoral_commission, acronym=ENTITY_CDE)

        # Create admissions
        cls.admission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            financing_type=ChoixTypeFinancement.WORK_CONTRACT.name,
            financing_work_contract=ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
            submitted_at=datetime.datetime.now(),
            submitted=True,
        )

        # Create languages
        cls.languages = [LanguageFactory(code=code) for code in ['EN', 'FR', 'IT', 'NL', 'ZH']]

        # Users
        cls.sic_user = CentralManagerRoleFactory(entity=first_doctoral_commission).person.user
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.admission.training.education_group
        ).person.user

        # Urls
        cls.url = reverse('admission:doctorate:update:languages', args=[cls.admission.uuid])
        cls.details_url = reverse('admission:doctorate:languages', args=[cls.admission.uuid])

    def setUp(self) -> None:
        # Mock documents
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", "mimetype": "application/pdf", "size": 1},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch(
            "osis_document.api.utils.confirm_remote_upload",
            side_effect=lambda token, *args, **kwargs: token,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.contrib.fields.FileField._confirm_multiple_upload",
            side_effect=lambda _, value, __: value,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_access(self):
        # Anonymous user
        self.client.force_login(user=UserFactory())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

        # SIC
        self.client.force_login(user=self.sic_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Program manager
        other_admission = DoctorateAdmissionFactory(
            training=self.admission.training,
            candidate=self.admission.candidate,
            status=ChoixStatutPropositionDoctorale.TRAITEMENT_FAC.name,
        )
        self.client.force_login(user=self.program_manager_user)
        response = self.client.get(reverse('admission:doctorate:update:languages', args=[other_admission.uuid]))
        self.assertEqual(response.status_code, 200)

    def test_form_initialization(self):
        self.client.force_login(user=self.sic_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        formset = response.context['formset']
        self.assertEqual(len(formset.forms), 0)

        # Add languages

        # Require language
        en_language_knowledge = LanguageKnowledgeFactory(
            person=self.admission.candidate,
            language__code='EN',
            listening_comprehension=LanguageKnowledgeGrade.A1.name,
            speaking_ability=LanguageKnowledgeGrade.A2.name,
            writing_ability=LanguageKnowledgeGrade.B1.name,
            certificate=[],
        )

        # Facultative language
        nl_language_knowledge = LanguageKnowledgeFactory(
            person=self.admission.candidate,
            language__code='NL',
            listening_comprehension=LanguageKnowledgeGrade.B1.name,
            speaking_ability=LanguageKnowledgeGrade.B2.name,
            writing_ability=LanguageKnowledgeGrade.C1.name,
            certificate=[],
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        formset = response.context['formset']
        self.assertEqual(len(formset.forms), 2)

        # EN form
        form = formset.forms[0]
        self.assertEqual(form.instance, en_language_knowledge)
        self.assertEqual(form.instance_language, en_language_knowledge.language.name)
        self.assertEqual(form.is_required, True)
        self.assertIsInstance(form.fields['language'].widget, HiddenInput)
        self.assertEqual(form.fields['language'].disabled, True)

        self.assertEqual(form['language'].value(), en_language_knowledge.language.pk)
        self.assertEqual(form['listening_comprehension'].value(), en_language_knowledge.listening_comprehension)
        self.assertEqual(form['speaking_ability'].value(), en_language_knowledge.speaking_ability)
        self.assertEqual(form['writing_ability'].value(), en_language_knowledge.writing_ability)
        self.assertEqual(form['certificate'].value(), en_language_knowledge.certificate)

        # NL form
        form = formset.forms[1]
        self.assertEqual(form.instance, nl_language_knowledge)
        self.assertEqual(form.instance_language, nl_language_knowledge.language.name)
        self.assertEqual(form.is_required, False)
        self.assertNotIsInstance(form.fields['language'].widget, HiddenInput)
        self.assertEqual(form.fields['language'].disabled, False)

        self.assertEqual(form['language'].value(), nl_language_knowledge.language.pk)
        self.assertEqual(form['listening_comprehension'].value(), nl_language_knowledge.listening_comprehension)
        self.assertEqual(form['speaking_ability'].value(), nl_language_knowledge.speaking_ability)
        self.assertEqual(form['writing_ability'].value(), nl_language_knowledge.writing_ability)
        self.assertEqual(form['certificate'].value(), nl_language_knowledge.certificate)

    def test_form_submit_with_duplicate_languages(self):
        self.client.force_login(user=self.sic_user)

        response = self.client.post(
            self.url,
            data={
                'form-0-language': self.languages[0].pk,
                'form-0-listening_comprehension': '1',
                'form-0-speaking_ability': '1',
                'form-0-writing_ability': '3',
                'form-0-certificate': [uuid.uuid4()],
                'form-1-language': self.languages[0].pk,
                'form-1-listening_comprehension': '5',
                'form-1-speaking_ability': '6',
                'form-1-writing_ability': '1',
                'form-1-certificate': [uuid.uuid4()],
                'form-2-language': self.languages[1].pk,
                'form-2-listening_comprehension': '5',
                'form-2-speaking_ability': '6',
                'form-2-writing_ability': '1',
                'form-2-certificate': [uuid.uuid4()],
                'form-INITIAL_FORMS': 0,
                'form-TOTAL_FORMS': 3,
            },
        )

        self.assertEqual(response.status_code, 200)

        formset = response.context['formset']

        self.assertFalse(formset.is_valid())

        self.assertIn(
            gettext('This language is set more than once.'),
            formset.forms[0].errors.get('language', []),
        )

        self.assertCountEqual(
            formset.non_form_errors(),
            [
                gettext('You cannot enter a language more than once, please correct the form.'),
            ],
        )

    def test_form_submit_with_missing_required_languages(self):
        self.client.force_login(user=self.sic_user)

        response = self.client.post(
            self.url,
            data={
                'form-0-language': self.languages[2].pk,
                'form-0-listening_comprehension': '1',
                'form-0-speaking_ability': '1',
                'form-0-writing_ability': '3',
                'form-0-certificate': [uuid.uuid4()],
                'form-INITIAL_FORMS': 0,
                'form-TOTAL_FORMS': 1,
            },
        )

        self.assertEqual(response.status_code, 200)

        formset = response.context['formset']

        self.assertFalse(formset.is_valid())

        non_form_errors = formset.non_form_errors()

        self.assertEqual(len(non_form_errors), 1)
        self.assertRegex(
            non_form_errors[0],
            r'^Des langues obligatoires sont manquantes \((EN, FR)|(FR, EN)\).$',
        )

    def test_form_submit_with_missing_data(self):
        self.client.force_login(user=self.sic_user)

        response = self.client.post(
            self.url,
            data={
                'form-0-language': self.languages[0].pk,
                'form-INITIAL_FORMS': 0,
                'form-TOTAL_FORMS': 1,
            },
        )

        self.assertEqual(response.status_code, 200)

        formset = response.context['formset']

        self.assertFalse(formset.is_valid())

        form = formset.forms[0]

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('listening_comprehension', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('speaking_ability', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('writing_ability', []))

    def test_form_submit_with_valid_data(self):
        self.client.force_login(user=self.sic_user)

        certificates = [[uuid.uuid4()] for _ in range(5)]

        # Create the new language knowledge
        response = self.client.post(
            self.url,
            data={
                'form-0-language': self.languages[0].pk,
                'form-0-listening_comprehension': '1',
                'form-0-speaking_ability': '2',
                'form-0-writing_ability': '3',
                'form-0-certificate_0': certificates[0],
                'form-1-language': self.languages[1].pk,
                'form-1-listening_comprehension': '2',
                'form-1-speaking_ability': '3',
                'form-1-writing_ability': '4',
                'form-1-certificate_0': certificates[1],
                'form-2-language': self.languages[2].pk,
                'form-2-listening_comprehension': '3',
                'form-2-speaking_ability': '4',
                'form-2-writing_ability': '5',
                'form-2-certificate_0': certificates[2],
                'form-INITIAL_FORMS': 0,
                'form-TOTAL_FORMS': 3,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response=response, expected_url=self.details_url)

        language_knowledge: QuerySet[LanguageKnowledge] = self.admission.candidate.languages_knowledge.all().order_by(
            'language__code'
        )

        self.assertEqual(len(language_knowledge), 3)

        self.assertEqual(language_knowledge[0].language, self.languages[0])
        self.assertEqual(language_knowledge[0].listening_comprehension, LanguageKnowledgeGrade.A1.name)
        self.assertEqual(language_knowledge[0].speaking_ability, LanguageKnowledgeGrade.A2.name)
        self.assertEqual(language_knowledge[0].writing_ability, LanguageKnowledgeGrade.B1.name)
        self.assertEqual(language_knowledge[0].certificate, certificates[0])

        self.assertEqual(language_knowledge[1].language, self.languages[1])
        self.assertEqual(language_knowledge[1].listening_comprehension, LanguageKnowledgeGrade.A2.name)
        self.assertEqual(language_knowledge[1].speaking_ability, LanguageKnowledgeGrade.B1.name)
        self.assertEqual(language_knowledge[1].writing_ability, LanguageKnowledgeGrade.B2.name)
        self.assertEqual(language_knowledge[1].certificate, certificates[1])

        self.assertEqual(language_knowledge[2].language, self.languages[2])
        self.assertEqual(language_knowledge[2].listening_comprehension, LanguageKnowledgeGrade.B1.name)
        self.assertEqual(language_knowledge[2].speaking_ability, LanguageKnowledgeGrade.B2.name)
        self.assertEqual(language_knowledge[2].writing_ability, LanguageKnowledgeGrade.C1.name)
        self.assertEqual(language_knowledge[2].certificate, certificates[2])

        # Update the existing ones / Add a new one
        response = self.client.post(
            self.url,
            data={
                'form-0-id': language_knowledge[0].pk,
                'form-0-language': self.languages[0].pk,
                'form-0-listening_comprehension': '3',
                'form-0-speaking_ability': '2',
                'form-0-writing_ability': '1',
                'form-0-certificate_0': certificates[0],
                'form-1-id': language_knowledge[1].pk,
                'form-1-language': self.languages[1].pk,
                'form-1-listening_comprehension': '4',
                'form-1-speaking_ability': '3',
                'form-1-writing_ability': '2',
                'form-1-certificate_0': certificates[1],
                'form-2-id': language_knowledge[2].pk,
                'form-2-language': self.languages[3].pk,
                'form-2-listening_comprehension': '5',
                'form-2-speaking_ability': '4',
                'form-2-writing_ability': '3',
                'form-2-certificate_0': certificates[3],
                'form-3-language': self.languages[4].pk,
                'form-3-listening_comprehension': '5',
                'form-3-speaking_ability': '1',
                'form-3-writing_ability': '2',
                'form-3-certificate_0': certificates[4],
                'form-INITIAL_FORMS': 3,
                'form-TOTAL_FORMS': 4,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response=response, expected_url=self.details_url)

        language_knowledge: QuerySet[LanguageKnowledge] = self.admission.candidate.languages_knowledge.all().order_by(
            'language__code'
        )

        self.assertEqual(len(language_knowledge), 4)

        self.assertEqual(language_knowledge[0].language, self.languages[0])
        self.assertEqual(language_knowledge[0].listening_comprehension, LanguageKnowledgeGrade.B1.name)
        self.assertEqual(language_knowledge[0].speaking_ability, LanguageKnowledgeGrade.A2.name)
        self.assertEqual(language_knowledge[0].writing_ability, LanguageKnowledgeGrade.A1.name)
        self.assertEqual(language_knowledge[0].certificate, certificates[0])

        self.assertEqual(language_knowledge[1].language, self.languages[1])
        self.assertEqual(language_knowledge[1].listening_comprehension, LanguageKnowledgeGrade.B2.name)
        self.assertEqual(language_knowledge[1].speaking_ability, LanguageKnowledgeGrade.B1.name)
        self.assertEqual(language_knowledge[1].writing_ability, LanguageKnowledgeGrade.A2.name)
        self.assertEqual(language_knowledge[1].certificate, certificates[1])

        self.assertEqual(language_knowledge[2].language, self.languages[3])
        self.assertEqual(language_knowledge[2].listening_comprehension, LanguageKnowledgeGrade.C1.name)
        self.assertEqual(language_knowledge[2].speaking_ability, LanguageKnowledgeGrade.B2.name)
        self.assertEqual(language_knowledge[2].writing_ability, LanguageKnowledgeGrade.B1.name)
        self.assertEqual(language_knowledge[2].certificate, certificates[3])

        self.assertEqual(language_knowledge[3].language, self.languages[4])
        self.assertEqual(language_knowledge[3].listening_comprehension, LanguageKnowledgeGrade.C1.name)
        self.assertEqual(language_knowledge[3].speaking_ability, LanguageKnowledgeGrade.A1.name)
        self.assertEqual(language_knowledge[3].writing_ability, LanguageKnowledgeGrade.A2.name)
        self.assertEqual(language_knowledge[3].certificate, certificates[4])

        # Remove the unused ones
        response = self.client.post(
            self.url,
            data={
                'form-0-id': language_knowledge[0].pk,
                'form-0-DELETE': '',
                'form-0-language': self.languages[0].pk,
                'form-0-listening_comprehension': '3',
                'form-0-speaking_ability': '2',
                'form-0-writing_ability': '1',
                'form-0-certificate_0': certificates[0],
                'form-1-id': language_knowledge[1].pk,
                'form-1-DELETE': '',
                'form-1-language': self.languages[1].pk,
                'form-1-listening_comprehension': '4',
                'form-1-speaking_ability': '3',
                'form-1-writing_ability': '2',
                'form-1-certificate_0': certificates[1],
                'form-2-id': language_knowledge[2].pk,
                'form-2-DELETE': 'on',
                'form-2-language': self.languages[3].pk,
                'form-2-listening_comprehension': '5',
                'form-2-speaking_ability': '4',
                'form-2-writing_ability': '3',
                'form-2-certificate_0': certificates[3],
                'form-3-id': language_knowledge[3].pk,
                'form-3-DELETE': 'on',
                'form-3-language': self.languages[4].pk,
                'form-3-listening_comprehension': '5',
                'form-3-speaking_ability': '1',
                'form-3-writing_ability': '2',
                'form-3-certificate_0': certificates[4],
                'form-INITIAL_FORMS': 4,
                'form-TOTAL_FORMS': 4,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response=response, expected_url=self.details_url)

        language_knowledge: QuerySet[LanguageKnowledge] = self.admission.candidate.languages_knowledge.all().order_by(
            'language__code'
        )

        self.assertEqual(len(language_knowledge), 2)

        self.assertEqual(language_knowledge[0].language, self.languages[0])
        self.assertEqual(language_knowledge[0].listening_comprehension, LanguageKnowledgeGrade.B1.name)
        self.assertEqual(language_knowledge[0].speaking_ability, LanguageKnowledgeGrade.A2.name)
        self.assertEqual(language_knowledge[0].writing_ability, LanguageKnowledgeGrade.A1.name)
        self.assertEqual(language_knowledge[0].certificate, certificates[0])

        self.assertEqual(language_knowledge[1].language, self.languages[1])
        self.assertEqual(language_knowledge[1].listening_comprehension, LanguageKnowledgeGrade.B2.name)
        self.assertEqual(language_knowledge[1].speaking_ability, LanguageKnowledgeGrade.B1.name)
        self.assertEqual(language_knowledge[1].writing_ability, LanguageKnowledgeGrade.A2.name)
        self.assertEqual(language_knowledge[1].certificate, certificates[1])
