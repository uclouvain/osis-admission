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

from admission.ddd.preparation.projet_doctoral.domain.model._candidat_signaletique import CandidatSignaletique
from base.ddd.utils.business_validator import BusinessValidator
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import (
    IdentificationNonCompleteeException,
    NumeroIdentiteBelgeNonSpecifieException,
    DateOuAnneeNaissanceNonSpecifieeException,
    DetailsPasseportNonSpecifiesException,
    CarteIdentiteeNonSpecifieeException,
    NumeroIdentiteNonSpecifieException,
)

BE_ISO_CODE = 'BE'


@attr.s(frozen=True, slots=True)
class ShouldSignaletiqueCandidatEtreCompletee(BusinessValidator):
    signaletique = attr.ib(type='CandidatSignaletique')  # type: CandidatSignaletique

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


@attr.s(frozen=True, slots=True)
class ShouldCandidatSpecifierNumeroIdentite(BusinessValidator):
    numero_registre_national_belge = attr.ib(type=Optional[str])
    numero_carte_identite = attr.ib(type=Optional[str])
    numero_passeport = attr.ib(type=Optional[str])

    def validate(self, *args, **kwargs):
        if not (self.numero_registre_national_belge or self.numero_carte_identite or self.numero_passeport):
            raise NumeroIdentiteNonSpecifieException


@attr.s(frozen=True, slots=True)
class ShouldCandidatBelgeSpecifierNumeroRegistreNationalBelge(BusinessValidator):
    numero_registre_national_belge = attr.ib(type=Optional[str])
    pays_nationalite = attr.ib(type=Optional[str])

    def validate(self, *args, **kwargs):
        if self.pays_nationalite == BE_ISO_CODE and not self.numero_registre_national_belge:
            raise NumeroIdentiteBelgeNonSpecifieException


@attr.s(frozen=True, slots=True)
class ShouldCandidatSpecifierDateOuAnneeNaissance(BusinessValidator):
    date_naissance = attr.ib(type=Optional[datetime.date])
    annee_naissance = attr.ib(type=Optional[int])

    def validate(self, *args, **kwargs):
        if not (self.date_naissance or self.annee_naissance):
            raise DateOuAnneeNaissanceNonSpecifieeException


@attr.s(frozen=True, slots=True)
class ShouldCandidatAuthentiquerPasseport(BusinessValidator):
    numero_passeport = attr.ib(type=Optional[str])
    passeport = attr.ib(type=List[str])
    date_expiration_passeport = attr.ib(type=Optional[datetime.date])

    def validate(self, *args, **kwargs):
        if self.numero_passeport and (not self.passeport or not self.date_expiration_passeport):
            raise DetailsPasseportNonSpecifiesException


@attr.s(frozen=True, slots=True)
class ShouldCandidatAuthentiquerIdentite(BusinessValidator):
    numero_registre_national_belge = attr.ib(type=Optional[str])
    numero_carte_identite = attr.ib(type=Optional[str])
    carte_identite = attr.ib(type=List[str])

    def validate(self, *args, **kwargs):
        if (self.numero_registre_national_belge or self.numero_carte_identite) and not self.carte_identite:
            raise CarteIdentiteeNonSpecifieeException
