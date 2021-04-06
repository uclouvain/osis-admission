from django.test import tag
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from admission.contrib.models import AdmissionDoctorate, AdmissionType
from admission.contrib.views import AdmissionDoctorateDeleteView
from admission.tests import TestCase
from admission.tests.factories import AdmissionDoctorateFactory
from base.tests.factories.person import PersonFactory


class AdmissionDoctorateCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.candidate = PersonFactory()
        cls.url = reverse("admissions:doctorate-create")
        cls.data = {
            "comment": "this is a test",
            "type": AdmissionType.ADMISSION.name,
            "candidate": cls.candidate.id,
        }

    def test_create_doctorate_admission_add_user_as_author(self):
        self.client.force_login(self.person.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertEqual(response.status_code, 200)
        # check that the object in the response got the person as author
        self.assertEqual(response.context_data["object"].author, self.person)
        # and double check by getting it from the db
        admission_author = AdmissionDoctorate.objects.get(
            candidate=self.candidate.id
        ).author
        self.assertEqual(admission_author, self.person)

    def test_create_doctorate_admission_redirect_to_detail_view(self):
        self.client.force_login(self.person.user)
        response = self.client.post(self.url, data=self.data, follow=True)
        self.assertEqual(response.status_code, 200)
        # make sure that the AdmissionDoctorate creation redirect to the detail view
        self.assertTemplateUsed(
            response,
            "admission/doctorate/admission_doctorate_detail.html",
        )

    def test_view_context_data_contains_cancel_url(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["cancel_url"])


class AdmissionDoctorateListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        AdmissionDoctorateFactory(
            candidate=cls.person,
            author=cls.person,
            type=AdmissionType.ADMISSION.name,
            comment="First admission",
        )
        AdmissionDoctorateFactory(
            candidate=cls.person,
            author=cls.person,
            type=AdmissionType.ADMISSION.name,
            comment="Second admission",
        )
        AdmissionDoctorateFactory(
            candidate=cls.person,
            author=cls.person,
            type=AdmissionType.PRE_ADMISSION.name,
            comment="A pre-admission",
        )
        cls.url = reverse("admissions:doctorate-list")

    def test_view_context_data_contains_items_per_page(self):
        self.client.force_login(self.person.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["items_per_page"])

    def test_message_is_triggered_if_no_results(self):
        self.client.force_login(self.person.user)
        response = self.client.get(
            self.url, data={"type": "this type doesn't exist"}
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), _("No result!"))

    def test_filtering_by_admission_type(self):
        self.client.force_login(self.person.user)
        response = self.client.get(
            self.url, data={"type": AdmissionType.ADMISSION.name}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data["object_list"]), 2)

    def test_filtering_by_pre_admission_type(self):
        self.client.force_login(self.person.user)
        response = self.client.get(
            self.url, data={"type": AdmissionType.PRE_ADMISSION.name}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data["object_list"]), 1)

    def test_filtering_by_candidate(self):
        self.client.force_login(self.person.user)
        response = self.client.get(
            self.url, data={"candidate": self.person.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data["object_list"]), 3)

    @tag('perf')
    def test_get_num_queries_serializer(self):
        self.client.force_login(self.person.user)
        with self.assertNumQueriesLessThan(13):
            self.client.get(self.url, HTTP_ACCEPT='application/json')


class AdmissionDoctorateDeleteViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.admission = AdmissionDoctorateFactory(
            candidate=cls.candidate, author=cls.candidate
        )
        cls.url = reverse("admissions:doctorate-delete", args=[cls.admission.pk])

    def test_delete_view_sends_message_when_object_is_deleted(self):
        self.client.force_login(self.candidate.user)
        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), _(AdmissionDoctorateDeleteView.success_message)
        )

    def test_delete_view_removes_admission_from_db(self):
        self.client.force_login(self.candidate.user)
        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AdmissionDoctorate.objects.count(), 0)


class AdmissionDoctorateUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.candidate = PersonFactory()
        cls.new_candidate = PersonFactory()
        cls.admission = AdmissionDoctorateFactory(
            candidate=cls.candidate,
            author=cls.candidate,
            comment="A comment",
            type=AdmissionType.ADMISSION,
        )
        cls.update_data = {
            "type": AdmissionType.PRE_ADMISSION.name,
            "comment": "New comment",
            "candidate": cls.new_candidate.pk,
        }
        cls.url = reverse("admissions:doctorate-update", args=[cls.admission.pk])

    def test_doctorate_admission_is_updated(self):
        self.client.force_login(self.candidate.user)
        response = self.client.post(self.url, data=self.update_data)
        self.assertEqual(response.status_code, 302)
        admission = AdmissionDoctorate.objects.get(pk=self.admission.pk)
        admission.refresh_from_db()
        self.assertEqual(admission.comment, self.update_data["comment"])
        self.assertEqual(admission.type, self.update_data["type"])
