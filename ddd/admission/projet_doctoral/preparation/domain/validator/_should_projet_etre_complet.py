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

from admission.ddd.admission.projet_doctoral.preparation.domain.model._detail_projet import DetailProjet
from admission.ddd.admission.projet_doctoral.preparation.domain.model._enums import ChoixTypeAdmission
from admission.ddd.admission.projet_doctoral.preparation.domain.model._financement import (
    ChoixTypeFinancement,
    Financement,
    financement_non_rempli,
)
from admission.ddd.admission.projet_doctoral.preparation.domain.validator.exceptions import (
    DetailProjetNonCompleteException,
)
from base.ddd.utils.business_validator import BusinessValidator


@attr.dataclass(frozen=True, slots=True)
class ShouldProjetEtreComplet(BusinessValidator):
    type_admission: ChoixTypeAdmission
    projet: 'DetailProjet'
    financement: 'Financement'

    def validate(self, *args, **kwargs):
        champs_obligatoires = [
            "titre",
            "resume",
            "langue_redaction_these",
            "documents",
        ]
        if self.type_admission == ChoixTypeAdmission.ADMISSION:
            champs_obligatoires.append("proposition_programme_doctoral")

        champs_financements_obligatoires = [
            "duree_prevue",
            "temps_consacre",
        ]
        if (
            # projet
            not all([getattr(self.projet, champ_obligatoire) for champ_obligatoire in champs_obligatoires])
            # financement
            or self.financement == financement_non_rempli
            or not all([getattr(self.financement, champ) for champ in champs_financements_obligatoires])
            # bourse
            or (
                self.financement.type == ChoixTypeFinancement.SEARCH_SCHOLARSHIP
                and (
                    not self.financement.bourse_date_debut
                    or not self.financement.bourse_date_fin
                    or not self.financement.bourse_preuve
                )
            )
        ):
            raise DetailProjetNonCompleteException
