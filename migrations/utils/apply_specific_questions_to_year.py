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
from typing import Iterable, List

from admission.models import AdmissionFormItemInstantiation


def apply_specific_questions_to_year(
    form_item_instantiation_model,
    academic_year_model,
    form_item_internal_labels: List[str],
    from_year: int,
    to_year: int,
):
    """
    Apply specific questions to a target year (to_year) by creating instantiations having the same configuration as
    the original ones from a specific year (from_year).
    :param form_item_instantiation_model: The AdmissionFormItemInstantiation model class
    :param academic_year_model: The AcademicYear model class
    :param form_item_internal_labels: The list of internal labels of the specific questions
    :param from_year: The year of the original instantiations
    :param to_year: The year of the new instantiations
    :return:
    """
    if not form_item_internal_labels:
        return

    target_academic_year = academic_year_model.objects.filter(year=to_year).first()

    if not target_academic_year:
        return

    form_items_instantiations: Iterable[AdmissionFormItemInstantiation] = form_item_instantiation_model.objects.filter(
        form_item__internal_label__in=form_item_internal_labels,
        academic_year__year=from_year,
    )

    if not form_items_instantiations:
        return

    for form_item_instantiation in form_items_instantiations:
        form_item_instantiation.pk = None
        form_item_instantiation._state.adding = True
        form_item_instantiation.academic_year = target_academic_year

    form_item_instantiation_model.objects.bulk_create(form_items_instantiations)
