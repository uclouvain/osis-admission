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
from django.db import migrations

from admission.migrations.utils.synchronise_determined_academic_year import (
    update_determined_academic_year_for_submitted_admissions,
)


def update_determined_academic_year(apps, schema_editor):
    BaseAdmission = apps.get_model('admission', 'BaseAdmission')
    update_determined_academic_year_for_submitted_admissions(base_admission_model=BaseAdmission)


class Migration(migrations.Migration):
    dependencies = [
        ('admission', '0261_generaleducationadmission_regular_registration_proof_for_registration_change'),
    ]

    operations = [
        migrations.RunPython(code=update_determined_academic_year, reverse_code=migrations.RunPython.noop),
    ]
