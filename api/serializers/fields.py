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
from django.urls.exceptions import NoReverseMatch
from django.urls import reverse, resolve

from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from osis_role.contrib.views import APIPermissionRequiredMixin


class ActionLinksField(serializers.Field):
    """
    Returns a dictionary of actions and their related endpoint (url + method type) that depend on user permissions.
    """

    def __init__(self, actions, **kwargs):
        kwargs.setdefault('default', {})
        kwargs.setdefault('source', '*')
        self.actions = actions
        super().__init__(**kwargs)

    def to_representation(self, instance):
        links = {}

        # Get the mandatory parameters from the context
        try:
            request = self.context['request']
        except KeyError:
            raise ImproperlyConfigured(
                'The \'request\' property must be added to the serializer context to compute the action links.'
            )

        # Get a dictionary of the available actions with their related endpoint (URL & HTTP method)
        for action_name, action in self.actions.items():

            # Get the url params
            if isinstance(action.get('params'), list):
                try:
                    url_args = [ getattr(instance, param_name) for param_name in action['params'] ]
                except AttributeError as error:
                    raise ImproperlyConfigured(error)
            else:
                url_args = []

            # Build the view url
            try:
                url = reverse(action.get('path_name'), args=url_args)
            except NoReverseMatch:
                raise ImproperlyConfigured(
                    'Please check the following path exists: \'{}\''.format(action.get('path_name'))
                )

            # Find the view related to this url
            resolver_match = resolve(url)
            view_class = resolver_match.func.view_class

            if issubclass(view_class, APIPermissionRequiredMixin):
                view = view_class(args=resolver_match.args, kwargs=resolver_match.kwargs)

                # Check the permissions specified in the view via the 'permission_mapping' property
                try:
                    view.check_method_permissions(request.user, action.get('method'))
                    # Add the related endpoints if the user has the right permissions
                    links[action_name] = {
                        'method': action.get('method'),
                        'url': url,
                    }
                except (PermissionDenied, NotAuthenticated) as e:
                    # Add the error if the user hasn't got the right permissions
                    links[action_name] = {
                        'errors': e.args
                    }

            else:
                raise ImproperlyConfigured(
                    'All paths specified in the \'links\' property must be related to views that implement '
                    'the \'{}\' mixin'.format(APIPermissionRequiredMixin.__name__)
                )

        return links
