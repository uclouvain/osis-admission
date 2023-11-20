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

from typing import List, Optional, Dict

from django.conf import settings
from django.db.models import OuterRef, Subquery, Q, F
from django.db.models.functions import JSONObject
from django.utils.translation import get_language

from admission.auth.roles.program_manager import ProgramManager
from admission.contrib.models.base import training_campus_subquery
from admission.ddd.admission.dtos.formation import BaseFormationDTO
from admission.ddd.admission.shared_kernel.role.repository.gestionnaire import IGestionnaireRepository
from base.models.education_group_year import EducationGroupYear


class GestionnaireRepository(IGestionnaireRepository):
    @classmethod
    def rechercher_formations_gerees(
        cls,
        matriculaire_gestionnaire: str,
        annee: int,
        terme_recherche: Optional[str],
    ) -> List['BaseFormationDTO']:

        current_language = get_language()

        translated_title = 'title' if current_language == settings.LANGUAGE_CODE_FR else 'title_english'

        sub_qs = EducationGroupYear.objects.filter(
            education_group_id=OuterRef('education_group_id'),
            academic_year__year=annee,
        ).annotate(
            lieu_enseignement=training_campus_subquery(training_field='pk'),
            json_training=JSONObject(
                uuid=F('uuid'),
                sigle=F('acronym'),
                intitule=F(translated_title),
                lieu_enseignement=F('lieu_enseignement'),
                annee=F('academic_year__year'),
            ),
        )

        if terme_recherche:
            sub_qs = sub_qs.filter(
                Q(**{f'{translated_title}__icontains': terme_recherche}) | Q(acronym__icontains=terme_recherche)
            )

        qs: List[Dict] = (
            ProgramManager.objects.filter(person__global_id=matriculaire_gestionnaire)
            .annotate(
                training=Subquery(sub_qs.values('json_training')[:1]),
            )
            .values_list('training', flat=True)
        )

        return [BaseFormationDTO(**training) for training in qs if training]
