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
from django.db.models import F


def update_determined_academic_year_for_submitted_admissions(base_admission_model):
    qs = (
        base_admission_model.objects.filter(
            submitted_at__isnull=False,
        )
        .exclude(
            determined_academic_year_id=F('training__academic_year_id'),
        )
        .select_related('training')
    )

    for admission in qs:
        admission.determined_academic_year_id = admission.training.academic_year_id

    base_admission_model.objects.bulk_update(qs, ['determined_academic_year_id'])
