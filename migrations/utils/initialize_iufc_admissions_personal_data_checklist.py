# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.db.models import F, Func, JSONField, Q, Value

from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutChecklist, OngletsChecklist


def initialize_iufc_admissions_personal_data_checklist(model_class):
    default_data = {
        'libelle': 'To be processed',
        'enfants': [],
        'extra': {},
        'statut': ChoixStatutChecklist.INITIAL_CANDIDAT.name,
    }

    return (
        model_class.objects.filter(
            continuingeducationadmission__isnull=False,
            checklist__has_key='current',
        )
        .filter(
            ~Q(checklist__current__has_key=OngletsChecklist.donnees_personnelles.name),
        )
        .update(
            checklist=Func(
                Func(
                    F('checklist'),
                    Value(['initial', OngletsChecklist.donnees_personnelles.name]),
                    Value(default_data, output_field=JSONField()),
                    function='jsonb_set',
                    output_field=JSONField(),
                ),
                Value(['current', OngletsChecklist.donnees_personnelles.name]),
                Value(default_data, output_field=JSONField()),
                function='jsonb_set',
                output_field=JSONField(),
            )
        )
    )
