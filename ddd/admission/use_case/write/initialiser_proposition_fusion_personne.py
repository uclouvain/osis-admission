# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.admission.commands import InitialiserPropositionFusionPersonneCommand
from admission.ddd.admission.domain.model.proposition_fusion_personne import PropositionFusionPersonneIdentity
from admission.ddd.admission.repository.i_proposition_fusion_personne import IPropositionPersonneFusionRepository


def initialiser_proposition_fusion_personne(
    cmd: 'InitialiserPropositionFusionPersonneCommand',
    proposition_fusion_personne_repository: 'IPropositionPersonneFusionRepository',
) -> PropositionFusionPersonneIdentity:
   return proposition_fusion_personne_repository.initialiser(
      global_id=cmd.original_global_id,
      nom=cmd.nom,
      prenom=cmd.prenom,
      autres_prenoms=cmd.autres_prenoms,
      date_naissance=cmd.date_naissance,
      lieu_naissance=cmd.lieu_naissance,
      email=cmd.email,
      genre=cmd.genre,
      etat_civil=cmd.etat_civil,
      nationalite=cmd.nationalite,
      numero_national=cmd.numero_national,
      numero_carte_id=cmd.numero_carte_id,
      numero_passeport=cmd.numero_passeport,
      dernier_noma_connu=cmd.dernier_noma_connu,
   )