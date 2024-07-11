# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import logging
from io import StringIO

import freezegun
from django.utils.timezone import now
from django.views.generic import TemplateView

from admission.ddd.admission.doctorat.preparation.commands import DeterminerAnneeAcademiqueEtPotQuery as DoctorateCmd
from admission.ddd.admission.doctorat.preparation.dtos import PropositionDTO
from admission.ddd.admission.dtos.conditions import InfosDetermineesDTO
from admission.ddd.admission.formation_continue.commands import DeterminerAnneeAcademiqueEtPotQuery as ContinuingCmd
from admission.ddd.admission.formation_generale.commands import DeterminerAnneeAcademiqueEtPotQuery as GeneralCmd
from admission.views.common.mixins import LoadDossierViewMixin
from osis_common.ddd.interface import BusinessException

__all__ = ['DebugView']


class DebugView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/debug.html'
    permission_required = "admission.view_debug_info"

    def get_context_data(self, **kwargs):
        from infrastructure.messages_bus import message_bus_instance

        data = super().get_context_data(**kwargs)

        # Install a temporary handler for the logging info
        logger = logging.getLogger('admission.ddd.admission.domain.service.i_calendrier_inscription')
        logger.setLevel(logging.DEBUG)
        with StringIO() as buffer, freezegun.freeze_time(self.request.GET.get("date-soumission")):
            handler = logging.StreamHandler(buffer)
            handler.setLevel(logging.DEBUG)
            logger.addHandler(handler)

            try:
                mapping = {
                    'doctorate': DoctorateCmd,
                    'general-education': GeneralCmd,
                    'continuing-education': ContinuingCmd,
                }
                cmd = mapping[self.current_context](self.admission_uuid)
                dto: 'InfosDetermineesDTO' = message_bus_instance.invoke(cmd)
                data['determined_academic_year'] = dto.annee
                data['determined_pool'] = dto.pool.name
                data['date_calcul'] = now().date()
            except BusinessException as e:
                data['exception'] = e
            finally:
                data['pool_logs'] = buffer.getvalue()

            logger.removeHandler(handler)

        logger = logging.getLogger('CalculFinancabilite')
        logger.setLevel(logging.INFO)
        with StringIO() as buffer, freezegun.freeze_time(self.request.GET.get("date-soumission")):
            handler = logging.StreamHandler(buffer)
            handler.setLevel(logging.INFO)
            logger.addHandler(handler)
            from ddd.logic.financabilite.commands import DeterminerSiCandidatEstFinancableQuery

            formation = self.proposition.doctorat if self.is_doctorate else self.proposition.formation

            financabilite = message_bus_instance.invoke(
                DeterminerSiCandidatEstFinancableQuery(
                    matricule_fgs=self.proposition.matricule_candidat,
                    sigle_formation=formation.sigle,
                    annee=formation.annee,
                    est_en_reorientation=False,
                )
            )
            data['financabilite'] = financabilite
            data['financabilite_logs'] = buffer.getvalue()
            logger.removeHandler(handler)

        return data
