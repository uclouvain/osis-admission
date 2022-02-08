##############################################################################
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
##############################################################################
import datetime
from typing import List, Optional

import attr

from admission.ddd.preparation.projet_doctoral.domain.model._detail_projet import ChoixLangueRedactionThese
from admission.ddd.preparation.projet_doctoral.domain.model._experience_precedente_recherche import (
    ChoixDoctoratDejaRealise,
)
from osis_common.ddd import interface

UUID = str


@attr.s(frozen=True, slots=True)
class InitierPropositionCommand(interface.CommandRequest):
    type_admission = attr.ib(type=str)
    sigle_formation = attr.ib(type=str)
    annee_formation = attr.ib(type=int)
    matricule_candidat = attr.ib(type=str)
    justification = attr.ib(type=Optional[str], default='')
    commission_proximite = attr.ib(type=Optional[str], default='')
    type_financement = attr.ib(type=Optional[str], default='')
    type_contrat_travail = attr.ib(type=Optional[str], default='')
    eft = attr.ib(type=Optional[int], default=None)
    bourse_recherche = attr.ib(type=Optional[str], default='')
    duree_prevue = attr.ib(type=Optional[int], default=None)
    temps_consacre = attr.ib(type=Optional[int], default=None)
    titre_projet = attr.ib(type=Optional[str], default='')
    resume_projet = attr.ib(type=Optional[str], default='')
    institut_these = attr.ib(type=Optional[str], default='')
    lieu_these = attr.ib(type=Optional[str], default='')
    autre_lieu_these = attr.ib(type=Optional[str], default='')
    documents_projet = attr.ib(type=List[str], factory=list)
    graphe_gantt = attr.ib(type=List[str], factory=list)
    proposition_programme_doctoral = attr.ib(type=List[str], factory=list)
    projet_formation_complementaire = attr.ib(type=List[str], factory=list)
    lettres_recommandation = attr.ib(type=List[str], factory=list)
    langue_redaction_these = attr.ib(type=str, default=ChoixLangueRedactionThese.UNDECIDED.name)
    doctorat_deja_realise = attr.ib(type=str, default=ChoixDoctoratDejaRealise.NO.name)
    institution = attr.ib(type=Optional[str], default='')
    date_soutenance = attr.ib(type=Optional[datetime.date], default=None)
    raison_non_soutenue = attr.ib(type=Optional[str], default='')


@attr.s(frozen=True, slots=True)
class CompleterPropositionCommand(interface.CommandRequest):
    uuid = attr.ib(type=str)
    type_admission = attr.ib(type=str)
    justification = attr.ib(type=Optional[str], default='')
    commission_proximite = attr.ib(type=Optional[str], default='')
    type_financement = attr.ib(type=Optional[str], default='')
    type_contrat_travail = attr.ib(type=Optional[str], default='')
    eft = attr.ib(type=Optional[int], default=None)
    bourse_recherche = attr.ib(type=Optional[str], default='')
    duree_prevue = attr.ib(type=Optional[int], default=None)
    temps_consacre = attr.ib(type=Optional[int], default=None)
    titre_projet = attr.ib(type=Optional[str], default='')
    resume_projet = attr.ib(type=Optional[str], default='')
    documents_projet = attr.ib(type=List[str], factory=list)
    graphe_gantt = attr.ib(type=List[str], factory=list)
    proposition_programme_doctoral = attr.ib(type=List[str], factory=list)
    projet_formation_complementaire = attr.ib(type=List[str], factory=list)
    lettres_recommandation = attr.ib(type=List[str], factory=list)
    langue_redaction_these = attr.ib(type=str, default=ChoixLangueRedactionThese.UNDECIDED.name)
    institut_these = attr.ib(type=Optional[str], default='')
    lieu_these = attr.ib(type=Optional[str], default='')
    autre_lieu_these = attr.ib(type=Optional[str], default='')
    doctorat_deja_realise = attr.ib(type=str, default=ChoixDoctoratDejaRealise.NO.name)
    institution = attr.ib(type=Optional[str], default='')
    date_soutenance = attr.ib(type=Optional[datetime.date], default=None)
    raison_non_soutenue = attr.ib(type=Optional[str], default='')


@attr.s(frozen=True, slots=True)
class SearchDoctoratCommand(interface.CommandRequest):
    sigle_secteur_entite_gestion = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class IdentifierPromoteurCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)
    matricule = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class IdentifierMembreCACommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)
    matricule = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class DemanderSignaturesCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class VerifierPropositionCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class SupprimerPromoteurCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)
    matricule = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class SupprimerMembreCACommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)
    matricule = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class ApprouverPropositionCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)
    matricule = attr.ib(type=str)
    commentaire_interne = attr.ib(type=Optional[str], default='')
    commentaire_externe = attr.ib(type=Optional[str], default='')


@attr.s(frozen=True, slots=True)
class RefuserPropositionCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)
    matricule = attr.ib(type=str)
    motif_refus = attr.ib(type=str)
    commentaire_interne = attr.ib(type=Optional[str], default='')
    commentaire_externe = attr.ib(type=Optional[str], default='')


@attr.s(frozen=True, slots=True)
class SoumettrePropositionCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class DefinirCotutelleCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)
    motivation = attr.ib(type=Optional[str], default='')
    institution = attr.ib(type=Optional[str], default='')
    demande_ouverture = attr.ib(type=List[str], factory=list)
    convention = attr.ib(type=List[str], factory=list)
    autres_documents = attr.ib(type=List[str], factory=list)


@attr.s(frozen=True, slots=True)
class SearchPropositionsCandidatCommand(interface.CommandRequest):
    matricule_candidat = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class SearchPropositionsSuperviseesCommand(interface.CommandRequest):
    matricule_membre = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class GetPropositionCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class GetGroupeDeSupervisionCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class GetCotutelleCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class SupprimerPropositionCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)


@attr.s(frozen=True, slots=True)
class ApprouverPropositionParPdfCommand(interface.CommandRequest):
    uuid_proposition = attr.ib(type=str)
    matricule = attr.ib(type=str)
    pdf = attr.ib(type=str)
