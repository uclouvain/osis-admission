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
from enum import Enum
from typing import Dict, List, Optional

import attr
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    BesoinDeDerogation,
    ChoixStatutChecklist,
    DecisionCDDEnum,
    DerogationFinancement,
    OngletsChecklist,
)
from admission.ddd.admission.domain.model.enums.authentification import (
    EtatAuthentificationParcours,
)
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
class StatutsChecklistDoctorale:
    donnees_personnelles: StatutChecklist
    assimilation: StatutChecklist
    parcours_anterieur: StatutChecklist
    financabilite: StatutChecklist
    choix_formation: StatutChecklist
    projet_recherche: StatutChecklist
    decision_cdd: StatutChecklist
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
    onglet: index for index, onglet in enumerate(attr.fields_dict(StatutsChecklistDoctorale))  # type: ignore
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

onglet_donnes_personnelles = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.donnees_personnelles,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='A_TRAITER',
            libelle=_('To be processed'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        ),
        ConfigurationStatutChecklist(
            identifiant='A_COMPLETER',
            libelle=_('To be completed'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'fraud': '0'},
        ),
        ConfigurationStatutChecklist(
            identifiant='FRAUDEUR',
            libelle=_('Fraudster'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'fraud': '1'},
        ),
        ConfigurationStatutChecklist(
            identifiant='VALIDEES',
            libelle=_('Validated'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ),
    ],
)

onglet_assimilation = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.assimilation,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='NON_CONCERNE',
            libelle=_('Not concerned'),
            statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
        ),
        ConfigurationStatutChecklist(
            identifiant='DECLARE_ASSIMILE_OU_PAS',
            libelle=_('Declared assimilated or not'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        ),
        ConfigurationStatutChecklist(
            identifiant='A_COMPLETER',
            libelle=_('To be completed'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
        ),
        ConfigurationStatutChecklist(
            identifiant='AVIS_EXPERT',
            libelle=_('Expert opinion'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
        ),
        ConfigurationStatutChecklist(
            identifiant='A_COMPLETER_APRES_INSCRIPTION',
            libelle=_('To be completed after application'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR,
        ),
        ConfigurationStatutChecklist(
            identifiant='VALIDEE',
            libelle=pgettext_lazy('assimilation-checklist', 'Validated'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ),
    ],
)

onglet_parcours_anterieur = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.parcours_anterieur,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='A_TRAITER',
            libelle=_('To be processed'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        ),
        ConfigurationStatutChecklist(
            identifiant='TOILETTE',
            libelle=_('Cleaned'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
        ),
        ConfigurationStatutChecklist(
            identifiant='INSUFFISANT',
            libelle=_('Insufficient'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
        ),
        ConfigurationStatutChecklist(
            identifiant='SUFFISANT',
            libelle=_('Sufficient'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ),
    ],
)

onglets_parcours_anterieur_experiences = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.experiences_parcours_anterieur,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='A_TRAITER',
            libelle=_('To be processed'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        ),
        ConfigurationStatutChecklist(
            identifiant='A_COMPLETER',
            libelle=_('To be completed'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
        ),
        ConfigurationStatutChecklist(
            identifiant='AUTHENTIFICATION',
            libelle=_('Authentication'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={'authentification': '1'},
        ),
    ]
    + [
        ConfigurationStatutChecklist(
            identifiant=f'AUTHENTIFICATION.{etat_authentification.name}',
            libelle=etat_authentification.value,
            statut=None,
            extra={
                'etat_authentification': etat_authentification.name,
            },
            identifiant_parent='AUTHENTIFICATION',
        )
        for etat_authentification in EtatAuthentificationParcours
    ]
    + [
        ConfigurationStatutChecklist(
            identifiant='AVIS_EXPERT',
            libelle=_('Expert advice'),
            extra={'authentification': '0'},
            statut=ChoixStatutChecklist.GEST_EN_COURS,
        ),
        ConfigurationStatutChecklist(
            identifiant='A_COMPLETER_APRES_INSCRIPTION',
            libelle=_('To complete after enrolment'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR,
        ),
        ConfigurationStatutChecklist(
            identifiant='VALIDEE',
            libelle=_('Validated'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ),
    ],
)

onglet_financabilite = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.financabilite,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='NON_CONCERNE',
            libelle=_('Not concerned'),
            statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
        ),
        ConfigurationStatutChecklist(
            identifiant='A_TRAITER',
            libelle=_('To be processed'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        ),
        ConfigurationStatutChecklist(
            identifiant='AVIS_EXPERT',
            libelle=_('Expert opinion'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={'en_cours': 'expert'},
        ),
        ConfigurationStatutChecklist(
            identifiant='BESOIN_DEROGATION',
            libelle=_('Dispensation needed'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={'en_cours': 'derogation'},
        ),
    ]
    + [
        ConfigurationStatutChecklist(
            identifiant=f'BESOIN_DEROGATION.{besoin_derogation.name}',
            libelle=besoin_derogation.value,
            statut=None,
            extra={
                'etat_besoin_derogation': besoin_derogation.name,
            },
            identifiant_parent='BESOIN_DEROGATION',
        )
        for besoin_derogation in DerogationFinancement
    ]
    + [
        ConfigurationStatutChecklist(
            identifiant='A_COMPLETER',
            libelle=_('To be completed'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'to_be_completed': '1'},
        ),
        ConfigurationStatutChecklist(
            identifiant='NON_FINANCABLE',
            libelle=_('Not financeable'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'to_be_completed': '0'},
        ),
        ConfigurationStatutChecklist(
            identifiant='DEROGATION_ACCORDEE',
            libelle=_('Dispensation granted'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
            extra={'reussite': 'derogation'},
        ),
        ConfigurationStatutChecklist(
            identifiant='FINANCABLE',
            libelle=_('Financeable'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
            extra={'reussite': 'financable'},
        ),
    ],
)

onglet_choix_formation = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.choix_formation,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='A_TRAITER',
            libelle=_('To be processed'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        ),
        ConfigurationStatutChecklist(
            identifiant='VALIDE',
            libelle=_('Validated'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ),
    ],
)

onglet_projet_recherche = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.projet_recherche,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='A_TRAITER',
            libelle=_('To be processed'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        ),
        ConfigurationStatutChecklist(
            identifiant='A_COMPLETER',
            libelle=_('To be completed'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
        ),
        ConfigurationStatutChecklist(
            identifiant='VALIDE',
            libelle=_('Validated'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ),
    ],
)

onglet_decision_cdd = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.decision_cdd,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='A_TRAITER',
            libelle=_('To be processed'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        ),
        ConfigurationStatutChecklist(
            identifiant='PRIS_EN_CHARGE',
            libelle=_('Taken in charge'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
        ),
        ConfigurationStatutChecklist(
            identifiant='A_COMPLETER_PAR_SIC',
            libelle=_('To be completed by SIC'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'decision': DecisionCDDEnum.HORS_DECISION.name},
        ),
        ConfigurationStatutChecklist(
            identifiant='CLOTURE',
            libelle=_('Closed'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'decision': DecisionCDDEnum.CLOTURE.name},
        ),
        ConfigurationStatutChecklist(
            identifiant='REFUS',
            libelle=_('Refusal'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'decision': DecisionCDDEnum.EN_DECISION.name},
        ),
        ConfigurationStatutChecklist(
            identifiant='ACCORD',
            libelle=_('Approval'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ),
    ],
)

onglet_decision_sic = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.decision_sic,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='A_TRAITER',
            libelle=_('To be processed'),
            statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        ),
        ConfigurationStatutChecklist(
            identifiant='A_COMPLETER',
            libelle=_('Manager follow-up'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'blocage': 'to_be_completed'},
        ),
        ConfigurationStatutChecklist(
            identifiant='BESOIN_DEROGATION',
            libelle=_('Dispensation needed'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={'en_cours': 'derogation'},
        ),
    ]
    + [
        ConfigurationStatutChecklist(
            identifiant=f'BESOIN_DEROGATION.{etat_besoin_derogation.name}',
            libelle=etat_besoin_derogation.value,
            statut=None,
            extra={
                'etat_besoin_derogation': etat_besoin_derogation.name,
            },
            identifiant_parent='BESOIN_DEROGATION',
        )
        for etat_besoin_derogation in BesoinDeDerogation
    ]
    + [
        ConfigurationStatutChecklist(
            identifiant='REFUS_A_VALIDER',
            libelle=_('Refusal to validate'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={'en_cours': 'refusal'},
        ),
        ConfigurationStatutChecklist(
            identifiant='AUTORISATION_A_VALIDER',
            libelle=_('Approval to validate'),
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={'en_cours': 'approval'},
        ),
        ConfigurationStatutChecklist(
            identifiant='CLOTURE',
            libelle=_('Closed'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'blocage': 'closed'},
        ),
        ConfigurationStatutChecklist(
            identifiant='REFUSE',
            libelle=_('REFUSEE'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'blocage': 'refusal'},
        ),
        ConfigurationStatutChecklist(
            identifiant='AUTORISE',
            libelle=_('Approved'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ),
    ],
)

ORGANISATION_ONGLETS_CHECKLIST: List[ConfigurationOngletChecklist] = [
    onglet_donnes_personnelles,
    onglet_assimilation,
    onglet_parcours_anterieur,
    onglets_parcours_anterieur_experiences,
    onglet_financabilite,
    onglet_choix_formation,
    onglet_projet_recherche,
    onglet_decision_cdd,
    onglet_decision_sic,
]

ORGANISATION_ONGLETS_CHECKLIST_POUR_LISTING: List[ConfigurationOngletChecklist] = [
    onglet_decision_cdd,
    ConfigurationOngletChecklist(
        identifiant=onglet_decision_sic.identifiant,
        statuts=[statut for statut in onglet_decision_sic.statuts if not statut.identifiant_parent],
    ),
]

ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT = {
    onglet.identifiant.name: {statut.identifiant: statut for statut in onglet.statuts}
    for onglet in ORGANISATION_ONGLETS_CHECKLIST
}
