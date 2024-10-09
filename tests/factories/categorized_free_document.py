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
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from admission.contrib.models.categorized_free_document import CategorizedFreeDocument
from admission.ddd.admission.formation_generale.domain.model.enums import OngletsChecklist


class CategorizedFreeDocumentFactory(DjangoModelFactory):
    checklist_tab = factory.Iterator(OngletsChecklist.get_names())
    short_label_fr = FuzzyText(length=10)
    short_label_en = FuzzyText(length=10)
    long_label_fr = FuzzyText(length=20)
    long_label_en = FuzzyText(length=20)

    class Meta:
        model = CategorizedFreeDocument
