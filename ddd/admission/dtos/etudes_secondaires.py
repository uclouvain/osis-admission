# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional, List

import attr

from osis_common.ddd import interface


@attr.dataclass(slots=True, frozen=True)
class DiplomeBelgeEtudesSecondairesDTO(interface.DTO):
    certificat_inscription: List = attr.Factory(list)
    diplome: List = attr.Factory(list)
    type_enseignement: str = ''
    autre_type_enseignement: str = ''
    nom_institut: str = ''
    adresse_institut: str = ''
    communaute: str = ''


@attr.dataclass(slots=True, frozen=True)
class DiplomeEtrangerEtudesSecondairesDTO(interface.DTO):
    resultat: str = ''
    type_diplome: str = ''
    regime_linguistique: str = ''
    pays_regime_linguistique: str = ''
    pays_membre_ue: Optional[bool] = None
    pays_iso_code: str = ''
    pays_nom: str = ''
    releve_notes: List = attr.Factory(list)
    traduction_releve_notes: List = attr.Factory(list)
    diplome: List = attr.Factory(list)
    traduction_diplome: List = attr.Factory(list)
    certificat_inscription: List = attr.Factory(list)
    traduction_certificat_inscription: List = attr.Factory(list)
    equivalence: str = ''
    decision_final_equivalence_ue: List = attr.Factory(list)
    decision_final_equivalence_hors_ue: List = attr.Factory(list)
    preuve_decision_equivalence: List = attr.Factory(list)


@attr.dataclass(slots=True, frozen=True)
class AlternativeSecondairesDTO(interface.DTO):
    examen_admission_premier_cycle: List = attr.Factory(list)


@attr.dataclass(slots=True, frozen=True)
class EtudesSecondairesDTO(interface.DTO):
    diplome_belge: Optional[DiplomeBelgeEtudesSecondairesDTO] = None
    diplome_etranger: Optional[DiplomeEtrangerEtudesSecondairesDTO] = None
    alternative_secondaires: Optional[AlternativeSecondairesDTO] = None
    diplome_etudes_secondaires: str = ''
    annee_diplome_etudes_secondaires: Optional[int] = None
    valorisees: Optional[bool] = False
