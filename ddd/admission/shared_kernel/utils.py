# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.shared_kernel.domain.model.enums.authentification import EtatAuthentificationParcours
from admission.ddd.admission.formation_generale.domain.model.enums import ChoixStatutChecklist
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import StatutChecklist
from osis_profile.models.enums.experience_validation import ChoixStatutValidationExperience


def initialiser_checklist_experience(experience_uuid, statut, statut_authentification):
    return StatutChecklist(
        libelle=_('To be processed'),
        statut=statut,
        extra={
            'identifiant': experience_uuid,
            'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
        },
    )

def initialiser_dictionnaire_checklist_experience(checklist_tabs_organization, experience_uuid, statut, statut_authentification):
    configuration_statut = checklist_tabs_organization['experiences_parcours_anterieur'][statut]

    return {
        'macro_statut': statut,
        'statut': configuration_statut.statut.name,
        'libelle': ChoixStatutValidationExperience[statut].value,
        'extra': {
            'identifiant': experience_uuid,
            'etat_authentification': statut_authentification,
            **configuration_statut.extra,
        },

    }
    return StatutChecklist(
        libelle=_('To be processed'),
        statut=ChoixStatutChecklist.INITIAL_CANDIDAT,
        extra={
            'identifiant': experience_uuid,
            'etat_authentification': EtatAuthentificationParcours.NON_CONCERNE.name,
        },
    )
