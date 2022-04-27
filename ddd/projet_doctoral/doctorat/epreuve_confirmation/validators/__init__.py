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
from ._should_avis_prolongation_etre_complete import ShouldAvisProlongationEtreComplete
from ._should_date_epreuve_etre_valide import ShouldDateEpreuveEtreValide
from ._should_demande_prolongation_etre_completee import ShouldDemandeProlongationEtreCompletee
from ._should_demande_prolongation_etre_definie import ShouldDemandeProlongationEtreDefinie
from ._should_epreuve_confirmation_etre_completee import ShouldEpreuveConfirmationEtreCompletee

__all__ = [
    "ShouldAvisProlongationEtreComplete",
    "ShouldDateEpreuveEtreValide",
    "ShouldDemandeProlongationEtreCompletee",
    "ShouldDemandeProlongationEtreDefinie",
    "ShouldEpreuveConfirmationEtreCompletee",
]
