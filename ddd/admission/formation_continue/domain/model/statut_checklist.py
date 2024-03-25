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
from enum import Enum
from typing import List, Optional, Dict

import attr

from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutChecklist
from osis_common.ddd import interface


@attr.dataclass
class StatutChecklist(interface.ValueObject):
    libelle: str
    enfants: List['StatutChecklist'] = attr.Factory(list)
    statut: Optional[ChoixStatutChecklist] = None
    extra: Dict[str, any] = attr.Factory(dict)

    @classmethod
    def from_dict(cls, item: Dict[str, any]):
        return cls(
            libelle=item.get('libelle', ''),
            statut=ChoixStatutChecklist[item['statut']] if item.get('statut') else None,
            enfants=[cls.from_dict(enfant) for enfant in item.get('enfants', [])],
            extra=item.get('extra', {}),
        )

    def to_dict(self):
        return attr.asdict(self, value_serializer=self._serialize)

    def _serialize(cls, inst, field, value):
        if isinstance(value, Enum):
            return value.name

        return value


@attr.dataclass
class StatutsChecklistContinue:
    fiche_etudiant: StatutChecklist
    decision: StatutChecklist

    @classmethod
    def from_dict(cls, checklist_en_tant_que_dict: Dict[str, Dict[str, any]]):
        checklist_by_tab = {}
        for key in INDEX_ONGLETS_CHECKLIST:
            item = checklist_en_tant_que_dict.get(key, {})
            checklist_by_tab[key] = StatutChecklist.from_dict(item=item)
        return cls(**checklist_by_tab)

    def recuperer_enfant(self, onglet, identifiant_enfant) -> StatutChecklist:
        return next(
            enfant for enfant in getattr(self, onglet).enfants if enfant.extra.get('identifiant') == identifiant_enfant
        )


INDEX_ONGLETS_CHECKLIST = {
    onglet: index for index, onglet in enumerate(attr.fields_dict(StatutsChecklistContinue))  # type: ignore
}
