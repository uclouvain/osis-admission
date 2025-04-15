# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from typing import List, Optional

from django.db.models import F

from admission.ddd.admission.shared_kernel.email_destinataire.domain.validator.exceptions import (
    InformationsDestinatairePasTrouvee,
)
from admission.ddd.admission.shared_kernel.email_destinataire.dtos.destinataire import (
    InformationsDestinataireDTO,
)
from admission.ddd.admission.shared_kernel.email_destinataire.repository.i_email_destinataire import (
    IEmailDestinataireRepository,
)
from epc.models.email_fonction_programme import EmailFonctionProgramme
from epc.models.enums.type_email_fonction_programme import TypeEmailFonctionProgramme


class EmailDestinataireRepository(IEmailDestinataireRepository):
    @classmethod
    def _get_base_qs(
        cls,
        sigle_programme: str,
        annee: int,
        pour_premiere_annee: bool,
    ):
        return (
            EmailFonctionProgramme.objects.filter(
                type=TypeEmailFonctionProgramme.DESTINATAIRE_ADMISSION.name,
                premiere_annee=pour_premiere_annee,
            )
            .annotate(
                sigle_formation=F('programme__educationgroupyear__acronym'),
                annee=F('programme__educationgroupyear__academic_year__year'),
            )
            .values('en_tete', 'email', 'sigle_formation', 'annee', 'premiere_annee')
            .filter(
                sigle_formation=sigle_programme.replace('-1', '') if pour_premiere_annee else sigle_programme,
                annee=annee,
            )
        )

    @classmethod
    def _build_dto(cls, email_fonction: dict) -> InformationsDestinataireDTO:
        return InformationsDestinataireDTO(
            en_tete=email_fonction.get('en_tete'),
            email=email_fonction.get('email'),
            sigle_formation=email_fonction.get('sigle_formation'),
            annee=email_fonction.get('annee'),
            pour_premiere_annee=email_fonction.get('premiere_annee'),
        )

    @classmethod
    def get_informations_destinataire_dto(
        cls,
        sigle_programme: str,
        annee: int,
        pour_premiere_annee: bool,
    ) -> 'InformationsDestinataireDTO':
        try:
            email_fonction = cls._get_base_qs(
                sigle_programme=sigle_programme,
                annee=annee,
                pour_premiere_annee=pour_premiere_annee,
            ).get()
        except EmailFonctionProgramme.DoesNotExist as e:
            raise InformationsDestinatairePasTrouvee from e
        return cls._build_dto(email_fonction=email_fonction)

    @classmethod
    def search_informations_destinataires_dto(
        cls,
        sigle_programme: str,
        annee: int,
        pour_premiere_annee: bool,
    ) -> List['InformationsDestinataireDTO']:
        emails_fonctions = cls._get_base_qs(
            sigle_programme=sigle_programme,
            annee=annee,
            pour_premiere_annee=pour_premiere_annee,
        )
        return [cls._build_dto(email_fonction=email_fonction) for email_fonction in emails_fonctions]

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
