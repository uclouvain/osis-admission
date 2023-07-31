# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

from django import template

from admission.ddd.admission.doctorat.preparation.dtos import ExperienceAcademiqueDTO
from admission.ddd.admission.doctorat.preparation.dtos.curriculum import ExperienceNonAcademiqueDTO
from admission.ddd.admission.dtos import EtudesSecondairesDTO

register = template.Library()


@register.filter
def est_experience_academique(experience):
    return isinstance(experience, ExperienceAcademiqueDTO)


@register.filter
def est_experience_non_academique(experience):
    return isinstance(experience, ExperienceNonAcademiqueDTO)


@register.filter
def est_etudes_secondaires(experience):
    return isinstance(experience, EtudesSecondairesDTO)


@register.filter
def get_parcours_annee_background(experiences):
    if any(est_experience_academique(experience) for experience in experiences):
        return 'bg-info'
    if any(est_etudes_secondaires(experience) for experience in experiences):
        return 'bg-warning'
    return ""


@register.filter
def get_experience_last_year(experience: ExperienceAcademiqueDTO):
    try:
        return list(sorted((experience_annee.annee for experience_annee in experience.annees), reverse=True))[0]
    except IndexError:
        return None


@register.filter
def get_experience_year(experience: ExperienceAcademiqueDTO, annee):
    for experience_annee in experience.annees:
        if experience_annee.annee == annee:
            return experience_annee
    return None


@register.filter
def filter_experiences_trainings(experiences):
    experiences = {
        annee: [
            experience for experience in experiences.get(annee, []) if not est_experience_non_academique(experience)
        ]
        for annee in range(max(experiences), min(experiences) - 1, -1)
    }
    # Enlève les années vides en début et fin
    for annee in list(experiences.keys()):
        if not experiences[annee]:
            del experiences[annee]
        else:
            break
    for annee in reversed(list(experiences.keys())):
        if not experiences[annee]:
            del experiences[annee]
        else:
            break
    return experiences


@register.filter
def filter_experiences_financability(experiences):
    return {
        annee: [
            experience
            for experience in experiences_annee
            if not est_experience_non_academique(experience)
            or not any(est_experience_academique(exp) or est_etudes_secondaires(exp) for exp in experiences_annee)
        ]
        for annee, experiences_annee in experiences.items()
    }
