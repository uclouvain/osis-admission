# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from factory import SubFactory

from admission.contrib.models.cdd_config import CddConfiguration
from admission.contrib.models.doctoral_training import Activity
from admission.ddd.projet_doctoral.doctorat.formation.domain.model._enums import CategorieActivite
from admission.forms.doctorate.training.activity import ConferenceForm
from admission.tests.factories import DoctorateAdmissionFactory


class ActivityFactory(factory.DjangoModelFactory):
    doctorate = factory.SubFactory(DoctorateAdmissionFactory, admitted=True)
    ects = factory.Faker('random_int', min=1, max=35)
    category = factory.Iterator(CategorieActivite.choices(), getter=lambda c: c[0])

    class Meta:
        model = Activity


class ConferenceFactory(ActivityFactory):
    category = CategorieActivite.CONFERENCE.name
    type = factory.Iterator(CddConfiguration.conference_types.field.default()[settings.LANGUAGE_CODE_FR])
    title = factory.Faker('catch_phrase')
    start_date = factory.Faker('date_between', start_date='-30d')
    end_date = factory.Faker('date_this_month')
    participating_days = factory.Faker('random_int', min=0, max=5)
    is_online = factory.Faker('boolean')
    website = factory.Faker('url')
    country = factory.SubFactory('reference.tests.factories.country.CountryFactory')
    city = factory.Faker('city')
    organizing_institution = factory.Faker('company')
    comment = factory.Faker('text', max_nb_chars=150)


class ServiceFactory(ActivityFactory):
    category = CategorieActivite.SERVICE.name
    type = factory.Iterator(CddConfiguration.service_types.field.default()[settings.LANGUAGE_CODE_FR])
    title = factory.Faker('catch_phrase')
    start_date = factory.Faker('date_between', start_date='-30d')
    end_date = factory.Faker('date_this_month')
    hour_volume = factory.Faker('random_int', min=0, max=5)
    organizing_institution = factory.Faker('company')
    comment = factory.Faker('text', max_nb_chars=150)


class SeminarFactory(ActivityFactory):
    category = CategorieActivite.SEMINAR.name
    type = factory.Iterator(CddConfiguration.seminar_types.field.default()[settings.LANGUAGE_CODE_FR])
    title = factory.Faker('catch_phrase')
    start_date = factory.Faker('date_between', start_date='-30d')
    end_date = factory.Faker('date_this_month')
    hour_volume = factory.Faker('random_int', min=0, max=5)
    participating_proof = ['uuid']


class ResidencyFactory(ActivityFactory):
    category = CategorieActivite.RESIDENCY.name


class ConferenceCommunicationFactory(ActivityFactory):
    category = CategorieActivite.COMMUNICATION.name
    parent = SubFactory(ConferenceFactory, doctorate=factory.SelfAttribute('..doctorate'))


class ConferencePublicationFactory(ActivityFactory):
    category = CategorieActivite.PUBLICATION.name
    parent = SubFactory(ConferenceFactory, doctorate=factory.SelfAttribute('..doctorate'))


class SeminarCommunicationFactory(ActivityFactory):
    category = CategorieActivite.COMMUNICATION.name
    parent = SubFactory(SeminarFactory, doctorate=factory.SelfAttribute('..doctorate'))
    title = factory.Faker('catch_phrase')
    start_date = factory.Faker('date_between', start_date='-30d')
    country = factory.SubFactory('reference.tests.factories.country.CountryFactory')
    city = factory.Faker('city')
    organizing_institution = factory.Faker('company')
    authors = factory.Faker('name')


class ResidencyCommunicationFactory(ActivityFactory):
    category = CategorieActivite.COMMUNICATION.name
    parent = SubFactory(ResidencyFactory, doctorate=factory.SelfAttribute('..doctorate'))


class CommunicationFactory(ActivityFactory):
    category = CategorieActivite.COMMUNICATION.name


class PublicationFactory(ActivityFactory):
    category = CategorieActivite.PUBLICATION.name


class VaeFactory(ActivityFactory):
    category = CategorieActivite.VAE.name


class CourseFactory(ActivityFactory):
    category = CategorieActivite.COURSE.name


class PaperFactory(ActivityFactory):
    category = CategorieActivite.PAPER.name
