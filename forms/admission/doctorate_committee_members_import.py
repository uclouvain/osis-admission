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

from django import forms
from django.utils.translation import gettext_lazy


class DoctorateCommitteeMembersImportForm(forms.Form):
    file = forms.FileField(
        label=gettext_lazy('CSV file'),
        help_text=gettext_lazy(
            'The file must contain, line by line, the CDD acronym in the first column and the names (concatenation of '
            'the first name and the last name) or the global identifiers of the persons to be added for this CDD in '
            'the following columns.'
        ),
    )
    with_header = forms.BooleanField(
        label=gettext_lazy('File with header'),
        required=False,
    )
