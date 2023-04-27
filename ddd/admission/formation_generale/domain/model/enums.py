# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.models.enums.got_diploma import GotDiploma
from base.models.utils.utils import ChoiceEnum


class ChoixStatutPropositionGenerale(ChoiceEnum):
    EN_BROUILLON = _('In draft')
    CONFIRMEE = _('Confirmed application (by student)')
    COMPLETEE = _('Completed application')
    ANNULEE = _('Cancelled application')
    A_COMPLETER_POUR_SIC = _('To be completed (by student) for SIC')
    A_COMPLETER_POUR_FAC_CDD = _('To be completed (by student) for FAC/CDD')
    TRAITEMENT_SIC = _('Processing by SIC')
    TRAITEMENT_FAC_CDD = _('Processing by Fac/CDD')
    ATTENTE_VALIDATION_DIRECTION = _('Pending validation from management')
    INSCRIPTION_AUTORISEE = _('Enrollment allowed')
    INSCRIPTION_REFUSEE = _('Enrollment denied')
    CLOTUREE = _('Closed')
    EN_RECOURS = _('Under appeal')


CHOIX_DIPLOME_OBTENU = {GotDiploma.YES.name, GotDiploma.THIS_YEAR.name}

STATUTS_PROPOSITION_GENERALE_NON_SOUMISE = {
    ChoixStatutPropositionGenerale.EN_BROUILLON.name,
    ChoixStatutPropositionGenerale.ANNULEE.name,
}
