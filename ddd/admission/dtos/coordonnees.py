##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Optional

import attr

from admission.admission_utils.format_address import format_address
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class AdressePersonnelleDTO(interface.DTO):
    rue: str
    code_postal: str
    ville: str
    pays: str
    nom_pays: str
    numero_rue: str
    boite_postale: str
    destinataire: str = ''

    def adresse_formatee(self, separator):
        return format_address(
            street=self.rue,
            street_number=self.numero_rue,
            postal_code=self.code_postal,
            city=self.ville,
            country=self.nom_pays,
            separator=separator,
        )


@attr.dataclass(frozen=True, slots=True)
class CoordonneesDTO(interface.DTO):
    domicile_legal: Optional[AdressePersonnelleDTO]
    adresse_correspondance: Optional[AdressePersonnelleDTO]
    numero_mobile: str
    adresse_email_privee: str
    numero_contact_urgence: str

    def adresse_domicile_legale_formatee(self, separator=', '):
        return self.domicile_legal.adresse_formatee(separator) if self.domicile_legal else ''

    def adresse_correspondance_formatee(self, separator=', '):
        return self.adresse_correspondance.adresse_formatee(separator) if self.adresse_correspondance else ''
