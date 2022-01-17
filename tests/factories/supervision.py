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

import factory

from admission.contrib.models import SupervisionActor
from admission.contrib.models.enums.actor_type import ActorType
from osis_signature.models import Actor, Process
from ..factories.roles import PromoterRoleFactory, CaMemberRoleFactory


class _ProcessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Process


class _ActorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Actor

    process = factory.SubFactory(_ProcessFactory)
    person = factory.SubFactory('base.tests.factories.person.PersonFactory')


class PromoterFactory(factory.DjangoModelFactory):
    def __init__(self, process=None):
        super().__init__()
        if process:
            self.actor_ptr.process = process

    class Meta:
        model = SupervisionActor

    actor_ptr = factory.SubFactory(_ActorFactory)
    type = ActorType.PROMOTER.name
    person = factory.SelfAttribute('actor_ptr.person')
    process = factory.SelfAttribute('actor_ptr.process')

    @factory.post_generation
    def generate_role(self, create, extracted, **kwargs):
        PromoterRoleFactory(person=self.actor_ptr.person, **kwargs)


class ExternalPromoterFactory(PromoterFactory):
    @factory.post_generation
    def generate_role(self, create, extracted, **kwargs):
        PromoterRoleFactory(person=self.actor_ptr.person, is_external=True, **kwargs)


class CaMemberFactory(PromoterFactory):
    type = ActorType.CA_MEMBER.name

    @factory.post_generation
    def generate_role(self, create, extracted, **kwargs):
        CaMemberRoleFactory(person=self.actor_ptr.person, **kwargs)
