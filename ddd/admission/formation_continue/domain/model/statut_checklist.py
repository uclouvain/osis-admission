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
from django.utils.translation import gettext_lazy as _, pgettext_lazy

from admission.ddd.admission.formation_continue.domain.model.enums import ChoixStatutChecklist, OngletsChecklist
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
    decision: StatutChecklist
    fiche_etudiant: StatutChecklist

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


@attr.dataclass
class ConfigurationStatutChecklist(interface.ValueObject):
    identifiant: str
    libelle: str
    statut: Optional[ChoixStatutChecklist] = None
    extra: Dict[str, any] = attr.Factory(dict)
    identifiant_parent: Optional[str] = None

    def matches_dict(self, other_configuration_as_dictionary: Dict[str, any]) -> bool:
        """
        Check if this configuration matches the other one.
        :param other_configuration_as_dictionary: A dictionary containing the other configuration.
        :return: True if this configuration matches the other one, False otherwise.
        """
        return self.matches(
            other_configuration_as_dictionary.get('statut', ''),
            other_configuration_as_dictionary.get('extra', {}),
        )

    def matches(self, status: str, extra: Optional[Dict[str, any]] = None) -> bool:
        """
        Check if this configuration matches the given status and extra.
        :param status: the status to match.
        :param extra: the extra to match.
        :return: True if this configuration matches the given status and extra, False otherwise.
        """
        if extra is None:
            extra = {}

        return bool(self.statut) and self.statut.name == status and self.extra.items() <= extra.items()

    def merge_statuses(self, other_status):
        return ConfigurationStatutChecklist(
            identifiant=self.identifiant,
            libelle=self.libelle,
            statut=self.statut or other_status.statut,
            extra={**self.extra, **other_status.extra},
            identifiant_parent=self.identifiant_parent,
        )


@attr.dataclass
class ConfigurationOngletChecklist(interface.ValueObject):
    identifiant: OngletsChecklist
    statuts: List[ConfigurationStatutChecklist]

    def get_status(self, status: str, extra: Optional[Dict[str, any]] = None) -> Optional[ConfigurationStatutChecklist]:
        return next((statut for statut in self.statuts if statut.matches(status, extra)), None)


STATUTS_CHECKLIST_PAR_ONGLET: Dict[str, Dict[str, ConfigurationStatutChecklist]] = {}


onglet_decision = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.decision,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='A_TRAITER',
            libelle=_('To be processed'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        ),
        ConfigurationStatutChecklist(
            identifiant='PRISE_EN_CHARGE',
            libelle=_('Taken in charge'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={'en_cours': 'taken_in_charge'},
        ),
        ConfigurationStatutChecklist(
            identifiant='ACCORD_FAC',
            libelle=_('Fac approval'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={'en_cours': 'fac_approval'},
        ),
        ConfigurationStatutChecklist(
            identifiant='MISE_EN_ATTENTE',
            libelle=_('On hold'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={'en_cours': 'on_hold'},
        ),
        ConfigurationStatutChecklist(
            identifiant='REFUSEE',
            libelle=_('Denied'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'blocage': 'denied'},
        ),
        ConfigurationStatutChecklist(
            identifiant='ANNULEE',
            libelle=_('Canceled'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'blocage': 'canceled'},
        ),
        ConfigurationStatutChecklist(
            identifiant='A_VALIDER',
            libelle=_('To validate IUFC'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={'en_cours': 'to_validate'},
        ),
        ConfigurationStatutChecklist(
            identifiant='VALIDEE',
            libelle=pgettext_lazy('decision-checklist', 'Validated'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ),
    ],
)


ORGANISATION_ONGLETS_CHECKLIST: List[ConfigurationOngletChecklist] = [
    onglet_decision,
]

ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT = {
    onglet.identifiant.name: {statut.identifiant: statut for statut in onglet.statuts}
    for onglet in ORGANISATION_ONGLETS_CHECKLIST
}
