# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.ddd.projet_doctoral.preparation.domain.model._membre_CA import MembreCAIdentity
from admission.ddd.projet_doctoral.preparation.domain.model._signature_promoteur import ChoixEtatSignature
from osis_common.ddd import interface


@attr.dataclass(frozen=True, slots=True)
class SignatureMembreCA(interface.ValueObject):
    membre_CA_id: 'MembreCAIdentity'
    etat: ChoixEtatSignature = ChoixEtatSignature.NOT_INVITED
    date: Optional[datetime.datetime] = None
    commentaire_externe: str = ''
    commentaire_interne: str = ''
    motif_refus: str = ''
    pdf: List[str] = attr.Factory(list)
