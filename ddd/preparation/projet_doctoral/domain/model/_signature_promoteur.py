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
import attr
from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum
from admission.ddd.preparation.projet_doctoral.domain.model._promoteur import PromoteurIdentity
from osis_common.ddd import interface


class ChoixEtatSignature(ChoiceEnum):
    NOT_INVITED = _('NOT_INVITED')  # Pas encore envoyée au signataire
    INVITED = _('INVITED')  # Envoyée au signataire
    APPROVED = _('APPROVED')  # Approuvée par le signataire
    REFUSED = _('REFUSED')  # Refusée par le signataire


@attr.s(frozen=True, slots=True)
class SignaturePromoteur(interface.ValueObject):
    promoteur_id = attr.ib(type=PromoteurIdentity)
    etat = attr.ib(type=ChoixEtatSignature, default=ChoixEtatSignature.NOT_INVITED)
    commentaire_externe = attr.ib(type=str, default='')
    commentaire_interne = attr.ib(type=str, default='')
    motif_refus = attr.ib(type=str, default='')
