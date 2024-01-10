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

from django.utils.translation import pgettext_lazy

from base.models.utils.utils import ChoiceEnum


class TypeEquivalenceTitreAcces(ChoiceEnum):
    NON_CONCERNE = pgettext_lazy('equivalence_type', 'Not concerned')
    EQUIVALENCE_CESS = pgettext_lazy('equivalence_type', 'CESS equivalence')
    EQUIVALENCE_GRADE_ACADEMIQUE_FWB = pgettext_lazy('equivalence_type', 'FWB academic degree equivalence')
    EQUIVALENCE_DE_NIVEAU = pgettext_lazy('equivalence_type', 'Level equivalence')
    NON_RENSEIGNE = pgettext_lazy('equivalence_type', 'Not specified')


class StatutEquivalenceTitreAcces(ChoiceEnum):
    COMPLETE = pgettext_lazy('equivalence_status', 'Completed')
    RESTRICTIVE = pgettext_lazy('equivalence_status', 'Restricted')
    EN_ATTENTE = pgettext_lazy('equivalence_status', 'Waiting')
    NON_RENSEIGNE = pgettext_lazy('equivalence_status', 'Not specified')


class EtatEquivalenceTitreAcces(ChoiceEnum):
    DEFINITIVE = pgettext_lazy('equivalence_state', 'Definitive')
    PROVISOIRE = pgettext_lazy('equivalence_state', 'Provisional')
