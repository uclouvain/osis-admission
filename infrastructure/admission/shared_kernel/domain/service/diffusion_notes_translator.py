# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime

from admission.ddd.admission.shared_kernel.domain.service.i_diffusion_notes_translator import IDiffusionNotesTranslator
from ddd.logic.diffusion_des_notes.dto.autorisation_diffusion_de_notes import AutorisationDiffusionDeNotesDTO
from ddd.logic.diffusion_des_notes.dto.date_diffusion_de_notes_individuelle import DateDiffusionDeNotesDTO
from ddd.logic.diffusion_des_notes.queries import GetDateDiffusionDeNotesQuery, ListerAutorisationDiffusionDeNotesQuery


class DiffusionNotesTranslator(IDiffusionNotesTranslator):
    @classmethod
    def recuperer_date_diffusion_notes_derniere_session(
        cls,
        sigle_formation: str,
        est_premiere_annee_bachelier: bool,
        noma: str,
        annee: int,
    ) -> datetime.date:
        from infrastructure.messages_bus import message_bus_instance

        marks_diffusion_date: DateDiffusionDeNotesDTO = message_bus_instance.invoke(
            GetDateDiffusionDeNotesQuery(
                sigle_formation=sigle_formation,
                premiere_annee=est_premiere_annee_bachelier,
                noma=noma,
                annee=annee,
                numero_session=3,
            )
        )

        return marks_diffusion_date.date

    @classmethod
    def recuperer_sessions_avec_autorisation_diffusion_resultats(
        cls,
        sigle_formation: str,
        noma: str,
        annee: int,
    ) -> set[int]:
        from infrastructure.messages_bus import message_bus_instance

        autorisations: list[AutorisationDiffusionDeNotesDTO] = message_bus_instance.invoke(
            ListerAutorisationDiffusionDeNotesQuery(
                sigle_formation=sigle_formation,
                noma=noma,
                annee=annee,
            )
        )

        return {autorisation.numero_session for autorisation in autorisations}
