# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.doctorat.preparation.domain.model.doctorat_formation import (
    ENTITY_CDE,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixTypeAdmission,
)
from admission.models import DoctorateAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.roles import ProgramManagerRoleFactory
from base.models.enums.entity_type import EntityType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.user import UserFactory
from reference.tests.factories.language import EnglishLanguageFactory, LanguageFactory


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

        cls.institute = EntityVersionFactory(entity_type=EntityType.INSTITUTE.name)
        cls.other_institute = EntityVersionFactory(entity_type=EntityType.INSTITUTE.name)

        cls.language = LanguageFactory()
        cls.other_language = LanguageFactory()

        # Create admissions
        cls.admission: DoctorateAdmission = DoctorateAdmissionFactory(
            training__management_entity=first_doctoral_commission,
            training__academic_year=academic_years[0],
            proximity_commission=ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
            type=ChoixTypeAdmission.ADMISSION.name,
            thesis_institute=cls.institute,
            thesis_language=cls.language,
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
        patcher = patch("osis_document.api.utils.get_remote_token", side_effect=lambda value, **kwargs: value)
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

        form = response.context['form']

        self.assertEqual(form['lieu_these'].value(), self.admission.thesis_location)
        self.assertEqual(form['titre_projet'].value(), self.admission.project_title)
        self.assertEqual(form['resume_projet'].value(), self.admission.project_abstract)
        self.assertEqual(form['documents_projet'].value(), self.admission.project_document)
        self.assertEqual(form['graphe_gantt'].value(), self.admission.gantt_graph)
        self.assertEqual(form['proposition_programme_doctoral'].value(), self.admission.program_proposition)
        self.assertEqual(form['projet_formation_complementaire'].value(), self.admission.additional_training_project)
        self.assertEqual(form['lettres_recommandation'].value(), self.admission.recommendation_letters)
        self.assertEqual(form['langue_redaction_these'].value(), self.admission.thesis_language.code)
        self.assertEqual(form['institut_these'].value(), self.admission.thesis_institute.uuid)
        self.assertEqual(form['projet_doctoral_deja_commence'].value(), False)
        self.assertEqual(form['projet_doctoral_institution'].value(), self.admission.phd_alread_started_institute)
        self.assertEqual(form['projet_doctoral_date_debut'].value(), self.admission.work_start_date)
        self.assertEqual(form['doctorat_deja_realise'].value(), self.admission.phd_already_done)
        self.assertEqual(form['institution'].value(), self.admission.phd_already_done_institution)
        self.assertEqual(form['domaine_these'].value(), self.admission.phd_already_done_thesis_domain)
        self.assertEqual(form['non_soutenue'].value(), None)
        self.assertEqual(form['date_soutenance'].value(), self.admission.phd_already_done_defense_date)
        self.assertEqual(form['raison_non_soutenue'].value(), self.admission.phd_already_done_no_defense_reason)

        self.assertCountEqual(
            form.fields['institut_these'].widget.choices,
            ((self.institute.uuid, f'{self.institute.title} ({self.institute.acronym})'),),
        )

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
            "langue_redaction_these": self.other_language.code,
            "institut_these": str(self.other_institute.uuid),
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

        self.admission.refresh_from_db()

        self.assertEqual(self.admission.thesis_location, data['lieu_these'])
        self.assertEqual(self.admission.project_title, data['titre_projet'])
        self.assertEqual(self.admission.project_abstract, data['resume_projet'])
        self.assertEqual(self.admission.project_document, [uuid.UUID(data['documents_projet_0'])])
        self.assertEqual(self.admission.gantt_graph, [])
        self.assertEqual(self.admission.program_proposition, [uuid.UUID(data['proposition_programme_doctoral_0'])])
        self.assertEqual(self.admission.additional_training_project, [])
        self.assertEqual(self.admission.recommendation_letters, [])
        self.assertEqual(self.admission.thesis_language.code, data['langue_redaction_these'])
        self.assertEqual(self.admission.thesis_institute.uuid, self.other_institute.uuid)
        self.assertEqual(self.admission.phd_alread_started, True)
        self.assertEqual(self.admission.phd_alread_started_institute, data['projet_doctoral_institution'])
        self.assertEqual(self.admission.work_start_date, datetime.date(2222, 12, 12))
        self.assertEqual(self.admission.phd_already_done, data['doctorat_deja_realise'])
        self.assertEqual(self.admission.phd_already_done_institution, '')
        self.assertEqual(self.admission.phd_already_done_thesis_domain, '')
        self.assertEqual(self.admission.phd_already_done_defense_date, None)
        self.assertEqual(self.admission.phd_already_done_no_defense_reason, '')

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
