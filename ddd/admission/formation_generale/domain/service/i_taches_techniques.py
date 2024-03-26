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
from abc import abstractmethod

from admission.ddd.admission.formation_generale.domain.model.proposition import Proposition
from admission.ddd.admission.formation_generale.domain.model.statut_checklist import StatutChecklist
from osis_common.ddd.interface import DomainService


class ITachesTechniques(DomainService):
    @classmethod
    @abstractmethod
    def annuler_paiement_initial_frais_dossier(
        cls,
        proposition: Proposition,
        statut_checklist_frais_dossier_avant_modification: StatutChecklist,
    ):
        """
        Exécute des tâches techniques lors de l'annulation du paiement des frais de dossier demandé par le système
        à la soumission de la demande. Ces tâches sont normalement exécutées de manière asynchrone lorsque
        l'utilisateur soumet sa demande et qu'il ne doit pas payer des frais de dossier ou qu'il paie les frais de
        dossier suite à la soumission de sa demande. Il s'agit des tâches de :
        - fusion et conversion de chaque document en un fichier PDF ;
        - génération du PDF récapitulatif de la demande à destination du candidat.
        :param proposition: Proposition concernée par l'annulation des frais de dossier.
        :param statut_checklist_frais_dossier_avant_modification: Statut de la checklist des frais de dossier avant
        modification par le gestionnaire.
        """
        raise NotImplementedError
