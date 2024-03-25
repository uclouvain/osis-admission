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
import copy
from typing import Optional

from django.utils.translation import gettext_noop as _

from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutChecklist,
)
from admission.ddd.admission.formation_continue.domain.model.proposition import Proposition
from admission.ddd.admission.formation_continue.domain.model.statut_checklist import (
    StatutChecklist,
    StatutsChecklistContinue,
)
from osis_common.ddd import interface


class Checklist(interface.DomainService):
    @classmethod
    def initialiser(
        cls,
        proposition: Proposition,
    ):
        checklist_initiale = cls.recuperer_checklist_initiale()
        proposition.checklist_initiale = checklist_initiale
        proposition.checklist_actuelle = copy.deepcopy(checklist_initiale)

    @classmethod
    def recuperer_checklist_initiale(
        cls,
    ) -> Optional[StatutsChecklistContinue]:
        return StatutsChecklistContinue(
            fiche_etudiant=StatutChecklist(
                libelle=_("To be processed"),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
            decision=StatutChecklist(
                libelle=_('To be processed'),
                statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
            ),
        )
