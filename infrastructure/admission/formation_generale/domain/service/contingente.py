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
from django.db import connection

from admission.calendar.admission_calendar import SIGLES_WITH_QUOTA
from admission.ddd.admission.formation_generale.domain.model.enums import (
    STATUTS_PROPOSITION_GENERALE_SOUMISE,
)
from admission.ddd.admission.formation_generale.domain.model.proposition import (
    Proposition,
)
from admission.ddd.admission.formation_generale.domain.service.i_contingente import (
    IContingente,
)
from admission.ddd.admission.formation_generale.domain.validator.exceptions import (
    UneSeuleFormationContingentePossible,
)
from admission.models import GeneralEducationAdmission

SEQUENCE_PATTERN = "admission_contingente_{year}_{acronym}_seq"


class Contingente(IContingente):
    @classmethod
    def generer_numero_de_dossier_ares_si_necessaire(cls, proposition: 'Proposition', annee: int) -> str:
        acronym = proposition.formation_id.sigle
        year = str(annee)

        if acronym not in SIGLES_WITH_QUOTA or not proposition.est_non_resident_au_sens_decret:
            return ""

        # Get next value from sequence
        sequence = SEQUENCE_PATTERN.format(
            year=year,
            acronym=acronym,
        )
        cursor = connection.cursor()
        cursor.execute("CREATE SEQUENCE IF NOT EXISTS %(sequence)s" % {'sequence': sequence})
        cursor.execute("SELECT NEXTVAL('%(sequence)s')" % {'sequence': sequence})
        index = cursor.fetchone()[0]

        return f"UCLouvain/{acronym[0]}-{year[-2:]}{index:04}"

    @classmethod
    def verifier_proposition_contingente_unique(cls, proposition: 'Proposition'):
        if proposition.formation_id.sigle not in SIGLES_WITH_QUOTA or not proposition.est_non_resident_au_sens_decret:
            return
        if GeneralEducationAdmission.objects.filter(
            candidate__global_id=proposition.matricule_candidat,
            status__in=STATUTS_PROPOSITION_GENERALE_SOUMISE,
            training__acronym__in=SIGLES_WITH_QUOTA,
            training__academic_year__year=proposition.formation_id.annee,
            is_non_resident=True,
        ).exists():
            raise UneSeuleFormationContingentePossible()
