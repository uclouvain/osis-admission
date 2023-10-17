##############################################################################
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
##############################################################################
import attr
from django.conf import settings
from django.utils.translation import get_language

from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class PosteDiplomatiqueDTO(interface.DTO):
    code: int
    nom_francais: str
    nom_anglais: str
    adresse_email: str

    def __str__(self):
        return '{nom} (<a href="mailto:{email}">{email}</a>)'.format(
            nom={
                settings.LANGUAGE_CODE_FR: self.nom_francais,
                settings.LANGUAGE_CODE_EN: self.nom_anglais,
            }.get(get_language()),
            email=self.adresse_email,
        )
