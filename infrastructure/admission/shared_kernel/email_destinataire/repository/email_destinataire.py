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

from typing import Optional, List

from django.db.models import F

from admission.ddd.admission.shared_kernel.email_destinataire.domain.validator.exceptions import \
    InformationsDestinatairePasTrouvee
from admission.ddd.admission.shared_kernel.email_destinataire.dtos.destinataire import InformationsDestinataireDTO
from admission.ddd.admission.shared_kernel.email_destinataire.repository.i_email_destinataire import \
    IEmailDestinataireRepository
from epc.models.email_fonction_programme import EmailFonctionProgramme


class EmailDestinataireRepository(IEmailDestinataireRepository):
    @classmethod
    def get_informations_destinataire_dto(
        cls,
        sigle_programme: str,
        annee: int,
        pour_premiere_annee: bool,
    ) -> 'InformationsDestinataireDTO':
        try:
            email_fonction = (
                EmailFonctionProgramme.objects.filter(premiere_annee=pour_premiere_annee)
                .annotate(
                    sigle_formation=F('programme__educationgroupyear__acronym'),
                    annee=F('programme__educationgroupyear__academic_year__year'),
                )
                .get(
                    sigle_formation=sigle_programme.replace('-1', '') if pour_premiere_annee else sigle_programme,
                    annee=annee,
                )
                .values('en_tete', 'email', 'sigle_formation', 'annee', 'premiere_annee')
            )
        except EmailFonctionProgramme.DoesNotExist as e:
            raise InformationsDestinatairePasTrouvee from e
        return InformationsDestinataireDTO(
            en_tete=email_fonction.get('en_tete'),
            email=email_fonction.get('email'),
            sigle_formation=email_fonction.get('sigle_formation'),
            annee=email_fonction.get('annee'),
            pour_premiere_annee=email_fonction.get('premiere_annee'),
        )

    @classmethod
    def get(cls, entity_id: 'EntityIdentity') -> 'RootEntity':
        pass

    @classmethod
    def search(cls, entity_ids: Optional[List['EntityIdentity']] = None, **kwargs) -> List['RootEntity']:
        pass

    @classmethod
    def delete(cls, entity_id: 'EntityIdentity', **kwargs: 'ApplicationService') -> None:
        pass

    @classmethod
    def save(cls, entity: 'RootEntity') -> None:
        pass
