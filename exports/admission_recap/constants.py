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
from django.utils.translation import gettext_lazy as _

from base.models.enums.education_group_types import TrainingType

TRAINING_TYPES_WITH_EQUIVALENCE = {
    TrainingType.AGGREGATION.name,
    TrainingType.CAPAES.name,
    TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
}
FORMATTED_RELATIONSHIPS = {
    'PERE': _('your father'),
    'MERE': _('your mother'),
    'TUTEUR_LEGAL': _('your legal guardian'),
    'CONJOINT': _('your partner'),
    'COHABITANT_LEGAL': _('your legal cohabitant'),
}
