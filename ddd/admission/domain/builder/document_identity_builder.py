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

from admission.ddd.admission.domain.model.emplacement_document import EmplacementDocumentIdentity
from admission.ddd.admission.enums.emplacement_document import OngletsDemande, DocumentsInterOnglets
from osis_common.ddd import interface


class EmplacementDocumentIdentityBuilder(interface.EntityIdentityBuilder):
    @classmethod
    def build(
        cls,
        onglet_document: OngletsDemande,
        identifiant_document: str = '',
        token_document: str = '',
        identifiant_question_specifique: str = '',
    ) -> EmplacementDocumentIdentity:
        if identifiant_document:
            return EmplacementDocumentIdentity(identifiant=identifiant_document)

        if identifiant_question_specifique:
            return EmplacementDocumentIdentity(
                identifiant='{}.{}.{}'.format(
                    onglet_document.name,
                    DocumentsInterOnglets.QUESTION_SPECIFIQUE.name,
                    identifiant_question_specifique,
                ),
            )

        if token_document:
            return EmplacementDocumentIdentity(identifiant=f'{onglet_document.name}.{token_document}')
