# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from django.test.utils import override_settings
from django.urls.base import reverse
from django.urls.conf import path
from django.utils.translation import gettext as _
from rest_framework.serializers import Serializer
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView

from admission.api.serializers.fields import ActionLinksField
from admission.contrib.models import DoctorateAdmission
from admission.tests.factories import DoctorateAdmissionFactory
from admission.tests.factories.groups import CandidateGroupFactory
from osis_role.contrib.views import APIPermissionRequiredMixin


# Mock views
class TestAPIDetailViewWithPermissions(APIPermissionRequiredMixin, APIView):
    permission_mapping = {
        'GET': 'admission.view_doctorateadmission',
        'DELETE': 'admission.delete_doctorateadmission',
        'PUT': ('admission.change_doctorateadmission', ),
    }

    def get_permission_object(self):
        return get_object_or_404(DoctorateAdmission, uuid=self.kwargs['uuid'])


class TestAPIListAndCreateViewWithPermissions(APIPermissionRequiredMixin, APIView):
    permission_mapping = {
        'GET': 'admission.access_doctorateadmission',
        'POST': 'admission.add_doctorateadmission',
    }


class TestAPIViewWithoutPermission(APIView):
    pass


# Mock url
urlpatterns = [
    path(
        'api-view-with-permissions/<uuid:uuid>/',
        TestAPIDetailViewWithPermissions.as_view(),
        name='api_view_with_permissions_detail',
    ),
    path(
        'api-view-with-permissions/',
        TestAPIListAndCreateViewWithPermissions.as_view(),
        name='api_view_with_permissions',
    ),
    path(
        'api-view-without-permission/',
        TestAPIViewWithoutPermission.as_view(),
        name='api_view_without_permission',
    ),
]


@override_settings(ROOT_URLCONF=__name__)
class SerializerFieldsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Data
        cls.first_doctorate_admission = DoctorateAdmissionFactory()
        cls.second_doctorate_admission = DoctorateAdmissionFactory()
        cls.first_user = cls.first_doctorate_admission.candidate.user
        cls.second_user = cls.second_doctorate_admission.candidate.user
        cls.first_user.groups.add(CandidateGroupFactory())
        cls.second_user.groups.add(CandidateGroupFactory())

        # Request
        factory = APIRequestFactory()
        cls.request = factory.get('api-view-with-permissions/', format='json')
        cls.request.user = cls.first_user
        cls.request._force_auth_user = cls.first_user

    def test_serializer_with_no_context_request(self):
        # The request is missing -> we raise an exception
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={})

        serializer = SerializerWithActionLinks(
            instance=self.first_doctorate_admission
        )
        with self.assertRaisesMessage(ImproperlyConfigured, 'request'):
            serializer.data

    def test_serializer_without_action(self):
        # The list of actions is empty -> we return an empty dictionary
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={})

        serializer = SerializerWithActionLinks(
            instance=self.first_doctorate_admission,
            context={
                'request': self.request,
            },
        )
        self.assertTrue('links' in serializer.data)
        self.assertEqual(serializer.data['links'], {})

    def test_serializer_with_action_and_valid_permission(self):
        # The list of actions contains one available action -> we return the related endpoint
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'add_doctorateadmission': {
                    'method': 'POST',
                    'path_name': 'api_view_with_permissions',
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_doctorate_admission,
            context={
                'request': self.request,
            },
        )
        self.assertTrue('links' in serializer.data)
        self.assertEqual(serializer.data['links'], {
            'add_doctorateadmission': {
                'method': 'POST',
                'url': reverse('api_view_with_permissions')
            }
        })

    def test_serializer_with_action_and_valid_permission_and_param(self):
        # The list of actions contains one available action with a url parameter -> we return the related endpoint
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'get_doctorateadmission': {
                    'method': 'GET',
                    'path_name': 'api_view_with_permissions_detail',
                    'params': ['uuid']
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_doctorate_admission,
            context={
                'request': self.request,
            },
        )
        self.assertTrue('links' in serializer.data)
        self.assertEqual(serializer.data['links'], {
            'get_doctorateadmission': {
                'method': 'GET',
                'url': reverse('api_view_with_permissions_detail', args=[self.first_doctorate_admission.uuid]),
            }
        })

    def test_serializer_with_action_and_param_but_invalid_permission(self):
        # The list of actions contains one available action with a url parameter
        # But the user hasn't got access to this resource -> we return the related error
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'update_doctorateadmission': {
                    'method': 'PUT',
                    'path_name': 'api_view_with_permissions_detail',
                    'params': ['uuid']
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.second_doctorate_admission,
            context={
                'request': self.request,
            },
        )
        self.assertTrue('links' in serializer.data)
        self.assertEqual(serializer.data['links'], {
            'update_doctorateadmission': {
                'error': _("You must be the request author to access this admission"),
            }
        })

    def test_serializer_with_action_and_valid_permission_but_bad_params(self):
        # The list of actions contains one available action but with a bad url parameter -> we raise an exception
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'get_doctorateadmission': {
                    'method': 'GET',
                    'path_name': 'api_view_with_permissions_detail',
                    'params': ['incorrect_param']
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_doctorate_admission,
            context={
                'request': self.request,
            },
        )
        with self.assertRaisesMessage(ImproperlyConfigured, 'incorrect_param'):
            serializer.data

    def test_serializer_with_action_and_valid_permission_but_bad_path_name(self):
        # The list of actions contains one action with a bad path name -> we raise an exception
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'add_doctorateadmission': {
                    'method': 'POST',
                    'path_name': 'invalid_api_view_with_permissions',
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_doctorate_admission,
            context={
                'request': self.request,
            },
        )
        with self.assertRaisesMessage(ImproperlyConfigured, 'invalid_api_view_with_permissions'):
            serializer.data

    def test_serializer_with_action_and_valid_permission_but_bad_view(self):
        # The list of actions contains one action with a valid path name but related to a view which doesn't
        # implement the APIPermissionRequiredMixin mixin -> we raise an exception
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'add_doctorateadmission': {
                    'method': 'POST',
                    'path_name': 'api_view_without_permission',
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_doctorate_admission,
            context={
                'request': self.request,
            },
        )
        with self.assertRaisesMessage(ImproperlyConfigured, 'APIPermissionRequiredMixin'):
            serializer.data

    def test_serializer_with_action_and_valid_permission_and_param_many_instances(self):
        # The list of actions contains one available action with a url parameter. We pass two instances and the user
        # only has access to one of these instances -> we return two different results depending on the permissions.

        doctorate_admissions = DoctorateAdmission.objects.all().order_by('created')

        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'get_doctorateadmission': {
                    'method': 'GET',
                    'path_name': 'api_view_with_permissions_detail',
                    'params': ['uuid'],
                }
            })

        serializer = SerializerWithActionLinks(
            many=True,
            instance=doctorate_admissions,
            context={
                'request': self.request,
            },
        )
        self.assertEqual(len(serializer.data), 2)
        # First doctorate admission: the user has got the right permissions -> we return the related endpoint
        self.assertTrue('links' in serializer.data[0])
        self.assertEqual(serializer.data[0]['links'], {
            'get_doctorateadmission': {
                'method': 'GET',
                'url': reverse('api_view_with_permissions_detail', args=[self.first_doctorate_admission.uuid])
            }
        })
        # Second doctorate admission: the user hasn't got the right permissions -> we return the error
        self.assertTrue('links' in serializer.data[1])
        self.assertEqual(serializer.data[1]['links'], {
            'get_doctorateadmission': {
                'error': _("You must be the request author to access this admission"),
            }
        })
