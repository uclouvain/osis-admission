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


def migrate_old_predefined_refusal_reasons(apps, schema_editor):
    """The previous predefined reasons will be moved to the other reasons field."""
    DoctorateAdmission = apps.get_model('admission', 'DoctorateAdmission')

    doctorate_refusal_reasons = DoctorateAdmission.refusal_reasons.through.objects.select_related(
        'doctorateadmission',
        'refusalreason',
    )

    doctorates_to_update = {}
    for doctorate_refusal_reason in doctorate_refusal_reasons:
        current_doctorate = doctorate_refusal_reason.doctorateadmission

        if current_doctorate.pk in doctorates_to_update:
            current_doctorate = doctorates_to_update[current_doctorate.pk]
        else:
            doctorates_to_update[current_doctorate.pk] = current_doctorate

        current_doctorate.other_refusal_reasons.append(doctorate_refusal_reason.refusalreason.name)

    DoctorateAdmission.objects.bulk_update(list(doctorates_to_update.values()), fields=['other_refusal_reasons'])
    doctorate_refusal_reasons.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("admission", "0253_promoter_unique_constraint_data_structure"),
    ]

    operations = [
        migrations.RunPython(code=migrate_old_predefined_refusal_reasons, reverse_code=migrations.RunPython.noop),
    ]
