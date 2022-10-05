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
from admission.ddd.parcours_doctoral.formation.domain.model.activite import Activite
from admission.ddd.parcours_doctoral.formation.domain.model.enums import CategorieActivite, StatutActivite
from admission.ddd.parcours_doctoral.formation.repository.i_activite import IActiviteRepository
from osis_common.ddd import interface


class RefuserActivite(interface.DomainService):
    @classmethod
    def refuser_activite(
        cls,
        activite: Activite,
        activite_repository: IActiviteRepository,
        avec_modification: bool,
        remarque: str,
    ) -> None:
        activite.refuser(avec_modification, remarque)
        activite_repository.save(activite)

        # Refuser toutes les sous-activités
        if activite.categorie in [CategorieActivite.CONFERENCE, CategorieActivite.RESIDENCY, CategorieActivite.SEMINAR]:
            sous_activites = activite_repository.search(parent_id=activite.entity_id)
            for sous_activite in sous_activites:
                sous_activite.statut = StatutActivite.REFUSEE
                activite_repository.save(sous_activite)
