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
from factory.fuzzy import FuzzyText

from admission.contrib.models import Scholarship
from admission.ddd.admission.enums.type_bourse import TypeBourse


class ScholarshipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Scholarship


class DoubleDegreeScholarshipFactory(factory.django.DjangoModelFactory):
    type = TypeBourse.DOUBLE_TRIPLE_DIPLOMATION.name
    short_name = FuzzyText(length=20)
    long_name = FuzzyText(length=40)

    class Meta:
        model = Scholarship


class InternationalScholarshipFactory(factory.django.DjangoModelFactory):
    type = TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name
    short_name = FuzzyText(length=20)
    long_name = FuzzyText(length=40)

    class Meta:
        model = Scholarship


class DoctorateScholarshipFactory(factory.django.DjangoModelFactory):
    type = TypeBourse.BOURSE_INTERNATIONALE_DOCTORAT.name
    short_name = FuzzyText(length=20)
    long_name = FuzzyText(length=40)

    class Meta:
        model = Scholarship


class ErasmusMundusScholarshipFactory(factory.django.DjangoModelFactory):
    type = TypeBourse.ERASMUS_MUNDUS.name
    short_name = FuzzyText(length=20)
    long_name = FuzzyText(length=40)

    class Meta:
        model = Scholarship
