# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.shared_kernel.email_destinataire.dtos.destinataire import InformationsDestinataireDTO
from admission.ddd.admission.shared_kernel.email_destinataire.queries import RecupererInformationsDestinataireQuery
from admission.ddd.admission.shared_kernel.email_destinataire.repository.i_email_destinataire import \
    IEmailDestinataireRepository


def recuperer_informations_destinataire(
    query: 'RecupererInformationsDestinataireQuery',
    email_destinataire_repository: 'IEmailDestinataireRepository',
) -> 'InformationsDestinataireDTO':
    return email_destinataire_repository.get_informations_destinataire_dto(
        sigle_programme=query.sigle_formation,
        annee=query.annee,
        pour_premiere_annee=query.est_premiere_annee,
    )
