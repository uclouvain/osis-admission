# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

import factory
from django.conf import settings
from osis_signature.models import Actor, Process

from admission.contrib.models import SupervisionActor
from admission.contrib.models.enums.actor_type import ActorType
from ..factories.roles import CaMemberRoleFactory, PromoterRoleFactory


class _ProcessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Process


class _ActorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Actor

    process = factory.SubFactory(_ProcessFactory)
    person = factory.SubFactory('base.tests.factories.person.PersonFactory')


class PromoterFactory(factory.django.DjangoModelFactory):
    def __init__(self, process=None, **kwargs):
        super().__init__(**kwargs)
        if process:
            self.actor_ptr.process = process

    class Meta:
        model = SupervisionActor

    actor_ptr = factory.SubFactory(_ActorFactory, person__user__first_name="Promoter")
    type = ActorType.PROMOTER.name
    person = factory.SelfAttribute('actor_ptr.person')
    process = factory.SelfAttribute('actor_ptr.process')

    @factory.post_generation
    def generate_role(self, create, extracted, **kwargs):
        PromoterRoleFactory(person=self.actor_ptr.person, **kwargs)


class ExternalPromoterFactory(PromoterFactory):
    actor_ptr = factory.SubFactory(_ActorFactory, person__user__first_name="External promoter")
    person = None
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    institute = factory.Faker('company')
    city = factory.Faker('city')
    country = factory.SubFactory('reference.tests.factories.country.CountryFactory')
    language = factory.Iterator(settings.LANGUAGES, getter=lambda l: l[0])

    @factory.post_generation
    def generate_role(self, create, extracted, **kwargs):
        if self.actor_ptr.person_id:
            PromoterRoleFactory(person=self.actor_ptr.person, **kwargs)


class CaMemberFactory(PromoterFactory):
    actor_ptr = factory.SubFactory(_ActorFactory, person__user__first_name="CA Member")
    type = ActorType.CA_MEMBER.name

    @factory.post_generation
    def generate_role(self, create, extracted, **kwargs):
        if self.actor_ptr.person_id:
            CaMemberRoleFactory(person=self.actor_ptr.person, **kwargs)
