# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from factory.fuzzy import FuzzyText

from admission.models.checklist import (
    AdditionalApprovalCondition,
    DoctorateRefusalReason,
    DoctorateRefusalReasonCategory,
    FreeAdditionalApprovalCondition,
    RefusalReason,
    RefusalReasonCategory,
)


class RefusalReasonCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RefusalReasonCategory

    name = factory.fuzzy.FuzzyText(length=10)
    order = 0


class RefusalReasonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RefusalReason

    name = FuzzyText(length=10)
    category = factory.SubFactory(RefusalReasonCategoryFactory)
    order = 0


class DoctorateRefusalReasonCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DoctorateRefusalReasonCategory

    name = factory.fuzzy.FuzzyText(length=10)
    order = 0


class DoctorateRefusalReasonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DoctorateRefusalReason

    name = FuzzyText(length=10)
    category = factory.SubFactory(DoctorateRefusalReasonCategoryFactory)
    order = 0


class AdditionalApprovalConditionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdditionalApprovalCondition

    order = factory.Sequence(lambda n: n)
    name_fr = FuzzyText(length=10)
    name_en = FuzzyText(length=10)

    @classmethod
    def _setup_next_sequence(cls):
        """Set up an initial sequence value for Sequence attributes.

        Returns:
            int: the first available ID to use for instances of this factory.
        """
        return (AdditionalApprovalCondition.objects.aggregate(Max('order'))['order__max'] or 0) + 1


class FreeAdditionalApprovalConditionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FreeAdditionalApprovalCondition

    name_fr = FuzzyText(length=10)
    name_en = FuzzyText(length=10)
