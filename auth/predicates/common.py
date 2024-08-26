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
from admission.contrib.models.epc_injection import EPCInjectionStatus
from base.models.person_creation_ticket import PersonTicketCreation, PersonTicketCreationStatus
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


def _build_queryset_cache_key_from_role_qs(role_qs, suffix):
    """
    Return a cache key based on the model class of the queryset. This is useful when we want to cache a queryset for a
    user who has several roles.
    :param role_qs: The role queryset
    :param suffix: The suffix of the cache key
    :return: The cache key
    """
    return f'{role_qs.model.__module__}_{role_qs.model.__name__}_{suffix}'.replace('.', '_')


def has_scope(*scopes):
    assert len(scopes) > 0, 'You must provide at least one scope name'

    name = 'has_scope:%s' % ','.join(s.name for s in scopes)

    @predicate(name, bind=True)
    def fn(self, user):
        cache_key = _build_queryset_cache_key_from_role_qs(self.context['role_qs'], 'admission_scopes')

        if not hasattr(user, cache_key):
            setattr(
                user,
                cache_key,
                set(
                    scope
                    for scope_list in self.context['role_qs'].values_list('scopes', flat=True)
                    for scope in scope_list
                ),
            )
        return set([s.name for s in scopes]) <= getattr(user, cache_key)

    return fn


@predicate(bind=True)
def is_part_of_education_group(self, user: User, obj: BaseAdmission):
    cache_key = _build_queryset_cache_key_from_role_qs(self.context['role_qs'], 'education_groups_affected')

    if not hasattr(user, cache_key):
        setattr(user, cache_key, self.context['role_qs'].get_education_groups_affected())

    return obj.training.education_group_id in getattr(user, cache_key)


@predicate(bind=True)
def is_entity_manager(self, user: User, obj: BaseAdmission):
    cache_key = _build_queryset_cache_key_from_role_qs(self.context['role_qs'], 'entities_ids')

    if not hasattr(user, cache_key):
        setattr(user, cache_key, self.context['role_qs'].get_entities_ids())

    return obj.training.management_entity_id in getattr(user, cache_key)


def has_education_group_of_types(*education_group_types):
    name = 'has_education_group_of_types:%s' % ','.join(education_group_types)

    @predicate(name, bind=True)
    def fn(self, user: User):
        cache_key = _build_queryset_cache_key_from_role_qs(self.context['role_qs'], 'education_group_types')

        if not hasattr(user, cache_key):
            setattr(
                user,
                cache_key,
                set(
                    self.context['role_qs'].values_list(
                        'education_group__educationgroupyear__education_group_type__name',
                        flat=True,
                    )
                ),
            )
        return set(education_group_types) & getattr(user, cache_key)

    return fn


@predicate(bind=True)
@predicate_failed_msg(message=_("Admission has been sent to EPC."))
def is_sent_to_epc(self, user: User, obj: BaseAdmission):
    return obj.sent_to_epc


@predicate(bind=True)
def pending_digit_ticket_response(self, user: User, obj: BaseAdmission):
    return obj.candidate.global_id[0] in ['8', '9'] and PersonTicketCreation.objects.filter(
        person_id=obj.candidate_id,
        status__in=[
           PersonTicketCreationStatus.CREATED.name,
           PersonTicketCreationStatus.IN_PROGRESS.name,
           PersonTicketCreationStatus.ERROR.name,
        ]
    ).exists()
