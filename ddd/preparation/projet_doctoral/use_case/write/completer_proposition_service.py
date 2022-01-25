# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.ddd.preparation.projet_doctoral.builder.proposition_identity_builder import \
    PropositionIdentityBuilder
from admission.ddd.preparation.projet_doctoral.commands import CompleterPropositionCommand
from admission.ddd.preparation.projet_doctoral.domain.model._institut import InstitutIdentity
from admission.ddd.preparation.projet_doctoral.domain.model.proposition import PropositionIdentity
from admission.ddd.preparation.projet_doctoral.domain.service.commission_proximite import CommissionProximite
from admission.ddd.preparation.projet_doctoral.domain.service.i_doctorat import IDoctoratTranslator
from admission.ddd.preparation.projet_doctoral.repository.i_proposition import IPropositionRepository


def completer_proposition(
        cmd: 'CompleterPropositionCommand',
        proposition_repository: 'IPropositionRepository',
        doctorat_translator: 'IDoctoratTranslator',
) -> 'PropositionIdentity':
    # GIVEN
    entity_id = PropositionIdentityBuilder.build_from_uuid(cmd.uuid)
    proposition_candidat = proposition_repository.get(entity_id=entity_id)
    doctorat = doctorat_translator.get(proposition_candidat.sigle_formation, proposition_candidat.annee)
    CommissionProximite().verifier(doctorat, cmd.commission_proximite)

    # WHEN
    proposition_candidat.completer(
        type_admission=cmd.type_admission,
        justification=cmd.justification,
        commission_proximite=cmd.commission_proximite,
        type_financement=cmd.type_financement,
        type_contrat_travail=cmd.type_contrat_travail,
        eft=cmd.eft,
        bourse_recherche=cmd.bourse_recherche,
        duree_prevue=cmd.duree_prevue,
        temps_consacre=cmd.temps_consacre,
        titre=cmd.titre_projet,
        resume=cmd.resume_projet,
        langue_redaction_these=cmd.langue_redaction_these,
        institut_these=InstitutIdentity(cmd.institut_these) if cmd.institut_these else None,
        lieu_these=cmd.lieu_these,
        autre_lieu_these=cmd.autre_lieu_these,
        documents=cmd.documents_projet,
        graphe_gantt=cmd.graphe_gantt,
        proposition_programme_doctoral=cmd.proposition_programme_doctoral,
        projet_formation_complementaire=cmd.projet_formation_complementaire,
        lettres_recommandation=cmd.lettres_recommandation,
        doctorat_deja_realise=cmd.doctorat_deja_realise,
        institution=cmd.institution,
        date_soutenance=cmd.date_soutenance,
        raison_non_soutenue=cmd.raison_non_soutenue,
    )

    # THEN
    proposition_repository.save(proposition_candidat)

    return entity_id
