##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict, List, Optional, Union
from uuid import UUID

import attr

from admission.ddd.admission.doctorat.preparation.dtos import CotutelleDTO
from admission.ddd.admission.dtos.bourse import BourseDTO
from admission.ddd.admission.dtos.profil_candidat import ProfilCandidatDTO
from osis_common.ddd import interface
from osis_profile import PLUS_5_ISO_CODES
from .doctorat import DoctoratDTO
from ..domain.model.enums import STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE


@attr.dataclass(slots=True)
class PropositionDTO(interface.DTO):
    uuid: str
    type_admission: str
    reference: str
    justification: Optional[str]
    doctorat: DoctoratDTO
    annee_calculee: Optional[int]
    type_demande: str
    pot_calcule: Optional[str]
    date_fin_pot: Optional[datetime.date]
    code_secteur_formation: str
    intitule_secteur_formation: str
    commission_proximite: Optional[str]
    type_financement: Optional[str]
    type_contrat_travail: Optional[str]
    eft: Optional[int]
    bourse_recherche: Optional[BourseDTO]
    autre_bourse_recherche: Optional[str]
    bourse_date_debut: Optional[datetime.date]
    bourse_date_fin: Optional[datetime.date]
    bourse_preuve: List[str]
    duree_prevue: Optional[int]
    temps_consacre: Optional[int]
    est_lie_fnrs_fria_fresh_csc: Optional[bool]
    commentaire_financement: Optional[str]
    titre_projet: Optional[str]
    resume_projet: Optional[str]
    documents_projet: List[str]
    graphe_gantt: List[str]
    proposition_programme_doctoral: List[str]
    projet_formation_complementaire: List[str]
    lettres_recommandation: List[str]
    langue_redaction_these: Optional[str]
    institut_these: Optional[UUID]
    nom_institut_these: str
    sigle_institut_these: str
    lieu_these: str
    projet_doctoral_deja_commence: Optional[bool]
    projet_doctoral_institution: Optional[str]
    projet_doctoral_date_debut: Optional[datetime.date]
    doctorat_deja_realise: str
    institution: Optional[str]
    domaine_these: str
    date_soutenance: Optional[datetime.date]
    raison_non_soutenue: Optional[str]
    statut: str
    fiche_archive_signatures_envoyees: List[str]
    matricule_candidat: str
    prenom_candidat: str
    nom_candidat: str
    nationalite_candidat: str
    langue_contact_candidat: str
    creee_le: datetime.datetime
    modifiee_le: datetime.datetime
    soumise_le: Optional[datetime.datetime]
    erreurs: List[Dict[str, str]]
    reponses_questions_specifiques: Dict[str, Union[str, List[str]]]
    curriculum: List[str]
    elements_confirmation: Dict[str, str]
    pdf_recapitulatif: List[str]
    documents_demandes: Dict
    documents_libres_fac_uclouvain: List[str]
    documents_libres_sic_uclouvain: List[str]

    @property
    def est_non_soumise(self):
        return self.statut in STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE


@attr.dataclass(frozen=True, slots=True)
class PropositionGestionnaireDTO(PropositionDTO):
    date_changement_statut: Optional[datetime.datetime]

    genre_candidat: str
    noma_candidat: str
    adresse_email_candidat: str
    nationalite_candidat_fr: str
    nationalite_candidat_en: str
    nationalite_candidat_code_iso: str
    nationalite_ue_candidat: Optional[bool]
    photo_identite_candidat: List[str]

    candidat_a_plusieurs_demandes: bool

    cotutelle: Optional[CotutelleDTO]

    profil_soumis_candidat: Optional[ProfilCandidatDTO]

    @property
    def candidat_a_nationalite_ue_5(self):
        return self.nationalite_ue_candidat is True or self.nationalite_candidat_code_iso in PLUS_5_ISO_CODES

    @property
    def candidat_a_nationalite_hors_ue_5(self):
        return self.nationalite_ue_candidat is False and self.nationalite_candidat_code_iso not in PLUS_5_ISO_CODES
