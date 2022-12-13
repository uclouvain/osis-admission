##############################################################################
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
##############################################################################
from typing import List, Optional

import attr

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class ComptabiliteDTO(interface.DTO):
    # Absence de dettes
    attestation_absence_dette_etablissement: List[str]

    # Affiliations
    etudiant_solidaire: Optional[bool]

    # Compte bancaire
    type_numero_compte: Optional[str]
    numero_compte_iban: Optional[str]
    iban_valide: Optional[bool]
    numero_compte_autre_format: Optional[str]
    code_bic_swift_banque: Optional[str]
    prenom_titulaire_compte: Optional[str]
    nom_titulaire_compte: Optional[str]


@attr.dataclass(frozen=True, slots=True)
class ConditionsComptabiliteDTO(interface.DTO):
    pays_nationalite_ue: Optional[bool]
    a_frequente_recemment_etablissement_communaute_fr: Optional[bool]
