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
from admission.ddd.doctorat.domain.model._formation import FormationIdentity
from admission.ddd.doctorat.domain.model.doctorat import DoctoratIdentity, Doctorat
from admission.ddd.doctorat.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.admission.projet_doctoral.preparation.domain.model.proposition import Proposition
from osis_common.ddd import interface


class DoctoratService(interface.DomainService):
    @classmethod
    def initier(cls, entity_id: 'DoctoratIdentity', proposition: 'Proposition') -> Doctorat:
        return Doctorat(
            entity_id=entity_id,
            formation_id=FormationIdentity(sigle=proposition.sigle_formation, annee=proposition.annee),
            matricule_doctorant=proposition.matricule_candidat,
            reference=proposition.reference or '',
            statut=ChoixStatutDoctorat.ADMITTED,
        )
