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
import attr

from admission.ddd.preparation.projet_doctoral.dtos import IdentificationDTO
from base.ddd.utils.business_validator import BusinessValidator
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import IdentificationNonCompleteeException

BE_ISO_CODE = "BE"  # TODO constant ?


@attr.s(frozen=True, slots=True)
class ShouldIdentificationCandidatEtreCompletee(BusinessValidator):
    identification = attr.ib(type="IdentificationDTO")  # type: IdentificationDTO

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

        for champ_obligatoire in champs_obligatoires:
            if not champ_obligatoire:
                raise IdentificationNonCompleteeException

        # TODO ne pas le demander s'il a eu une inscription identifiée précédemment
        if self.identification.annee_derniere_inscription is not None:
            raise IdentificationNonCompleteeException

        if not (self.identification.date_naissance or self.identification.annee_naissance):
            raise IdentificationNonCompleteeException

        if self.identification.pays_nationalite.iso_code == BE_ISO_CODE:
            if not self.identification.numero_registre_national_belge:
                raise IdentificationNonCompleteeException
        else:
            if not any((
                self.identification.numero_registre_national_belge,
                self.identification.numero_carte_identite,
                self.identification.numero_passeport
            ),):
                raise IdentificationNonCompleteeException

        if self.identification.numero_registre_national_belge or self.identification.numero_carte_identite:
            if not self.identification.carte_identite:
                raise IdentificationNonCompleteeException

        if self.identification.numero_passeport:
            if not self.identification.passeport or not self.identification.date_expiration_passeport:
                raise IdentificationNonCompleteeException


        # TODO diviser les validations