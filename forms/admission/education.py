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

from base.forms.utils import FIELD_REQUIRED_MESSAGE
from osis_profile.forms.etudes_secondaires import BachelorEducationForeignDiplomaForm
from osis_profile.models.enums.education import (
    ForeignDiplomaTypes,
)


class AdmissionBachelorEducationForeignDiplomaForm(BachelorEducationForeignDiplomaForm):
    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('foreign_diploma_type') == ForeignDiplomaTypes.NATIONAL_BACHELOR.name:
            # Equivalence
            if (
                getattr(self.fields['country'], 'is_ue_country', False) or self.is_med_dent_training
            ) and not cleaned_data.get('equivalence'):
                self.add_error('equivalence', FIELD_REQUIRED_MESSAGE)

        return cleaned_data
