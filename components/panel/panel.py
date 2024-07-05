# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.functional import Promise
from django_components import component
from voluptuous import Schema, Required, Any

from inscription_evaluation.components.utils import OsisComponent


@component.register("panel")
class PanelComponent(OsisComponent):
    template_name = "panel/panel.html"
    context_data_schema = Schema(
        {
            Required('title'): Any(str, Promise),
            Required('title_level', default=4): int,
            'edit_link_button': str,
            Required('edit_link_button_in_new_tab', default=False): bool,
            # FIXME Uncomment after upgrade to django_components >= 0.77
            # 'attributes': {str: str},
            # And remove `additional_class`, then move it to the `class` key of `attributes` when used
            'additional_class': str,
            # Also remove `id` and move it as a key of `attributes`
            'id': str,
        }
    )

    class Media:
        css = "panel/panel.css"
        js = "panel/panel.js"
