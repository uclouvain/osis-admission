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
import datetime
from decimal import Decimal
from typing import List, Optional, Union

import attr

from epc.models.enums.decision_resultat_cycle import DecisionResultatCycle
from osis_common.ddd import interface
from osis_profile.models.enums.curriculum import Grade


@attr.dataclass(frozen=True, slots=True)
class ActeurDTO(interface.DTO):
    nom_acteur: str
    prenom_acteur: str
    institut: str
    pays: str

    def __str__(self):
        return f'{self.nom_acteur} {self.prenom_acteur} ({self.institut}{", " + self.pays if self.pays else ""})'


@attr.dataclass(frozen=True, slots=True)
class ExperienceAcademiqueDTO(interface.DTO):
    nom_institut: str
    grade_obtenu: Optional[Union[Grade, DecisionResultatCycle]]
    nom_formation: str
    credits_acquis: Optional[Decimal]
    est_diplome: bool
    date_diplome: Optional[datetime.date]

    def __str__(self):
        return (
            f'{self.nom_formation} - '
            f'{self.nom_institut} - '
            f'{self.date_diplome.isoformat() if self.date_diplome else ""} - '
            f'{self.credits_acquis if self.credits_acquis is not None else "X"} ECTS - '
            f'{self.grade_obtenu.value if self.grade_obtenu else ""}'
        )


@attr.dataclass(frozen=True, slots=True)
class DemandeRechercheDTO(interface.DTO):
    uuid: str
    numero_demande: str
    etat_demande: str

    nom_candidat: str
    prenom_candidat: str
    noma_candidat: str
    matricule_candidat: str
    sigle_formation: str
    code_formation: str
    intitule_formation: str

    decision_fac: str
    decision_sic: str

    signatures_completees: bool

    date_confirmation: Optional[datetime.datetime]

    derniere_modification_le: datetime.datetime
    type_admission: str

    cotutelle: Optional[bool]

    code_pays_nationalite_candidat: str = ''
    nom_pays_nationalite_candidat: str = ''

    code_bourse: str = ''

    prenom_auteur_derniere_modification: str = ''
    nom_auteur_derniere_modification: str = ''

    nom_institut_these: str = ''
    sigle_institut_these: str = ''
    titre_projet: str = ''

    # Les attributs suivants sont à None s'ils ne sont pas récupérés
    promoteurs: Optional[List[ActeurDTO]] = None
    membres_ca: Optional[List[ActeurDTO]] = None
    experiences_academiques_reussies_externes: Optional[List[ExperienceAcademiqueDTO]] = None
    experiences_academiques_reussies_internes: Optional[List[ExperienceAcademiqueDTO]] = None

    @property
    def formation(self) -> str:
        return f'{self.sigle_formation} - {self.intitule_formation}'

    @property
    def candidat(self) -> str:
        noma = f' ({self.noma_candidat})' if self.noma_candidat else ''
        return f'{self.nom_candidat}, {self.prenom_candidat}{noma}'

    @property
    def derniere_modification_par(self) -> str:
        return f'{self.nom_auteur_derniere_modification}, {self.prenom_auteur_derniere_modification[:1]}'

    @property
    def institut_these(self) -> str:
        institut_these = ''

        if self.nom_institut_these:
            institut_these += self.nom_institut_these

        if self.sigle_institut_these:
            institut_these += f' ({self.sigle_institut_these})'

        return institut_these
