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
from dal import autocomplete
from django.utils.translation import gettext_lazy as _


class Select2MultipleWithCheckboxes(autocomplete.Select2Multiple):
    autocomplete_function = 'select2-multi-checkboxes'

    def build_attrs(self, *args, **kwargs):
        """Set data-autocomplete-light-language."""
        attrs = super().build_attrs(*args, **kwargs)
        attrs.setdefault('data-placeholder', _("Select items"))
        attrs.setdefault('data-selection-template', _("{items} items selected of {total}"))
        attrs.setdefault('data-select-all-label', _("Select all"))
        attrs.setdefault('data-unselect-all-label', _("Unselect all"))
        return attrs

    class Media:
        extend = True
        js = [
            'vendor/select2/dist/js/select2.full.js',  # Keep this to make it a dependency
            'admission/select2-multi-checkboxes.js',
        ]
        css = {
            'all': ['admission/select2-multi-checkboxes.css'],
        }
