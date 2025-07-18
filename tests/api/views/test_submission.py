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
from email import message_from_string
from unittest.mock import MagicMock, PropertyMock, patch

import freezegun
import mock
from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext_lazy as _
from osis_history.models import HistoryEntry
from osis_notification.models import EmailNotification
from rest_framework import status
from rest_framework.test import APITestCase

from admission.ddd.admission.domain.service.i_elements_confirmation import (
    IElementsConfirmation,
)
from admission.ddd.admission.domain.validator.exceptions import (
    HorsPeriodeSpecifiqueInscription,
    NombrePropositionsSoumisesDepasseException,
    QuestionsSpecifiquesInformationsComplementairesNonCompleteesException,
    ResidenceAuSensDuDecretNonDisponiblePourInscriptionException,
)
from admission.ddd.admission.enums import (
    CritereItemFormulaireFormation,
    Onglets,
    TypeSituationAssimilation,
)
from admission.ddd.admission.enums.type_demande import TypeDemande
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    EtudesSecondairesNonCompleteesException,
)
from admission.models import AdmissionTask
from admission.tests.factories.calendar import (
    AdmissionAcademicCalendarFactory,
    AdmissionMedDentEnrollmentAcademicCalendarFactory,
)
from admission.tests.factories.continuing_education import (
    ContinuingEducationAdmissionFactory,
)
from admission.tests.factories.curriculum import ProfessionalExperienceFactory
from admission.tests.factories.faculty_decision import (
    FreeAdditionalApprovalConditionFactory,
)
from admission.tests.factories.form_item import (
    AdmissionFormItemFactory,
    AdmissionFormItemInstantiationFactory,
    TextAdmissionFormItemFactory,
)
from admission.tests.factories.general_education import (
    GeneralEducationAdmissionFactory,
    GeneralEducationTrainingFactory,
)
from admission.tests.factories.person import (
    IncompletePersonForBachelorFactory,
    IncompletePersonForIUFCFactory,
)
from admission.tests.factories.roles import ProgramManagerRoleFactory
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.academic_year import AcademicYear
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.enums.education_group_types import TrainingType
from base.models.enums.got_diploma import GotDiploma
from base.models.enums.person_address_type import PersonAddressType
from base.models.enums.state_iufc import StateIUFC
from base.models.person_address import PersonAddress
from base.tests import QueriesAssertionsMixin
from infrastructure.financabilite.domain.service.financabilite import PASS_ET_LAS_LABEL
from osis_profile import BE_ISO_CODE
from osis_profile.models import EducationalExperience, ProfessionalExperience
from reference.tests.factories.country import CountryFactory


@freezegun.freeze_time("1980-02-25")
@override_settings(WAFFLE_CREATE_MISSING_SWITCHES=False)
class GeneralPropositionSubmissionTestCase(QueriesAssertionsMixin, APITestCase):
    def setUp(self):
        # Mock publish
        patcher = mock.patch(
            'infrastructure.utils.MessageBus.publish',
        )
        self.mock_publish = patcher.start()
        self.addCleanup(patcher.stop)

    @classmethod
    def setUpTestData(cls):
        AdmissionAcademicCalendarFactory.produce_all_required(quantity=6)
        AdmissionFormItemFactory(internal_label=PASS_ET_LAS_LABEL)

        # Validation errors
        cls.candidate_errors = IncompletePersonForBachelorFactory(
            private_email='candidate1@test.be',
        )
        cls.admission = GeneralEducationAdmissionFactory(
            candidate=cls.candidate_errors,
            # force type to have access conditions
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__acronym="FOOBAR",
        )
        cls.error_url = resolve_url("admission_api_v1:submit-general-proposition", uuid=cls.admission.uuid)

        # Validation ok
        cls.admission_ok = GeneralEducationAdmissionFactory(
            training__academic_year__year=1980,
            candidate__country_of_citizenship__european_union=True,
            candidate__private_email='candidate2@test.be',
            bachelor_with_access_conditions_met=True,
            determined_academic_year__year=1980,
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__main_domain__code='11A',
        )
        FreeAdditionalApprovalConditionFactory(
            admission=cls.admission_ok,
        )
        FreeAdditionalApprovalConditionFactory(
            admission=cls.admission_ok,
        )
        cls.second_admission_ok = GeneralEducationAdmissionFactory(
            candidate__country_of_citizenship__european_union=True,
            candidate__private_email='candidate3@test.be',
            bachelor_with_access_conditions_met=True,
            training=cls.admission_ok.training,
        )
        cls.third_admission_ok = GeneralEducationAdmissionFactory(
            candidate=cls.second_admission_ok.candidate,
            bachelor_with_access_conditions_met=True,
            training=cls.admission_ok.training,
        )
        cls.candidate_ok = cls.admission_ok.candidate
        cls.candidate_ok_residential_address = PersonAddress.objects.filter(
            person=cls.candidate_ok, label=PersonAddressType.RESIDENTIAL.name
        ).first()
        cls.second_candidate_ok = cls.second_admission_ok.candidate
        cls.ok_url = resolve_url("admission_api_v1:submit-general-proposition", uuid=cls.admission_ok.uuid)
        cls.second_ok_url = resolve_url(
            "admission_api_v1:submit-general-proposition",
            uuid=cls.second_admission_ok.uuid,
        )
        cls.third_ok_url = resolve_url(
            "admission_api_v1:submit-general-proposition",
            uuid=cls.third_admission_ok.uuid,
        )
        # Ensure we have this training available for the next acad
        GeneralEducationTrainingFactory(
            academic_year__year=1980,
            education_group_type=cls.admission_ok.training.education_group_type,
            acronym=cls.admission_ok.training.acronym,
            partial_acronym=cls.admission_ok.training.partial_acronym,
        )
        cls.data_ok = {
            'pool': AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN.name,
            'annee': 1980,
            'elements_confirmation': {
                'reglement_general': IElementsConfirmation.REGLEMENT_GENERAL,
                'protection_donnees': IElementsConfirmation.PROTECTION_DONNEES,
                'professions_reglementees': IElementsConfirmation.PROFESSIONS_REGLEMENTEES,
                'justificatifs': IElementsConfirmation.JUSTIFICATIFS % {'by_service': _("by the Enrolment Office")},
                'declaration_sur_lhonneur': IElementsConfirmation.DECLARATION_SUR_LHONNEUR
                % {'to_service': _("to the UCLouvain Registration Service")},
                'convention_cadre_stages': IElementsConfirmation.CONVENTION_CADRE_STAGE,
                'communication_hopitaux': IElementsConfirmation.COMMUNICATION_HOPITAUX,
            },
        }

    def test_general_proposition_verification_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.get(self.error_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ret = response.json()
        self.assertIn("ADMISSION-2", [e["status_code"] for e in ret['errors']])
        self.assertEqual(ret['access_conditions_url'], 'https://uclouvain.be/prog-1979-FOOBAR-cond_adm')

    def test_general_proposition_submission_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        data = {
            'pool': AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN.name,
            'annee': 1980,
        }
        response = self.client.post(self.error_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_general_proposition_verification_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        with self.assertNumQueriesLessThan(79):
            response = self.client.get(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ret = response.json()
        self.assertEqual(len(ret['errors']), 0)
        self.admission_ok.refresh_from_db()

        response = self.client.get(resolve_url("admission_api_v1:general_propositions", uuid=self.admission_ok.uuid))
        ret = response.json()
        self.assertEqual(ret['pot_calcule'], AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN.name)
        self.assertIsNotNone(ret['date_fin_pot'])

    def test_general_proposition_verification_ok_valuate_experiences(self):
        educational_experience = self.second_candidate_ok.educationalexperience_set.first()
        professional_experience = self.second_candidate_ok.professionalexperience_set.first()

        self.client.force_authenticate(user=self.second_candidate_ok.user)

        # First submission
        response = self.client.post(self.second_ok_url, data=self.data_ok)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.second_admission_ok.refresh_from_db()

        # Valuation of the secondary studies
        self.assertEqual(self.second_admission_ok.valuated_secondary_studies_person, self.second_candidate_ok)

        # Valuation of the curriculum experiences
        self.assertEqual(len(self.second_admission_ok.educational_valuated_experiences.all()), 1)
        self.assertEqual(len(self.second_admission_ok.professional_valuated_experiences.all()), 1)
        self.assertEqual(
            self.second_admission_ok.educational_valuated_experiences.first().uuid,
            educational_experience.uuid,
        )
        self.assertEqual(
            self.second_admission_ok.professional_valuated_experiences.first().uuid,
            professional_experience.uuid,
        )

        # Second submission
        response = self.client.post(self.third_ok_url, data=self.data_ok)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.third_admission_ok.refresh_from_db()

        # Valuation of the secondary studies
        self.assertEqual(self.third_admission_ok.valuated_secondary_studies_person, self.third_admission_ok.candidate)

        # Valuation of the curriculum experiences
        self.assertEqual(len(self.third_admission_ok.educational_valuated_experiences.all()), 1)
        self.assertEqual(len(self.third_admission_ok.professional_valuated_experiences.all()), 1)
        self.assertEqual(
            self.third_admission_ok.educational_valuated_experiences.first().uuid,
            educational_experience.uuid,
        )
        self.assertEqual(
            self.third_admission_ok.professional_valuated_experiences.first().uuid,
            professional_experience.uuid,
        )

    @mock.patch(
        'admission.ddd.admission.domain.service.i_calendrier_inscription.ICalendrierInscription.'
        'INTERDIRE_INSCRIPTION_ETUDES_CONTINGENTES_POUR_NON_RESIDENT',
        new_callable=PropertyMock,
        return_value=False,
    )
    def test_general_proposition_verification_contingent_non_ouvert(self, _):
        admission = GeneralEducationAdmissionFactory(
            is_non_resident=True,
            candidate=IncompletePersonForBachelorFactory(),
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__acronym="VETE1BA",
        )
        url = resolve_url("admission_api_v1:submit-general-proposition", uuid=admission.uuid)
        self.client.force_authenticate(user=admission.candidate.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ret = response.json()
        self.assertIsNotNone(ret['pool_start_date'])
        self.assertIsNotNone(ret['pool_end_date'])
        admission.refresh_from_db()
        self.assertNotIn(
            {
                'status_code': ResidenceAuSensDuDecretNonDisponiblePourInscriptionException.status_code,
                'detail': ResidenceAuSensDuDecretNonDisponiblePourInscriptionException.get_message(
                    nom_formation_fr=admission.training.title,
                    nom_formation_en=admission.training.title_english,
                ),
            },
            admission.detailed_status,
        )

    def test_general_proposition_verification_specific_enrolment_period_for_medicine_dentistry_bachelor(self):
        self.client.force_authenticate(user=self.candidate_ok.user)

        # Add a specific period
        current_specific_enrolment_period = AdmissionMedDentEnrollmentAcademicCalendarFactory(
            data_year=self.admission_ok.determined_academic_year,
            start_date=datetime.date(1980, 2, 1),
            end_date=datetime.date(1980, 2, 15),
        )

        next_specific_enrolment_period = AdmissionMedDentEnrollmentAcademicCalendarFactory(
            data_year__year=self.admission_ok.determined_academic_year.year + 1,
            start_date=datetime.date(1980, 3, 1),
            end_date=datetime.date(1980, 3, 15),
        )

        # Outside a period
        with freezegun.freeze_time("1980-01-31"):
            response = self.client.get(self.ok_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            ret = response.json()
            self.assertEqual(len(ret['errors']), 1)

            not_in_period_error = next(
                (
                    error
                    for error in ret['errors']
                    if error['status_code'] == HorsPeriodeSpecifiqueInscription.status_code
                ),
                None,
            )

            self.assertIsNotNone(not_in_period_error)

            self.assertEqual(
                not_in_period_error['detail'],
                "Dans l'attente de la publication des résultats du concours d'entrée en médecine et dentisterie, "
                "votre demande ne pourra être soumise qu'à partir du 1 février 1980.",
            )

        with freezegun.freeze_time("1980-02-16"):
            response = self.client.get(self.ok_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            ret = response.json()
            self.assertEqual(len(ret['errors']), 1)

            not_in_period_error = next(
                (
                    error
                    for error in ret['errors']
                    if error['status_code'] == HorsPeriodeSpecifiqueInscription.status_code
                ),
                None,
            )

            self.assertIsNotNone(not_in_period_error)

            self.assertEqual(
                not_in_period_error['detail'],
                "Dans l'attente de la publication des résultats du concours d'entrée en médecine et dentisterie, "
                "votre demande ne pourra être soumise qu'à partir du 1 mars 1980.",
            )

        # Inside a period
        with freezegun.freeze_time("1980-02-01"):
            response = self.client.get(self.ok_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            ret = response.json()
            self.assertEqual(len(ret['errors']), 0)

    def test_general_proposition_verification_contingent_est_interdite(self):
        admission = GeneralEducationAdmissionFactory(
            is_non_resident=True,
            candidate=IncompletePersonForBachelorFactory(),
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__acronym="VETE1BA",
        )
        url = resolve_url("admission_api_v1:submit-general-proposition", uuid=admission.uuid)
        self.client.force_authenticate(user=admission.candidate.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        admission.refresh_from_db()
        self.assertIn(
            {
                'status_code': ResidenceAuSensDuDecretNonDisponiblePourInscriptionException.status_code,
                'detail': ResidenceAuSensDuDecretNonDisponiblePourInscriptionException.get_message(
                    nom_formation_fr=admission.training.title,
                    nom_formation_en=admission.training.title_english,
                ),
            },
            admission.detailed_status,
        )

    def test_general_proposition_submission_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionGenerale.EN_BROUILLON.name)
        required_admission_form_item = TextAdmissionFormItemFactory()
        AdmissionFormItemInstantiationFactory(
            form_item=required_admission_form_item,
            required=True,
            display_according_education=CritereItemFormulaireFormation.TOUTE_FORMATION.name,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            academic_year=self.admission_ok.training.academic_year,
        )
        facultative_admission_form_item = TextAdmissionFormItemFactory()
        AdmissionFormItemInstantiationFactory(
            form_item=facultative_admission_form_item,
            required=False,
            display_according_education=CritereItemFormulaireFormation.TOUTE_FORMATION.name,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            academic_year=self.admission_ok.training.academic_year,
        )
        required_admission_form_item.refresh_from_db()
        facultative_admission_form_item.refresh_from_db()
        self.admission_ok.specific_question_answers = {
            str(required_admission_form_item.uuid): 'My first answer',
            str(uuid.uuid4()): 'My second answer',
        }
        self.admission_ok.save(update_fields=['specific_question_answers'])
        response = self.client.post(self.ok_url, self.data_ok)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.admission_ok.refresh_from_db()
        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertIsNotNone(self.admission_ok.submitted_at)
        self.assertEqual(self.admission_ok.late_enrollment, False)
        self.assertEqual(self.admission_ok.last_update_author, self.admission_ok.candidate)
        self.assertEqual(
            self.admission_ok.submitted_profile,
            {
                'identification': {
                    'first_name': self.admission_ok.candidate.first_name,
                    'last_name': self.admission_ok.candidate.last_name,
                    'gender': self.admission_ok.candidate.gender,
                    'country_of_citizenship': self.admission_ok.candidate.country_of_citizenship.iso_code,
                    'date_of_birth': self.admission_ok.candidate.birth_date.isoformat(),
                },
                'coordinates': {
                    'country': self.candidate_ok_residential_address.country.iso_code,
                    'postal_code': self.candidate_ok_residential_address.postal_code,
                    'city': self.candidate_ok_residential_address.city,
                    'street': self.candidate_ok_residential_address.street,
                    'street_number': self.candidate_ok_residential_address.street_number,
                    'postal_box': self.candidate_ok_residential_address.postal_box,
                },
            },
        )
        self.assertEqual(
            self.admission_ok.specific_question_answers,
            {
                str(required_admission_form_item.uuid): 'My first answer',
                str(facultative_admission_form_item.uuid): '',
            },
        )

        history_entry: HistoryEntry = HistoryEntry.objects.filter(
            object_uuid=self.admission_ok.uuid,
            tags__contains=['proposition', 'status-changed'],
        ).last()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.message_fr, 'La proposition a été soumise.')

        admission_tasks = AdmissionTask.objects.filter(admission=self.admission_ok).order_by('type')
        self.assertEqual(len(admission_tasks), 2)
        self.assertEqual(admission_tasks[0].type, AdmissionTask.TaskType.GENERAL_MERGE.name)
        self.assertEqual(admission_tasks[1].type, AdmissionTask.TaskType.GENERAL_RECAP.name)

        notifications = EmailNotification.objects.filter(person=self.admission_ok.candidate)
        self.assertEqual(len(notifications), 1)

        email_object = message_from_string(notifications[0].payload)
        self.assertEqual(email_object['To'], 'candidate2@test.be')
        self.assertNotIn('inscription tardive', notifications[0].payload)
        self.assertNotIn('payement des frais de dossier', notifications[0].payload)

    def test_general_proposition_submission_with_specific_enrolment_period_for_medicine_dentistry_bachelor(self):
        current_admission = GeneralEducationAdmissionFactory(
            training__academic_year__year=1980,
            candidate__country_of_citizenship__european_union=True,
            candidate__private_email='candidate2@test.be',
            bachelor_with_access_conditions_met=True,
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__main_domain__code='11A',
        )

        specific_enrolment_period = AdmissionMedDentEnrollmentAcademicCalendarFactory(
            data_year=current_admission.determined_academic_year,
            start_date=datetime.date(1980, 2, 1),
            end_date=datetime.date(1980, 2, 15),
        )

        self.client.force_authenticate(user=current_admission.candidate.user)
        current_url = resolve_url("admission_api_v1:submit-general-proposition", uuid=current_admission.uuid)

        # Outside the period
        with freezegun.freeze_time(datetime.date(1980, 1, 31)):
            response = self.client.post(current_url, self.data_ok)

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            errors_statuses = [e["status_code"] for e in response.json()['non_field_errors']]
            self.assertIn(HorsPeriodeSpecifiqueInscription.status_code, errors_statuses)

        # Inside the period
        with freezegun.freeze_time(datetime.date(1980, 2, 1)):
            response = self.client.post(current_url, self.data_ok)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            current_admission.refresh_from_db()
            self.assertEqual(current_admission.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)

    def test_general_proposition_submission_ok_is_an_enrollment_or_an_admission(self):
        current_admission = GeneralEducationAdmissionFactory(
            training__academic_year__year=1980,
            candidate__country_of_citizenship__european_union=True,
            candidate__private_email='candidate2@test.be',
            bachelor_with_access_conditions_met=True,
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__main_domain__code='11A',
        )

        self.client.force_authenticate(user=current_admission.candidate.user)

        current_url = resolve_url("admission_api_v1:submit-general-proposition", uuid=current_admission.uuid)

        # UE candidate and all titles from Belgium -> enrollment
        response = self.client.post(current_url, self.data_ok)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        current_admission.refresh_from_db()
        self.assertEqual(current_admission.type_demande, TypeDemande.INSCRIPTION.name)

        notifications = EmailNotification.objects.filter(person=current_admission.candidate)
        self.assertEqual(len(notifications), 1)
        self.assertIn('juillet 1980', notifications[0].payload)

        notifications[0].delete()

        current_admission.candidate.country_of_citizenship.european_union = False
        current_admission.candidate.country_of_citizenship.save(update_fields=['european_union'])

        # Not UE candidate with assimilation and all titles from Belgium -> admission
        current_admission.accounting.assimilation_situation = (
            TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name
        )
        current_admission.accounting.cpas_certificate = [uuid.uuid4()]
        current_admission.accounting.save(update_fields=['assimilation_situation', 'cpas_certificate'])

        current_admission.status = ChoixStatutPropositionGenerale.EN_BROUILLON.name
        current_admission.save(update_fields=['status'])

        response = self.client.post(
            current_url,
            {
                **self.data_ok,
                # The pool computation does not consider a candidate with assimilation as a UE candidate
                'pool': AcademicCalendarTypes.ADMISSION_POOL_HUE_UCL_PATHWAY_CHANGE.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        current_admission.refresh_from_db()
        self.assertEqual(current_admission.type_demande, TypeDemande.ADMISSION.name)

        notifications = EmailNotification.objects.filter(person=current_admission.candidate)
        self.assertEqual(len(notifications), 1)
        self.assertNotIn('juillet 1980', notifications[0].payload)

    @freezegun.freeze_time("1980-10-22")
    def test_general_proposition_submission_with_late_enrollment(self):
        self.client.force_authenticate(user=self.candidate_ok.user)

        # The submission is in October so we need to valuate September
        ProfessionalExperienceFactory(
            person=self.candidate_ok,
            start_date=datetime.date(1980, 9, 1),
            end_date=datetime.date(1980, 9, 30),
        )

        response = self.client.post(self.ok_url, self.data_ok)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.admission_ok.refresh_from_db()
        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertEqual(self.admission_ok.late_enrollment, True)

        notifications = EmailNotification.objects.filter(person=self.admission_ok.candidate)
        self.assertEqual(len(notifications), 1)

        self.assertIn('inscription tardive', notifications[0].payload)

    @freezegun.freeze_time("1980-11-25")
    def test_general_proposition_submission_ok_hors_delai(self):
        ProfessionalExperienceFactory(
            person=self.candidate_ok,
            start_date=datetime.date(1979, 1, 25),
            end_date=datetime.date(1980, 11, 25),
        )
        training = GeneralEducationTrainingFactory(
            academic_year__year=1981,
            education_group_type=self.admission_ok.training.education_group_type,
            acronym=self.admission_ok.training.acronym,
            partial_acronym=self.admission_ok.training.partial_acronym,
        )
        data_ok = {
            'pool': AcademicCalendarTypes.ADMISSION_POOL_UE5_BELGIAN.name,
            'annee': 1981,
            'elements_confirmation': {
                'hors_delai': IElementsConfirmation.HORS_DELAI % {'year': '1981-1982'},
                'reglement_general': IElementsConfirmation.REGLEMENT_GENERAL,
                'protection_donnees': IElementsConfirmation.PROTECTION_DONNEES,
                'professions_reglementees': IElementsConfirmation.PROFESSIONS_REGLEMENTEES,
                'justificatifs': IElementsConfirmation.JUSTIFICATIFS % {'by_service': _("by the Enrolment Office")},
                'declaration_sur_lhonneur': IElementsConfirmation.DECLARATION_SUR_LHONNEUR
                % {'to_service': _("to the UCLouvain Registration Service")},
                'convention_cadre_stages': IElementsConfirmation.CONVENTION_CADRE_STAGE,
                'communication_hopitaux': IElementsConfirmation.COMMUNICATION_HOPITAUX,
            },
        }
        self.client.force_authenticate(user=self.candidate_ok.user)
        self.assertNotEqual(self.admission_ok.training, training)
        response = self.client.post(self.ok_url, data_ok)
        self.admission_ok.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionGenerale.CONFIRMEE.name)
        self.assertEqual(self.admission_ok.training, training)

    def test_general_proposition_submission_bad_pool(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        data = {
            'pool': AcademicCalendarTypes.ADMISSION_POOL_HUE5_BELGIUM_RESIDENCY.name,
            'annee': 1980,
        }
        response = self.client.post(self.ok_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_general_proposition_verification_too_much_submitted_propositions(self):
        self.client.force_authenticate(user=self.candidate_ok.user)

        academic_year_1981 = AcademicYear.objects.get(year=1981)
        academic_year_1982 = AcademicYear.objects.get(year=1982)

        current_admission = GeneralEducationAdmissionFactory(
            candidate=self.candidate_ok,
            training__academic_year=academic_year_1981,
            determined_academic_year=None,
            # force type to have access conditions
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__acronym="FOOBAR",
        )

        current_admission_url = resolve_url("admission_api_v1:submit-general-proposition", uuid=current_admission.uuid)

        GeneralEducationAdmissionFactory(
            candidate=self.candidate_ok,
            status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            determined_academic_year=academic_year_1981,
        )
        GeneralEducationAdmissionFactory(
            candidate=self.candidate_ok,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            determined_academic_year=academic_year_1981,
        )

        # Two admissions already submitted for the same year (based on the training year)
        response = self.client.get(current_admission_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        errors_statuses = [e["status_code"] for e in response.json()['errors']]
        self.assertIn(NombrePropositionsSoumisesDepasseException.status_code, errors_statuses)

        # Two admissions already submitted for the same year (based on the determined academic year)
        current_admission.training.academic_year = academic_year_1982
        current_admission.training.save(update_fields=['academic_year'])
        current_admission.determined_academic_year = academic_year_1981
        current_admission.save(update_fields=['determined_academic_year'])

        response = self.client.get(current_admission_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        errors_statuses = [e["status_code"] for e in response.json()['errors']]
        self.assertIn(NombrePropositionsSoumisesDepasseException.status_code, errors_statuses)

        # Two admissions already submitted but for a different year (based on the training year)
        current_admission.determined_academic_year = None
        current_admission.save(update_fields=['determined_academic_year'])

        response = self.client.get(current_admission_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        errors_statuses = [e["status_code"] for e in response.json()['errors']]
        self.assertNotIn(NombrePropositionsSoumisesDepasseException.status_code, errors_statuses)

        # Two admissions already submitted but for a different year (based on the determined academic year)
        current_admission.determined_academic_year = academic_year_1982
        current_admission.save(update_fields=['determined_academic_year'])

        response = self.client.get(current_admission_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        errors_statuses = [e["status_code"] for e in response.json()['errors']]
        self.assertNotIn(NombrePropositionsSoumisesDepasseException.status_code, errors_statuses)

    def test_general_proposition_submission_too_much_submitted_propositions(self):
        self.client.force_authenticate(user=self.candidate_ok.user)

        data = self.data_ok.copy()
        data['annee'] = 1981

        academic_year_1981 = AcademicYear.objects.get(year=1981)
        academic_year_1982 = AcademicYear.objects.get(year=1982)

        current_admission = GeneralEducationAdmissionFactory(
            candidate=self.candidate_ok,
            training__academic_year=academic_year_1981,
            determined_academic_year=None,
            # force type to have access conditions
            training__education_group_type__name=TrainingType.BACHELOR.name,
            training__acronym="FOOBAR",
        )

        current_admission_url = resolve_url("admission_api_v1:submit-general-proposition", uuid=current_admission.uuid)

        GeneralEducationAdmissionFactory(
            candidate=self.candidate_ok,
            status=ChoixStatutPropositionGenerale.INSCRIPTION_AUTORISEE.name,
            determined_academic_year=academic_year_1981,
        )
        GeneralEducationAdmissionFactory(
            candidate=self.candidate_ok,
            status=ChoixStatutPropositionGenerale.CONFIRMEE.name,
            determined_academic_year=academic_year_1981,
        )

        # Two admissions already submitted for the same year (based on the training year)
        response = self.client.post(current_admission_url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_statuses = [e["status_code"] for e in response.json()['non_field_errors']]
        self.assertIn(NombrePropositionsSoumisesDepasseException.status_code, errors_statuses)

        # Two admissions already submitted for the same year (based on the determined academic year)
        current_admission.training.academic_year = academic_year_1982
        current_admission.training.save(update_fields=['academic_year'])
        current_admission.determined_academic_year = academic_year_1981
        current_admission.save(update_fields=['determined_academic_year'])

        response = self.client.post(current_admission_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_statuses = [e["status_code"] for e in response.json()['non_field_errors']]
        self.assertIn(NombrePropositionsSoumisesDepasseException.status_code, errors_statuses)

        data['annee'] = 1982

        # Two admissions already submitted but for a different year (based on the training year)
        current_admission.determined_academic_year = None
        current_admission.save(update_fields=['determined_academic_year'])

        response = self.client.post(current_admission_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_statuses = [e["status_code"] for e in response.json()['non_field_errors']]
        self.assertNotIn(NombrePropositionsSoumisesDepasseException.status_code, errors_statuses)

        # Two admissions already submitted but for a different year (based on the determined academic year)
        current_admission.determined_academic_year = academic_year_1982
        current_admission.save(update_fields=['determined_academic_year'])

        response = self.client.post(current_admission_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors_statuses = [e["status_code"] for e in response.json()['non_field_errors']]
        self.assertNotIn(NombrePropositionsSoumisesDepasseException.status_code, errors_statuses)


@freezegun.freeze_time('2022-12-10')
@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl/')
class ContinuingPropositionSubmissionTestCase(APITestCase):
    @classmethod
    @patch("osis_document.contrib.fields.FileField._confirm_multiple_upload")
    def setUpTestData(cls, confirm_upload):
        confirm_upload.side_effect = lambda _, value, __: ["550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92"] if value else []
        AdmissionAcademicCalendarFactory.produce_all_required()
        cls.belgium_country = CountryFactory(iso_code=BE_ISO_CODE)

        # Validation errors
        cls.candidate_errors = IncompletePersonForIUFCFactory()
        cls.admission = ContinuingEducationAdmissionFactory(
            candidate=cls.candidate_errors,
            # force type to have access conditions
            training__education_group_type__name=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
        )
        cls.error_url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=cls.admission.uuid)

        # Validation ok
        cls.admission_ok = ContinuingEducationAdmissionFactory(with_access_conditions_met=True)
        training = cls.admission_ok.training
        cls.candidate_ok = cls.admission_ok.candidate
        cls.candidate_ok_residential_address = PersonAddress.objects.filter(
            person=cls.candidate_ok, label=PersonAddressType.RESIDENTIAL.name
        ).first()
        cls.ok_url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=cls.admission_ok.uuid)

        cls.second_admission_ok = ContinuingEducationAdmissionFactory(
            with_access_conditions_met=True,
            training=training,
        )
        cls.third_admission_ok = ContinuingEducationAdmissionFactory(
            candidate=cls.second_admission_ok.candidate,
            with_access_conditions_met=True,
            training=training,
        )

        cls.first_fac_manager = ProgramManagerRoleFactory(education_group=training.education_group).person
        cls.second_fac_manager = ProgramManagerRoleFactory(education_group=training.education_group).person

        cls.second_candidate_ok = cls.second_admission_ok.candidate

        cls.second_ok_url = resolve_url(
            "admission_api_v1:submit-continuing-proposition",
            uuid=cls.second_admission_ok.uuid,
        )
        cls.third_ok_url = resolve_url(
            "admission_api_v1:submit-continuing-proposition",
            uuid=cls.third_admission_ok.uuid,
        )

        cls.submitted_data = {
            'pool': AcademicCalendarTypes.CONTINUING_EDUCATION_ENROLLMENT.name,
            'annee': 2022,
            'elements_confirmation': {
                'reglement_general': IElementsConfirmation.REGLEMENT_GENERAL,
                'protection_donnees': IElementsConfirmation.PROTECTION_DONNEES,
                'professions_reglementees': IElementsConfirmation.PROFESSIONS_REGLEMENTEES,
                'justificatifs': IElementsConfirmation.JUSTIFICATIFS % {'by_service': _("by the faculty")},
                'declaration_sur_lhonneur': IElementsConfirmation.DECLARATION_SUR_LHONNEUR
                % {'to_service': _("to the faculty")},
                'droits_inscription_iufc': IElementsConfirmation.DROITS_INSCRIPTION_IUFC,
            },
        }

    def setUp(self):
        # Mock osis-document
        patcher = mock.patch(
            'admission.infrastructure.admission.formation_continue.domain.service.notification.get_remote_token',
            return_value='foobar',
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
                'size': 1,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.confirm_remote_upload')
        patched = patcher.start()
        patched.return_value = '550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.contrib.fields.FileField._confirm_multiple_upload')
        patched = patcher.start()
        patched.side_effect = lambda _, value, __: ['550bf83e-2be9-4c1e-a2cd-1bdfe82e2c92'] if value else []
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_remote_tokens')
        patched = patcher.start()
        patched.side_effect = lambda uuids, **kwargs: {uuid: f'token-{index}' for index, uuid in enumerate(uuids)}
        self.addCleanup(patcher.stop)

        patcher = mock.patch('osis_document.api.utils.get_several_remote_metadata')
        patched = patcher.start()
        patched.side_effect = lambda tokens: {
            token: {
                'name': 'myfile',
                'mimetype': PDF_MIME_TYPE,
                'size': 1,
            }
            for token in tokens
        }
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.exports.admission_recap.attachments.get_raw_content_remotely')
        self.get_raw_content_mock = patcher.start()
        self.get_raw_content_mock.return_value = b'some content'
        self.addCleanup(patcher.stop)

        patcher = mock.patch('admission.exports.admission_recap.admission_recap.save_raw_content_remotely')
        self.save_raw_content_mock = patcher.start()
        self.save_raw_content_mock.return_value = 'pdf-token'
        self.addCleanup(patcher.stop)

        # Mock img2pdf
        patcher = mock.patch('admission.exports.admission_recap.attachments.img2pdf.convert')
        self.convert_img_mock = patcher.start()
        self.convert_img_mock.return_value = b'some content'
        self.addCleanup(patcher.stop)

        # Mock pikepdf
        patcher = mock.patch('admission.exports.admission_recap.admission_recap.Pdf')
        patched = patcher.start()
        patched.new.return_value = mock.MagicMock(pdf_version=1)
        self.outline_root = patched.new.return_value.open_outline.return_value.__enter__.return_value.root = MagicMock()
        patched.open.return_value.__enter__.return_value = mock.Mock(pdf_version=1, pages=[None])
        self.addCleanup(patcher.stop)

        # Mock weasyprint
        patcher = mock.patch('admission.exports.utils.get_pdf_from_template', return_value=b'some content')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_continuing_proposition_verification_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.get(self.error_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = response.json()
        self.assertTrue(len(json_content['errors']) > 0, "Should have errors")
        self.assertCountEqual(
            json_content['errors'],
            [
                {
                    "status_code": "FORMATION-CONTINUE-3",
                    "detail": _(
                        "Please specify the details of your most recent academic training and your most recent "
                        "non-academic experience."
                    ),
                },
            ],
        )

    def test_continuing_proposition_submission_with_errors(self):
        self.client.force_authenticate(user=self.candidate_errors.user)
        response = self.client.post(self.error_url, self.submitted_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_continuing_proposition_verification_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)
        response = self.client.get(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['errors'], [])

    def test_continuing_proposition_with_closed_training(self):
        self.client.force_authenticate(user=self.candidate_ok.user)

        admission = ContinuingEducationAdmissionFactory(
            candidate=self.candidate_ok,
            with_access_conditions_met=True,
        )
        admission.training.specificiufcinformations.state = StateIUFC.CLOSED.name
        admission.training.specificiufcinformations.save()

        admission_url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=admission.uuid)

        expected_error = {
            "status_code": "FORMATION-CONTINUE-6",
            "detail": _("Your application cannot be submitted because the %(acronym)s course is closed.")
            % {"acronym": admission.training.acronym},
        }

        # Verification
        response = self.client.get(admission_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = response.json()
        self.assertEqual(json_content.get('errors', []), [expected_error])

        # Submission
        response = self.client.post(admission_url, self.submitted_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        json_content = response.json()
        self.assertEqual(json_content.get('non_field_errors', []), [expected_error])

    def test_continuing_proposition_submission_ok(self):
        self.client.force_authenticate(user=self.candidate_ok.user)

        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionContinue.EN_BROUILLON.name)

        response = self.client.post(self.ok_url, self.submitted_data)

        # Check the response
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())

        # Check the admission
        self.admission_ok.refresh_from_db()
        self.assertEqual(self.admission_ok.status, ChoixStatutPropositionContinue.CONFIRMEE.name)
        self.assertIsNotNone(self.admission_ok.submitted_at)
        self.assertEqual(
            self.admission_ok.submitted_profile,
            {
                'identification': {
                    'first_name': self.admission_ok.candidate.first_name,
                    'last_name': self.admission_ok.candidate.last_name,
                    'gender': self.admission_ok.candidate.gender,
                    'country_of_citizenship': self.admission_ok.candidate.country_of_citizenship.iso_code,
                    'date_of_birth': self.admission_ok.candidate.birth_date.isoformat(),
                },
                'coordinates': {
                    'country': self.candidate_ok_residential_address.country.iso_code,
                    'postal_code': self.candidate_ok_residential_address.postal_code,
                    'city': self.candidate_ok_residential_address.city,
                    'street': self.candidate_ok_residential_address.street,
                    'street_number': self.candidate_ok_residential_address.street_number,
                    'postal_box': self.candidate_ok_residential_address.postal_box,
                },
            },
        )
        self.assertEqual(self.admission_ok.last_update_author, self.admission_ok.candidate)

        # Check tasks
        admission_tasks = AdmissionTask.objects.filter(admission=self.admission_ok)
        self.assertEqual(len(admission_tasks), 1)
        self.assertEqual(admission_tasks[0].type, AdmissionTask.TaskType.CONTINUING_MERGE.name)

        # Check the notification
        notifications = EmailNotification.objects.filter(person=self.candidate_ok)
        self.assertEqual(len(notifications), 1)

        email_object = message_from_string(notifications[0].payload)

        self.assertEqual(email_object['To'], self.admission_ok.candidate.private_email)

        cc_recipients = email_object['Cc'].split(',')
        self.assertEqual(len(cc_recipients), 2)
        self.assertCountEqual(cc_recipients, [self.first_fac_manager.email, self.second_fac_manager.email])

        content = email_object.as_string()
        self.assertIn(f'{self.admission_ok.candidate.first_name } {self.admission_ok.candidate.last_name}', content)
        self.assertIn('http://dummyurl/file/foobar', content)

        # Check the history entries
        history_entry: HistoryEntry = HistoryEntry.objects.filter(
            object_uuid=self.admission_ok.uuid,
            tags__contains=['proposition', 'status-changed'],
        ).last()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.message_fr, 'La proposition a été soumise.')

    def test_continuing_proposition_verification_ok_valuate_experiences(self):
        educational_experience = EducationalExperience.objects.filter(person=self.second_candidate_ok).first()
        professional_experience = ProfessionalExperience.objects.filter(person=self.second_candidate_ok).first()

        self.client.force_authenticate(user=self.second_candidate_ok.user)

        # First submission
        response = self.client.post(self.second_ok_url, data=self.submitted_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.second_admission_ok.refresh_from_db()

        # Valuation of the secondary studies
        self.assertEqual(self.second_admission_ok.valuated_secondary_studies_person, self.second_candidate_ok)

        # Valuation of the curriculum experiences
        self.assertEqual(len(self.second_admission_ok.educational_valuated_experiences.all()), 1)
        self.assertEqual(len(self.second_admission_ok.professional_valuated_experiences.all()), 1)
        self.assertEqual(
            self.second_admission_ok.educational_valuated_experiences.first().uuid,
            educational_experience.uuid,
        )
        self.assertEqual(
            self.second_admission_ok.professional_valuated_experiences.first().uuid,
            professional_experience.uuid,
        )

        # Check that the pdf recap has been generated with the right sections
        call_args = self.outline_root.append.call_args_list

        pdf_sections = [
            'identification',
            'coordinates',
            'training_choice',
            'education',
            'curriculum_academic_experience',
            'curriculum_non_academic_experience',
            'specific_question',
            'confirmation',
        ]

        self.assertEqual(len(call_args), len(pdf_sections))

        call_args_by_tab = {tab: call_args[index][0][0] for index, tab in enumerate(pdf_sections)}

        # Check that all pdf sections have been added
        self.assertEqual(call_args_by_tab['identification'].title, 'Identification')
        self.assertEqual(call_args_by_tab['coordinates'].title, 'Coordonnées')
        self.assertEqual(call_args_by_tab['training_choice'].title, 'Choix de formation')
        self.assertEqual(call_args_by_tab['education'].title, 'Études secondaires')
        self.assertEqual(
            call_args_by_tab['curriculum_academic_experience'].title,
            'Curriculum > Computer science 2021-2022',
        )
        self.assertEqual(
            call_args_by_tab['curriculum_non_academic_experience'].title,
            'Curriculum > Travail 01/2021-03/2021',
        )
        self.assertEqual(call_args_by_tab['specific_question'].title, 'Informations complémentaires')
        self.assertEqual(call_args_by_tab['confirmation'].title, 'Finalisation')

        # Second submission
        response = self.client.post(self.third_ok_url, data=self.submitted_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.third_admission_ok.refresh_from_db()

        # Valuation of the secondary studies
        self.assertEqual(self.third_admission_ok.valuated_secondary_studies_person, self.third_admission_ok.candidate)

        # Valuation of the curriculum experiences
        self.assertEqual(len(self.third_admission_ok.educational_valuated_experiences.all()), 1)
        self.assertEqual(len(self.third_admission_ok.professional_valuated_experiences.all()), 1)
        self.assertEqual(
            self.third_admission_ok.educational_valuated_experiences.first().uuid,
            educational_experience.uuid,
        )
        self.assertEqual(
            self.third_admission_ok.professional_valuated_experiences.first().uuid,
            professional_experience.uuid,
        )

    def test_continuing_proposition_verification_too_much_submitted_propositions(self):
        ContinuingEducationAdmissionFactory(
            candidate=self.candidate_ok,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )
        ContinuingEducationAdmissionFactory(
            candidate=self.candidate_ok,
            status=ChoixStatutPropositionContinue.CONFIRMEE.name,
        )
        self.client.force_authenticate(user=self.candidate_ok.user)
        response = self.client.get(self.ok_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ret = response.json()
        self.assertIn(NombrePropositionsSoumisesDepasseException.status_code, [e["status_code"] for e in ret['errors']])

    def test_continuing_proposition_submission_with_secondary_studies(self):
        admission = ContinuingEducationAdmissionFactory(candidate__graduated_from_high_school=GotDiploma.YES.name)
        url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=admission.uuid)
        self.client.force_authenticate(user=admission.candidate.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertIn(
            EtudesSecondairesNonCompleteesException.status_code,
            [e["status_code"] for e in json_response['errors']],
        )

        admission.candidate.graduated_from_high_school_year = self.candidate_ok.graduated_from_high_school_year
        admission.candidate.save()
        self.client.force_authenticate(user=admission.candidate.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        self.assertNotIn(
            EtudesSecondairesNonCompleteesException.status_code,
            [e["status_code"] for e in json_response['errors']],
        )

    def test_continuing_proposition_submission_with_specific_questions(self):
        admission = ContinuingEducationAdmissionFactory()
        admission_form_item = TextAdmissionFormItemFactory()
        AdmissionFormItemInstantiationFactory(
            form_item=admission_form_item,
            required=True,
            display_according_education=CritereItemFormulaireFormation.TOUTE_FORMATION.name,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            academic_year=admission.training.academic_year,
        )
        admission_form_item.refresh_from_db()

        self.client.force_authenticate(user=admission.candidate.user)

        url = resolve_url("admission_api_v1:submit-continuing-proposition", uuid=admission.uuid)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        status_codes = [e["status_code"] for e in json_response['errors']]
        self.assertIn(QuestionsSpecifiquesInformationsComplementairesNonCompleteesException.status_code, status_codes)

        admission.specific_question_answers = {str(admission_form_item.uuid): 'My answer'}
        admission.save()
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = response.json()
        status_codes = [e["status_code"] for e in json_response['errors']]
        self.assertNotIn(
            QuestionsSpecifiquesInformationsComplementairesNonCompleteesException.status_code, status_codes
        )
