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
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import ENTITY_CDE
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixTypeAdmission,
)
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import ProgramManagerRoleFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from reference.tests.factories.language import EnglishLanguageFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class ProjectViewTestCase(TestCase):
    @classmethod
    def get_scholarship(cls, uuid, **kwargs):
        return next((scholarship for scholarship in cls.mock_scholarships if scholarship.uuid == uuid), None)

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
            proximity_commission=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
            type=ChoixTypeAdmission.ADMISSION.name,
        )

        cls.pre_admission = DoctorateAdmissionFactory(
            training=cls.admission.training,
            type=ChoixTypeAdmission.PRE_ADMISSION.name,
        )

        EnglishLanguageFactory()

        # Users
        cls.program_manager_user = ProgramManagerRoleFactory(
            education_group=cls.admission.training.education_group
        ).person.user

        # Urls
        cls.url = reverse('admission:doctorate:update:project', args=[cls.admission.uuid])
        cls.pre_admission_url = reverse('admission:doctorate:update:project', args=[cls.pre_admission.uuid])
        cls.details_url = reverse('admission:doctorate:project', args=[cls.admission.uuid])

    def setUp(self):
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

    def test_detail_no_permission(self):
        # Anonymous user
        self.client.force_login(user=UserFactory())
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 403)

    def test_detail(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.get(self.details_url)
        self.assertTemplateUsed(response, 'admission/doctorate/details/project.html')

    def test_update_no_permission(self):
        # Anonymous user
        self.client.force_login(user=UserFactory())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_update_get(self):
        self.client.force_login(user=self.program_manager_user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'admission/doctorate/forms/project.html')

    def test_update_post(self):
        self.client.force_login(user=self.program_manager_user)
        data = {
            "type_financement": "WORK_CONTRACT",
            "type_contrat_travail": "other",
            "type_contrat_travail_other": "test+test",
            "eft": "12",
            "duree_prevue": "21",
            "temps_consacre": "12",
            "est_lie_fnrs_fria_fresh_csc": "False",
            "commentaire_financement": "rrgrgr",
            "titre_projet": "ffdbfbd",
            "resume_projet": "bfdbfd",
            "langue_redaction_these": "EN",
            "lieu_these": "",
            "documents_projet_0": "34eab30c-27e3-40db-b92e-0b51546a2448",
            "proposition_programme_doctoral_0": "34eab30c-27e3-40db-b92e-0b51546a2448",
            "projet_doctoral_deja_commence": "True",
            "projet_doctoral_institution": "Institution",
            "projet_doctoral_date_debut": "12/12/2222",
            "doctorat_deja_realise": "NO",
        }
        response = self.client.post(self.url, data, follow=True)
        self.assertTemplateUsed(response, 'admission/doctorate/details/project.html')

    def test_update_get_field_label_classes(self):
        self.client.force_login(user=self.program_manager_user)

        response = self.client.get(self.pre_admission_url)

        form = response.context['form']

        required_fields = {
            'justification',
            'type_contrat_travail',
            'eft',
            'bourse_recherche',
            'autre_bourse_recherche',
            'raison_non_soutenue',
            'titre_projet',
        }

        for field in form.fields:
            self.assertEqual(form.label_classes.get(field), 'required_text' if field in required_fields else None)

        response = self.client.get(self.url)

        form = response.context['form']

        required_fields = {
            'justification',
            'type_contrat_travail',
            'eft',
            'bourse_recherche',
            'autre_bourse_recherche',
            'raison_non_soutenue',
            'titre_projet',
            'type_financement',
            'bourse_date_debut',
            'bourse_date_fin',
            'bourse_preuve',
            'duree_prevue',
            'temps_consacre',
            'est_lie_fnrs_fria_fresh_csc',
            'resume_projet',
            'documents_projet',
            'proposition_programme_doctoral',
            'langue_redaction_these',
            'projet_doctoral_deja_commence',
            'projet_doctoral_institution',
            'projet_doctoral_date_debut',
            'institution',
            'domaine_these',
        }

        for field in form.fields:
            self.assertEqual(form.label_classes.get(field), 'required_text' if field in required_fields else None)
