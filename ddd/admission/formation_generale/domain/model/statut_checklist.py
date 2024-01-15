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

from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutChecklist
from osis_common.ddd import interface


@attr.dataclass
class StatutChecklist(interface.ValueObject):
    libelle: str
    enfants: List['StatutChecklist'] = attr.Factory(list)
    statut: Optional[ChoixStatutChecklist] = None
    extra: Dict[str, any] = attr.Factory(dict)

    # @property
    # def statut(self) -> Optional[ChoixStatutChecklist]:
    #     if self.enfants:
    #         # Si tous les enfants sont ok, alors c'est ok
    #         if all(c.statut == ChoixStatutChecklist.GEST_REUSSITE for c in self.enfants):
    #             return ChoixStatutChecklist.GEST_REUSSITE
    #
    #         # Puis c'est selon la présence du plus urgent
    #         ordre = [
    #             ChoixStatutChecklist.GEST_BLOCAGE,
    #             ChoixStatutChecklist.GEST_EN_COURS,
    #             ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR,
    #             ChoixStatutChecklist.INITIAL_CANDIDAT,
    #             ChoixStatutChecklist.INITIAL_NON_CONCERNE,
    #         ]
    #         for statut in ordre:
    #             if any(c.statut == statut for c in self.enfants):
    #                 return statut
    #     return self.statut
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
class StatutsChecklistGenerale:
    donnees_personnelles: StatutChecklist
    assimilation: StatutChecklist
    frais_dossier: StatutChecklist
    parcours_anterieur: StatutChecklist
    financabilite: StatutChecklist
    choix_formation: StatutChecklist
    specificites_formation: StatutChecklist
    decision_facultaire: StatutChecklist
    decision_sic: StatutChecklist

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
    onglet: index for index, onglet in enumerate(attr.fields_dict(StatutsChecklistGenerale))  # type: ignore
}
