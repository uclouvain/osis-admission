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

from admission.ddd.admission.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutChecklist,
    BesoinDeDerogation,
    DecisionFacultaireEnum,
    OngletsChecklist,
    DerogationFinancement,
)
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


@attr.dataclass
class ConfigurationStatutChecklist(interface.ValueObject):
    identifiant: str
    libelle: str
    statut: ChoixStatutChecklist
    extra: Dict[str, any] = attr.Factory(dict)

    def matches(self, other_configuration_as_dictionary: Dict[str, any]) -> bool:
        """
        Check if this configuration matches the other one.
        :param other_configuration_as_dictionary: A dictionary containing the other configuration.
        :return: True if this configuration matches the other one, False otherwise.
        """
        return (
            self.statut.name == other_configuration_as_dictionary.get('statut', '')
            and self.extra.items() <= other_configuration_as_dictionary.get('extra', {}).items()
        )


@attr.dataclass
class ConfigurationOngletChecklist(interface.ValueObject):
    identifiant: OngletsChecklist
    statuts: List[ConfigurationStatutChecklist]


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

onglet_frais_dossier = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.frais_dossier,
    statuts=[
        ConfigurationStatutChecklist(
            identifiant='NON_CONCERNE',
            libelle=_('Not concerned'),
            statut=ChoixStatutChecklist.INITIAL_NON_CONCERNE,
        ),
        ConfigurationStatutChecklist(
            identifiant='DOIT_PAYER',
            libelle=_('Must pay'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
        ),
        ConfigurationStatutChecklist(
            identifiant='DISPENSE',
            libelle=_('Dispensed'),
            statut=ChoixStatutChecklist.GEST_REUSSITE,
        ),
        ConfigurationStatutChecklist(
            identifiant='PAYES',
            libelle=_('Payed'),
            statut=ChoixStatutChecklist.SYST_REUSSITE,
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
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={
                'etat_authentification': etat_authentification.name,
                'authentification': '1',
            },
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
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={
                'etat_besoin_derogation': besoin_derogation.name,
                'en_cours': 'derogation',
            },
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

onglet_specificites_formation = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.specificites_formation,
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
            identifiant='A_COMPLETER_APRES_INSCRIPTION',
            libelle=_('To be completed after application'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE_ULTERIEUR,
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

onglet_decision_facultaire = ConfigurationOngletChecklist(
    identifiant=OngletsChecklist.decision_facultaire,
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
            extra={'decision': DecisionFacultaireEnum.HORS_DECISION.value},
        ),
        ConfigurationStatutChecklist(
            identifiant='REFUS',
            libelle=_('Refusal'),
            statut=ChoixStatutChecklist.GEST_BLOCAGE,
            extra={'decision': DecisionFacultaireEnum.EN_DECISION.value},
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
            statut=ChoixStatutChecklist.GEST_EN_COURS,
            extra={
                'etat_besoin_derogation': etat_besoin_derogation.name,
                'en_cours': 'derogation',
            },
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
    onglet_frais_dossier,
    onglet_parcours_anterieur,
    onglets_parcours_anterieur_experiences,
    onglet_financabilite,
    onglet_choix_formation,
    onglet_specificites_formation,
    onglet_decision_facultaire,
    onglet_decision_sic,
]

ORGANISATION_ONGLETS_CHECKLIST_PAR_STATUT = {
    onglet.identifiant.name: {statut.identifiant: statut for statut in onglet.statuts}
    for onglet in ORGANISATION_ONGLETS_CHECKLIST
}
