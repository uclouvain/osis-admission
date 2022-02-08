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

from admission.ddd.preparation.projet_doctoral.domain.model._detail_projet import DetailProjet
from admission.ddd.preparation.projet_doctoral.domain.model._enums import ChoixTypeAdmission
from admission.ddd.preparation.projet_doctoral.domain.model._financement import Financement, financement_non_rempli
from base.ddd.utils.business_validator import BusinessValidator
from admission.ddd.preparation.projet_doctoral.business_types import *
from admission.ddd.preparation.projet_doctoral.domain.validator.exceptions import DetailProjetNonCompleteException


@attr.s(frozen=True, slots=True)
class ShouldProjetEtreComplet(BusinessValidator):
    type_admission = attr.ib(type=ChoixTypeAdmission)
    projet = attr.ib(type="DetailProjet")  # type: DetailProjet
    financement = attr.ib(type="Financement")  # type: Financement

    def validate(self, *args, **kwargs):
        champs_obligatoires = [
            "titre",
            "resume",
            "langue_redaction_these",
            "documents",
        ]
        if self.type_admission == ChoixTypeAdmission.ADMISSION:
            champs_obligatoires.append("proposition_programme_doctoral")

        if (
            not all([getattr(self.projet, champ_obligatoire) for champ_obligatoire in champs_obligatoires])
            or self.financement == financement_non_rempli
        ):
            raise DetailProjetNonCompleteException
