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


class ByContextAdmissionFormMixin:
    """
    Hide and disable the fields that are not in the current context.
    """

    def __init__(self, current_context, fields_by_context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields_by_context = fields_by_context
        self.current_context_fields = self.fields_by_context[current_context]

        self.disable_fields_other_contexts()

    def disable_fields_other_contexts(self):
        """Disable and hide fields specific to other contexts."""
        for field in self.fields:
            if field not in self.current_context_fields:
                self.fields[field].disabled = True
                self.fields[field].widget = self.fields[field].hidden_widget()

    def add_error(self, field, error):
        if field and self.fields[field].disabled:
            return
        super().add_error(field, error)
