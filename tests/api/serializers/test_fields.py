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
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.test.utils import override_settings
from django.urls.base import reverse
from django.urls.conf import path
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView
from rules.predicates import predicate
from rules import RuleSet, always_allow, always_deny, predicate

from admission.api.serializers.fields import ActionLinksField
from base.tests.factories.user import UserFactory
from base.tests.factories.group import GroupFactory
from osis_role.contrib.models import EntityRoleModel
from osis_role.contrib.views import APIPermissionRequiredMixin
from osis_role import role
from osis_role.errors import predicate_failed_msg


# Mock views
class TestAPIDetailViewWithPermissions(APIPermissionRequiredMixin, APIView):
    permission_mapping = {
        'GET': 'test.view_customer',
        'DELETE': 'test.delete_customer',
        'PUT': ('test.change_customer', ),
    }

    def get_permission_object(self):
        return get_object_or_404(User, id=self.kwargs['id'])

    def delete(self, request, *args, **kwargs):
        return Response()

    def get(self, request, *args, **kwargs):
        return Response()
    
    def post(self, request, *args, **kwargs):
        return Response()
    
    def put(self, request, *args, **kwargs):
        return Response()


class TestAPIListAndCreateViewWithPermissions(APIPermissionRequiredMixin, APIView):
    permission_mapping = {
        'GET': 'test.view_customer',
        'POST': 'test.access_customer',
    }

    def delete(self, request, *args, **kwargs):
        return Response()

    def get(self, request, *args, **kwargs):
        return Response()
    
    def post(self, request, *args, **kwargs):
        return Response()
    
    def put(self, request, *args, **kwargs):
        return Response()


class TestAPIViewWithoutPermission(APIView):
    def delete(self, request, *args, **kwargs):
        return Response()

    def get(self, request, *args, **kwargs):
        return Response()
    
    def post(self, request, *args, **kwargs):
        return Response()
    
    def put(self, request, *args, **kwargs):
        return Response()


# Mock url
urlpatterns = [
    path(
        'api-view-with-permissions/<int:id>/',
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
class SerializersTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Create role predicate
        @predicate(bind=True)
        @predicate_failed_msg(message="You don't have access to other user information.")
        def is_current_user(self, user: User, obj: User):
            return user.id == obj.id

        # Create a role with a set of rules
        class CustomerRole(EntityRoleModel):
            class Meta:
                verbose_name = "TestCustomer"
                verbose_name_plural = "TestCustomers"
                group_name = "testcustomers"


            @classmethod
            def rule_set(cls):
                return RuleSet({
                    'test.access_customer': always_allow,
                    'test.add_customer': always_allow,
                    'test.change_customer': is_current_user,
                    'test.delete_customer': always_deny,
                    'test.view_customer': is_current_user,
                })

        class CustomerGroupFactory(GroupFactory):
            name = 'testcustomers'

        # Register the role
        role.role_manager.register(CustomerRole)
        cls.customer_role = CustomerRole

        # Data
        cls.first_user = UserFactory()
        cls.second_user = UserFactory()
        cls.first_user.groups.add(CustomerGroupFactory())
        cls.second_user.groups.add(CustomerGroupFactory())

        # Request
        factory = APIRequestFactory()
        cls.request = factory.get('api-view-with-permissions/', format='json')
        cls.request.user = cls.first_user

    @classmethod
    def tearDownClass(cls):
        # Remove the used role
        role.role_manager.roles.remove(cls.customer_role)

    def test_serializer_with_no_context_request(self):
        # The request is missing -> we raise an exception
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={})

        serializer = SerializerWithActionLinks(
            instance=self.first_user
        )
        with self.assertRaisesMessage(ImproperlyConfigured, 'request'):
            serializer.data

    def test_serializer_without_action(self):
        # The list of actions is empty -> we return an empty dictionary
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={})

        serializer = SerializerWithActionLinks(
            instance=self.first_user,
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
                'add_customer': {
                    'method': 'POST',
                    'path_name': 'api_view_with_permissions',
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_user,
            context={
                'request': self.request,
            },
        )
        self.assertTrue('links' in serializer.data)
        self.assertEqual(serializer.data['links'], {
            'add_customer': {
                'method': 'POST',
                'url': reverse('api_view_with_permissions')
            }
        })

    def test_serializer_with_action_and_valid_permission_and_param(self):
        # The list of actions contains one available action with a url parameter -> we return the related endpoint
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'get_customer': {
                    'method': 'GET',
                    'path_name': 'api_view_with_permissions_detail',
                    'params': ['id']
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_user,
            context={
                'request': self.request,
            },
        )
        self.assertTrue('links' in serializer.data)
        self.assertEqual(serializer.data['links'], {
            'get_customer': {
                'method': 'GET',
                'url': reverse('api_view_with_permissions_detail', args=[self.first_user.id]),
            }
        })

    def test_serializer_with_action_and_param_but_invalid_permission(self):
        # The list of actions contains one available action with a url parameter
        # But the user hasn't got access to this resource -> we return the related error
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'update_customer': {
                    'method': 'PUT',
                    'path_name': 'api_view_with_permissions_detail',
                    'params': ['id']
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.second_user,
            context={
                'request': self.request,
            },
        )
        self.assertTrue('links' in serializer.data)
        self.assertEqual(serializer.data['links'], {
            'update_customer': {
                'error': ('You don\'t have access to other user information.', ),
            }
        })

    def test_serializer_with_action_and_valid_permission_but_bad_params(self):
        # The list of actions contains one available action but with a bad url parameter -> we raise an exception
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'get_customer': {
                    'method': 'GET',
                    'path_name': 'api_view_with_permissions_detail',
                    'params': ['incorrect_param']
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_user,
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
                'add_customer': {
                    'method': 'POST',
                    'path_name': 'invalid_api_view_with_permissions',
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_user,
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
                'add_customer': {
                    'method': 'POST',
                    'path_name': 'api_view_without_permission',
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_user,
            context={
                'request': self.request,
            },
        )
        with self.assertRaisesMessage(ImproperlyConfigured, 'APIPermissionRequiredMixin'):
            serializer.data

    def test_serializer_with_action_and_valid_permission_and_param_many_instances(self):
        # The list of actions contains one available action with a url parameter. We pass two instances and the user
        # only has access to one of these instances -> we return two different results depending of the permissions.

        users = User.objects.filter(groups__name='testcustomers').order_by('id')
        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'get_customer': {
                    'method': 'GET',
                    'path_name': 'api_view_with_permissions_detail',
                    'params': ['id'],
                }
            })

        serializer = SerializerWithActionLinks(
            many=True,
            instance=users,
            context={
                'request': self.request,
            },
        )
        self.assertEqual(len(serializer.data), 2)
        # First doctorate admission: the user has got the right permissions -> we return the related endpoint
        self.assertTrue('links' in serializer.data[0])
        self.assertEqual(serializer.data[0]['links'], {
            'get_customer': {
                'method': 'GET',
                'url': reverse('api_view_with_permissions_detail', args=[self.first_user.id])
            }
        })
        # Second doctorate admission: the user hasn't got the right permissions -> we return the error
        self.assertTrue('links' in serializer.data[1])
        self.assertTrue('error' in serializer.data[1]['links']['get_customer'])

    def test_serializer_with_action_and_valid_permission_and_param_many_actions(self):
        # The list of actions contains two actions with an url parameter. The user only has the right permissions
        # for one of these actions -> we return two different results depending of the permissions.

        class SerializerWithActionLinks(Serializer):
            links = ActionLinksField(actions={
                'get_customer': {
                    'method': 'GET',
                    'path_name': 'api_view_with_permissions_detail',
                    'params': ['id'],
                },
                'delete_customer': {
                    'method': 'DELETE',
                    'path_name': 'api_view_with_permissions_detail',
                    'params': ['id'],
                }
            })

        serializer = SerializerWithActionLinks(
            instance=self.first_user,
            context={
                'request': self.request,
            },
        )
        # First action: the user has got the right permissions -> we return the related endpoint
        self.assertTrue('links' in serializer.data)
        self.assertDictContainsSubset({
            'get_customer': {
                'method': 'GET',
                'url': reverse('api_view_with_permissions_detail', args=[self.first_user.id])
            }
        }, serializer.data['links'])
        # Second action: the user hasn't got the right permissions -> we return the error
        self.assertTrue('error' in serializer.data['links']['delete_customer'])
