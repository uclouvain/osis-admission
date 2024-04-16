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
from django.utils.translation import gettext as _

from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from ddd.logic.shared_kernel.profil.dtos.etudes_secondaires import EtudesSecondairesDTO
from osis_common.ddd import interface
from osis_profile.models.enums.education import ForeignDiplomaTypes


@attr.dataclass(slots=True, frozen=True)
class DiplomeBelgeEtudesSecondairesDTO(interface.DTO):
    uuid: str = ''
    diplome: List = attr.Factory(list)
    type_enseignement: str = ''
    autre_type_enseignement: str = ''
    nom_institut: str = ''
    adresse_institut: str = ''
    communaute: str = ''

    def __str__(self):
        return _('CESS')


@attr.dataclass(slots=True, frozen=True)
class DiplomeEtrangerEtudesSecondairesDTO(interface.DTO):
    uuid: str = ''
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
    equivalence: str = ''
    decision_final_equivalence_ue: List = attr.Factory(list)
    decision_final_equivalence_hors_ue: List = attr.Factory(list)
    preuve_decision_equivalence: List = attr.Factory(list)

    def __str__(self):
        return str(ForeignDiplomaTypes.get_value(self.type_diplome))


@attr.dataclass(slots=True, frozen=True)
class AlternativeSecondairesDTO(interface.DTO):
    uuid: str = ''
    examen_admission_premier_cycle: List = attr.Factory(list)

    def __str__(self):
        return _("Bachelor's course entrance exam")


@attr.dataclass(slots=True, frozen=True)
class EtudesSecondairesAdmissionDTO(EtudesSecondairesDTO):
    @property
    def uuid(self):
        return OngletsDemande.ETUDES_SECONDAIRES.name
