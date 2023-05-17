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
import uuid
from typing import List

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.domain.model.proposition import PropositionIdentity
from admission.ddd.admission.enums.emplacement_document import (
    TypeEmplacementDocument,
    IDENTIFIANT_BASE_EMPLACEMENT_DOCUMENT_LIBRE_PAR_TYPE,
)
from osis_common.ddd import interface


class EmplacementDocumentIdentityBuilder(interface.EntityIdentityBuilder):
    @classmethod
    def build_libre(
        cls,
        type_emplacement: str,
        uuid_proposition: str,
    ) -> EmplacementDocumentIdentity:
        """
        Constructeur de l'identifiant de l'emplacement d'un document libre :
        - LIBRE_CANDIDAT.[UUID] pour un document libre à destination du candidat.
        - LIBRE_GESTIONNAIRE.[UUID] pour un document libre à destination des gestionnaires uniquement.
        - SYSTEME.[NOM_DOMAINE_DOCUMENT] pour un document généré par le système.
        :param type_emplacement: type de l'emplacement de document
        :param uuid_proposition: uuid de la proposition
        :return: l'identifiant de l'emplacement
        """
        return EmplacementDocumentIdentity(
            identifiant=f'{IDENTIFIANT_BASE_EMPLACEMENT_DOCUMENT_LIBRE_PAR_TYPE[type_emplacement]}.{uuid.uuid4()}',
            proposition_id=PropositionIdentity(uuid=uuid_proposition),
        )

    @classmethod
    def build_non_libre(
        cls,
        identifiant_emplacement: str,
        uuid_proposition: str,
    ) -> EmplacementDocumentIdentity:
        """
        Constructeur de l'identifiant de l'emplacement d'un document non libre.
        :param identifiant_emplacement: identifiant de l'emplacement de document
        :param uuid_proposition: uuid de la proposition
        :return: l'identifiant de l'emplacement
        """
        return EmplacementDocumentIdentity(
            identifiant=identifiant_emplacement,
            proposition_id=PropositionIdentity(uuid=uuid_proposition),
        )

    @classmethod
    def build_list(
        cls,
        identifiants_emplacements: List[str],
        uuid_proposition: str,
    ) -> List[EmplacementDocumentIdentity]:
        return [
            EmplacementDocumentIdentity(
                identifiant=identifiant_emplacement,
                proposition_id=PropositionIdentity(uuid=uuid_proposition),
            )
            for identifiant_emplacement in identifiants_emplacements
        ]
