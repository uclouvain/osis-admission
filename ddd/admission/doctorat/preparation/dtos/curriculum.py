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

from functools import reduce

import attr

from admission.ddd import NB_MOIS_MIN_VAE
from ddd.logic.shared_kernel.profil.dtos.parcours_externe import (
    CurriculumDTO,
    MessageCurriculumDTO,
)

message_candidat_avec_pae_avant_2015 = MessageCurriculumDTO(
    annee=2015,
    gabarit='admission/general_education/includes/checklist/curriculum_pae_avant_2015_message.html',
)


@attr.dataclass(frozen=True, slots=True)
class CurriculumAdmissionDTO(CurriculumDTO):
    @property
    def candidat_est_potentiel_vae(self) -> bool:
        """
        Un candidat est potentiel vae si la durée de l'ensemble de ses expériences non academiques est supérieure à 36.
        """
        return (
            reduce(
                lambda total, experience: self._compte_nombre_mois(total, experience),
                self.experiences_non_academiques,
                0,
            )
            >= NB_MOIS_MIN_VAE
        )
