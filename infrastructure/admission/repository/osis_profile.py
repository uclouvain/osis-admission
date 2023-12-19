# ##############################################################################
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
# ##############################################################################
from types import SimpleNamespace

from django.db import models

from admission.ddd.admission.doctorat.preparation.dtos import ExperienceAcademiqueDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceNonAcademiqueDTO
from admission.ddd.admission.repository.i_osis_profile import IOsisProfileRepository
from osis_profile.models import EducationalExperience, ProfessionalExperience


class OsisProfileRepository(IOsisProfileRepository):
    @classmethod
    def get_curriculum(cls, global_id: str) -> any:
        # add 2 zeros before global_id if it is not there already
        if global_id[0:2] != "00":
            global_id = "00" + global_id
        return {
            'educational': _convertir_en_liste_experience_academique_dto(
                list(EducationalExperience.objects.filter(person__global_id=global_id).annotate(
                    credits=models.Sum('educationalexperienceyear__acquired_credit_number'),
                    first_year=models.Min('educationalexperienceyear__academic_year__year'),
                    last_year=models.Max('educationalexperienceyear__academic_year__year'),
                ))),
            'professional': _convertir_en_liste_experience_non_academique_dto(
                list(ProfessionalExperience.objects.filter(person__global_id=global_id))
            ),
        }


def _convertir_en_liste_experience_academique_dto(liste_exp):
    return [ExperienceAcademiqueDTO(
        uuid=str(exp.uuid),
        pays=exp.country.name,
        nom_pays=exp.country.name,
        nom_institut=exp.institute.name,
        adresse_institut=exp.institute.main_address,
        code_institut=exp.institute.code,
        communaute_institut=exp.institute.get_community_display(),
        regime_linguistique='',
        nom_regime_linguistique='',
        type_releve_notes='',
        releve_notes=[''],
        traduction_releve_notes=[''],
        annees=[SimpleNamespace(annee=year) for year in range(exp.first_year, exp.last_year)],
        a_obtenu_diplome=exp.obtained_diploma,
        diplome=[''],
        traduction_diplome=[''],
        rang_diplome=exp.rank_in_diploma,
        date_prevue_delivrance_diplome=exp.expected_graduation_date,
        titre_memoire=exp.dissertation_title,
        note_memoire=exp.dissertation_score,
        resume_memoire=exp.dissertation_summary,
        grade_obtenu=exp.obtained_grade,
        systeme_evaluation=exp.get_evaluation_type_display(),
        nom_formation=exp.program.title,
        type_enseignement=exp.program.get_study_type_display(),
    ) for exp in liste_exp]


def _convertir_en_liste_experience_non_academique_dto(liste_exp):
    return [ExperienceNonAcademiqueDTO(
        uuid=str(exp.uuid),
        employeur=exp.institute_name,
        date_debut=exp.start_date,
        date_fin=exp.end_date,
        type=exp.get_type_display(),
        certificat=exp.certificate,
        fonction=exp.role,
        secteur=exp.get_sector_display(),
        autre_activite=exp.activity,
    ) for exp in liste_exp]
