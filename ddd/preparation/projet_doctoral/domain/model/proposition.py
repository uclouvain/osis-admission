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
import uuid
from typing import List, Optional, Union

import attr

from admission.ddd.preparation.projet_doctoral.domain.model._detail_projet import (
    ChoixLangueRedactionThese,
    DetailProjet,
)
from admission.ddd.preparation.projet_doctoral.domain.model._enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixStatutProposition,
    ChoixTypeAdmission,
)
from admission.ddd.preparation.projet_doctoral.domain.model._experience_precedente_recherche import (
    ChoixDoctoratDejaRealise,
    ExperiencePrecedenteRecherche,
    aucune_experience_precedente_recherche,
)
from admission.ddd.preparation.projet_doctoral.domain.model._financement import (
    ChoixTypeFinancement,
    Financement,
    financement_non_rempli,
)
from admission.ddd.preparation.projet_doctoral.domain.model._institut import InstitutIdentity
from admission.ddd.preparation.projet_doctoral.domain.model.doctorat import DoctoratIdentity
from admission.ddd.preparation.projet_doctoral.domain.service.i_profil_candidat import IProfilCandidatTranslator
from admission.ddd.preparation.projet_doctoral.domain.validator.validator_by_business_action import (
    CompletionPropositionValidatorList,
    ProjetDoctoralValidatorList,
    SoumettrePropositionValidatorList,
)
from osis_common.ddd import interface


@attr.s(frozen=True, slots=True)
class PropositionIdentity(interface.EntityIdentity):
    uuid = attr.ib(type=str)


@attr.s(slots=True, hash=False, eq=False)
class Proposition(interface.RootEntity):
    entity_id = attr.ib(type=PropositionIdentity)
    type_admission = attr.ib(type=ChoixTypeAdmission)
    doctorat_id = attr.ib(type=DoctoratIdentity)
    matricule_candidat = attr.ib(type=str)
    projet = attr.ib(type=DetailProjet)
    reference = attr.ib(type=Optional[str], default=None)
    justification = attr.ib(type=Optional[str], default='')
    statut = attr.ib(type=ChoixStatutProposition, default=ChoixStatutProposition.IN_PROGRESS)
    commission_proximite = attr.ib(
        type=Optional[Union[ChoixCommissionProximiteCDEouCLSM, ChoixCommissionProximiteCDSS]], default=None
    )
    financement = attr.ib(type=Financement, default=financement_non_rempli)
    experience_precedente_recherche = attr.ib(
        type=ExperiencePrecedenteRecherche,
        default=aucune_experience_precedente_recherche,
    )
    creee_le = attr.ib(type=Optional[datetime.datetime], default=None)

    @property
    def sigle_formation(self):
        return self.doctorat_id.sigle

    @property
    def annee(self):
        return self.doctorat_id.annee

    valeur_reference_base = 300000

    @property
    def est_verrouillee_pour_signature(self) -> bool:
        return self.statut == ChoixStatutProposition.SIGNING_IN_PROGRESS

    def est_en_cours(self):
        return self.statut == ChoixStatutProposition.IN_PROGRESS

    def completer(
            self,
            type_admission: str,
            justification: Optional[str],
            commission_proximite: Optional[str],
            type_financement: Optional[str],
            type_contrat_travail: Optional[str],
            eft: Optional[int],
            bourse_recherche: Optional[str],
            duree_prevue: Optional[int],
            temps_consacre: Optional[int],
            langue_redaction_these: str,
            institut_these: Optional[str],
            lieu_these: Optional[str],
            autre_lieu_these: Optional[str],
            titre: Optional[str],
            resume: Optional[str],
            doctorat_deja_realise: str,
            institution: Optional[str],
            date_soutenance: Optional[datetime.date],
            raison_non_soutenue: Optional[str],
            documents: List[str] = None,
            graphe_gantt: List[str] = None,
            proposition_programme_doctoral: List[str] = None,
            projet_formation_complementaire: List[str] = None,
            lettres_recommandation: List[str] = None,
    ) -> None:
        CompletionPropositionValidatorList(
            type_admission=type_admission,
            type_financement=type_financement,
            justification=justification,
            type_contrat_travail=type_contrat_travail,
            doctorat_deja_realise=doctorat_deja_realise,
            institution=institution,
        ).validate()
        self._completer_proposition(type_admission, justification, commission_proximite)
        self._completer_financement(
            type=type_financement,
            type_contrat_travail=type_contrat_travail,
            eft=eft,
            bourse_recherche=bourse_recherche,
            duree_prevue=duree_prevue,
            temps_consacre=temps_consacre,
        )
        self._completer_projet(
            titre=titre,
            resume=resume,
            langue_redaction_these=langue_redaction_these,
            institut_these=institut_these,
            lieu_these=lieu_these,
            autre_lieu_these=autre_lieu_these,
            documents=documents,
            graphe_gantt=graphe_gantt,
            proposition_programme_doctoral=proposition_programme_doctoral,
            projet_formation_complementaire=projet_formation_complementaire,
            lettres_recommandation=lettres_recommandation,
        )
        self._completer_experience_precedente(
            doctorat_deja_realise=doctorat_deja_realise,
            institution=institution,
            date_soutenance=date_soutenance,
            raison_non_soutenue=raison_non_soutenue,
        )

    def _completer_proposition(
            self,
            type_admission: str,
            justification: Optional[str],
            commission_proximite: Optional[str],
    ):
        self.type_admission = ChoixTypeAdmission[type_admission]
        self.justification = justification or ''
        self.commission_proximite = None
        if commission_proximite and commission_proximite in ChoixCommissionProximiteCDEouCLSM.get_names():
            self.commission_proximite = ChoixCommissionProximiteCDEouCLSM[commission_proximite]
        elif commission_proximite and commission_proximite in ChoixCommissionProximiteCDSS.get_names():
            self.commission_proximite = ChoixCommissionProximiteCDSS[commission_proximite]

    def _completer_financement(
            self,
            type: Optional[str],
            type_contrat_travail: Optional[str],
            eft: Optional[int],
            bourse_recherche: Optional[str],
            duree_prevue: Optional[int],
            temps_consacre: Optional[int],
    ):
        if type:
            self.financement = Financement(
                type=ChoixTypeFinancement[type],
                type_contrat_travail=type_contrat_travail or '',
                eft=eft,
                bourse_recherche=bourse_recherche or '',
                duree_prevue=duree_prevue,
                temps_consacre=temps_consacre,
            )
        else:
            self.financement = financement_non_rempli

    def _completer_projet(
            self,
            titre: Optional[str],
            resume: Optional[str],
            langue_redaction_these: str,
            institut_these: Optional[str],
            lieu_these: Optional[str],
            autre_lieu_these: Optional[str],
            documents: List[str] = None,
            graphe_gantt: List[str] = None,
            proposition_programme_doctoral: List[str] = None,
            projet_formation_complementaire: List[str] = None,
            lettres_recommandation: List[str] = None,
    ):
        self.projet = DetailProjet(
            titre=titre or '',
            resume=resume or '',
            langue_redaction_these=(ChoixLangueRedactionThese[langue_redaction_these]
                                    if langue_redaction_these else ChoixLangueRedactionThese.UNDECIDED),
            institut_these=InstitutIdentity(uuid.UUID(institut_these)) if institut_these else None,
            lieu_these=lieu_these or '',
            autre_lieu_these=autre_lieu_these or '',
            documents=documents or [],
            graphe_gantt=graphe_gantt or [],
            proposition_programme_doctoral=proposition_programme_doctoral or [],
            projet_formation_complementaire=projet_formation_complementaire or [],
            lettres_recommandation=lettres_recommandation or [],
        )

    def _completer_experience_precedente(
            self,
            doctorat_deja_realise: str,
            institution: Optional[str],
            date_soutenance: Optional[datetime.date],
            raison_non_soutenue: Optional[str],
    ):
        if doctorat_deja_realise == ChoixDoctoratDejaRealise.NO.name:
            self.experience_precedente_recherche = aucune_experience_precedente_recherche
        else:
            self.experience_precedente_recherche = ExperiencePrecedenteRecherche(
                doctorat_deja_realise=ChoixDoctoratDejaRealise[doctorat_deja_realise],
                institution=institution or '',
                date_soutenance=date_soutenance,
                raison_non_soutenue=raison_non_soutenue or '',
            )

    def verifier(self):
        """Vérification complète de la proposition"""
        SoumettrePropositionValidatorList(proposition=self).validate()

    def verrouiller_proposition_pour_signature(self):
        self.statut = ChoixStatutProposition.SIGNING_IN_PROGRESS

    def verifier_projet_doctoral(self):
        """Vérification de la validité du projet doctoral avant demande des signatures"""
        ProjetDoctoralValidatorList(self.type_admission, self.projet, self.financement).validate()

    def finaliser(self):
        self.statut = ChoixStatutProposition.SUBMITTED

    def supprimer(self):
        self.statut = ChoixStatutProposition.CANCELLED
