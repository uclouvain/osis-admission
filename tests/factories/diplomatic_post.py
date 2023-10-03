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
from django.db.models import Max
from factory import DjangoModelFactory

from admission.contrib.models import DiplomaticPost


class DiplomaticPostFactory(DjangoModelFactory):
    code = factory.LazyFunction(lambda: DiplomaticPostFactory._increment_counter())
    name_fr = factory.Faker('city')
    name_en = factory.Faker('city')
    email = factory.Faker('email')

    @classmethod
    def _increment_counter(cls):
        last_counter = (
            cls.COUNTER if hasattr(cls, 'COUNTER') else DiplomaticPost.objects.aggregate(Max('code'))['code__max'] or 0
        )
        cls.COUNTER = last_counter + 1
        return cls.COUNTER

    class Meta:
        model = DiplomaticPost
