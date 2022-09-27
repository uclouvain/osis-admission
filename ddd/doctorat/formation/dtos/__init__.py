# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Union

from admission.ddd.doctorat.formation.dtos.communication import CommunicationDTO
from admission.ddd.doctorat.formation.dtos.conference import (
    ConferenceCommunicationDTO,
    ConferenceDTO,
    ConferencePublicationDTO,
)
from admission.ddd.doctorat.formation.dtos.cours import CoursDTO
from admission.ddd.doctorat.formation.dtos.epreuve import EpreuveDTO
from admission.ddd.doctorat.formation.dtos.publication import PublicationDTO
from admission.ddd.doctorat.formation.dtos.sejour import SejourCommunicationDTO, SejourDTO
from admission.ddd.doctorat.formation.dtos.seminaire import SeminaireCommunicationDTO, SeminaireDTO
from admission.ddd.doctorat.formation.dtos.service import ServiceDTO
from admission.ddd.doctorat.formation.dtos.valorisation import ValorisationDTO

ActiviteDTO = Union[
    'CommunicationDTO',
    'ConferenceDTO',
    'ConferenceCommunicationDTO',
    'ConferencePublicationDTO',
    'PublicationDTO',
    'SejourCommunicationDTO',
    'SejourDTO',
    'SeminaireDTO',
    'ServiceDTO',
    'ValorisationDTO',
    'SeminaireCommunicationDTO',
    'CoursDTO',
    'EpreuveDTO',
]

__all__ = [
    'ActiviteDTO',
    'CommunicationDTO',
    'ConferenceCommunicationDTO',
    'ConferenceDTO',
    'ConferencePublicationDTO',
    'PublicationDTO',
    'SejourCommunicationDTO',
    'SejourDTO',
    'SeminaireDTO',
    'ServiceDTO',
    'ValorisationDTO',
    'SeminaireCommunicationDTO',
    'CoursDTO',
    'EpreuveDTO',
]
