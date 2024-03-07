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
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from rules import predicate
from waffle import switch_is_active

from admission.contrib.models import DoctorateAdmission
from admission.contrib.models.base import BaseAdmission
from osis_role.cache import predicate_cache
from osis_role.errors import predicate_failed_msg


@predicate(bind=True)
@predicate_failed_msg(message=_("You must be the request author to access this admission"))
def is_admission_request_author(self, user: User, obj: BaseAdmission):
    return obj.candidate == user.person


@predicate(bind=True)
@predicate_failed_msg(message=_("Another admission has been submitted."))
def does_not_have_a_submitted_admission(self, user: User, obj: DoctorateAdmission):
    return not BaseAdmission.objects.candidate_has_submission(user.person)


@predicate
def is_debug(*args):
    return switch_is_active("debug")


def has_scope(*scopes):
    assert len(scopes) > 0, 'You must provide at least one scope name'

    name = 'has_scope:%s' % ','.join(s.name for s in scopes)

    @predicate(name, bind=True)
    def fn(self, user):
        if not hasattr(user, '_admission_scopes'):
            user._admission_scopes = set(
                scope for scope_list in self.context['role_qs'].values_list('scopes', flat=True) for scope in scope_list
            )
        return set([s.name for s in scopes]) <= user._admission_scopes

    return fn


@predicate(bind=True)
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_part_of_education_group(self, user: User, obj: BaseAdmission):
    return obj.training.education_group_id in self.context['role_qs'].get_education_groups_affected()


@predicate(bind=True)
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_entity_manager(self, user: User, obj: BaseAdmission):
    return obj.training.management_entity_id in self.context['role_qs'].get_entities_ids()


def has_education_group_of_types(*education_group_types):
    name = 'has_education_group_of_types:%s' % ','.join(education_group_types)

    @predicate(name, bind=True)
    def fn(self, user: User):
        if not hasattr(user, '_education_group_types'):
            user._education_group_types = set(
                self.context['role_qs'].values_list(
                    'education_group__educationgroupyear__education_group_type__name', flat=True
                )
            )
        return set(education_group_types) & user._education_group_types

    return fn
