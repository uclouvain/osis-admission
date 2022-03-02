# ##############################################################################
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
# ##############################################################################
import datetime
from typing import List, Optional

import attr

from admission.ddd.projet_doctoral.preparation.domain.model._candidat_signaletique import CandidatSignaletique
from admission.ddd.projet_doctoral.preparation.domain.validator.exceptions import (
    CarteIdentiteeNonSpecifieeException,
    DateOuAnneeNaissanceNonSpecifieeException,
    DetailsPasseportNonSpecifiesException,
    IdentificationNonCompleteeException,
    NumeroIdentiteBelgeNonSpecifieException,
    NumeroIdentiteNonSpecifieException,
)
from base.ddd.utils.business_validator import BusinessValidator

BE_ISO_CODE = 'BE'


@attr.dataclass(frozen=True, slots=True)
class ShouldSignaletiqueCandidatEtreCompletee(BusinessValidator):
    signaletique: 'CandidatSignaletique'

    def validate(self, *args, **kwargs):
        champs_obligatoires = [
            'nom',
            'prenom',
            'sexe',
            'genre',
            'pays_nationalite',
            'photo_identite',
            'langue_contact',
        ]
        if not all([getattr(self.signaletique, champ_obligatoire) for champ_obligatoire in champs_obligatoires]):
            raise IdentificationNonCompleteeException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatSpecifierNumeroIdentite(BusinessValidator):
    numero_registre_national_belge: Optional[str]
    numero_carte_identite: Optional[str]
    numero_passeport: Optional[str]

    def validate(self, *args, **kwargs):
        if not (self.numero_registre_national_belge or self.numero_carte_identite or self.numero_passeport):
            raise NumeroIdentiteNonSpecifieException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatBelgeSpecifierNumeroRegistreNationalBelge(BusinessValidator):
    numero_registre_national_belge: Optional[str]
    pays_nationalite: Optional[str]

    def validate(self, *args, **kwargs):
        if self.pays_nationalite == BE_ISO_CODE and not self.numero_registre_national_belge:
            raise NumeroIdentiteBelgeNonSpecifieException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatSpecifierDateOuAnneeNaissance(BusinessValidator):
    date_naissance: Optional[datetime.date]
    annee_naissance: Optional[int]

    def validate(self, *args, **kwargs):
        if not (self.date_naissance or self.annee_naissance):
            raise DateOuAnneeNaissanceNonSpecifieeException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatAuthentiquerPasseport(BusinessValidator):
    numero_passeport: Optional[str]
    passeport: List[str]
    date_expiration_passeport: Optional[datetime.date]

    def validate(self, *args, **kwargs):
        if self.numero_passeport and (not self.passeport or not self.date_expiration_passeport):
            raise DetailsPasseportNonSpecifiesException


@attr.dataclass(frozen=True, slots=True)
class ShouldCandidatAuthentiquerIdentite(BusinessValidator):
    numero_registre_national_belge: Optional[str]
    numero_carte_identite: Optional[str]
    carte_identite: List[str]

    def validate(self, *args, **kwargs):
        if (self.numero_registre_national_belge or self.numero_carte_identite) and not self.carte_identite:
            raise CarteIdentiteeNonSpecifieeException
