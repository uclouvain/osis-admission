# ##############################################################################
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
# ##############################################################################
from django.utils.translation import gettext_lazy as _, pgettext_lazy, ngettext_lazy

from base.models.utils.utils import ChoiceEnum


class TypeEmplacementDocument(ChoiceEnum):
    # Documents réclamables
    NON_LIBRE = _('Not free')
    LIBRE_RECLAMABLE_SIC = _('Free and requestable by SIC')
    LIBRE_RECLAMABLE_FAC = _('Free and requestable by FAC')
    # Documents non réclamables
    LIBRE_INTERNE_SIC = _('Free and uploaded by SIC for the managers')
    LIBRE_INTERNE_FAC = _('Free and uploaded by FAC for the managers')
    SYSTEME = _('Generated by the system')


EMPLACEMENTS_DOCUMENTS_INTERNES = {
    TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
    TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
    TypeEmplacementDocument.SYSTEME.name,
}

EMPLACEMENTS_DOCUMENTS_LIBRES_NON_RECLAMABLES = {
    TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
    TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
}

EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES = {
    TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
    TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
}

EMPLACEMENTS_DOCUMENTS_RECLAMABLES = EMPLACEMENTS_DOCUMENTS_LIBRES_RECLAMABLES | {
    TypeEmplacementDocument.NON_LIBRE.name
}

EMPLACEMENTS_FAC = {
    TypeEmplacementDocument.LIBRE_INTERNE_FAC.name,
    TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name,
}

EMPLACEMENTS_SIC = {
    TypeEmplacementDocument.NON_LIBRE.name,
    TypeEmplacementDocument.LIBRE_INTERNE_SIC.name,
    TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name,
}


class StatutEmplacementDocument(ChoiceEnum):
    A_RECLAMER = _('To be requested')
    RECLAME = pgettext_lazy('document', 'Requested')
    NON_ANALYSE = _('Not analyzed')
    VALIDE = _('Validated')
    COMPLETE_APRES_RECLAMATION = _('Completed after the request')


class StatutReclamationEmplacementDocument(ChoiceEnum):
    IMMEDIATEMENT = _('Immediately')
    ULTERIEUREMENT_BLOQUANT = _('Later > blocking')
    ULTERIEUREMENT_NON_BLOQUANT = _('Later > non-blocking')


class OngletsDemande(ChoiceEnum):
    IDENTIFICATION = _('Identification')
    COORDONNEES = _('Coordinates')
    CHOIX_FORMATION = _('Course choice')
    ETUDES_SECONDAIRES = _('Secondary studies')
    CURRICULUM = _('Curriculum')
    LANGUES = _('Knowledge of languages')
    COMPTABILITE = _('Accounting')
    PROJET = pgettext_lazy('tab', 'Research project')
    COTUTELLE = _('Cotutelle')
    SUPERVISION = _('Supervision')
    INFORMATIONS_ADDITIONNELLES = _('Additional information')
    CONFIRMATION = pgettext_lazy('tab', 'Finalization')
    SUITE_AUTORISATION = _('Following authorization')


class IdentifiantBaseEmplacementDocument(ChoiceEnum):
    QUESTION_SPECIFIQUE = _('Specific question')
    LIBRE_CANDIDAT = _('Additional documents')  # Additional documents that can be requested from the candidate
    LIBRE_GESTIONNAIRE = _('Additional documents uploaded by a manager')
    SYSTEME = _('System')


IDENTIFIANT_BASE_EMPLACEMENT_DOCUMENT_LIBRE_PAR_TYPE = {
    TypeEmplacementDocument.LIBRE_INTERNE_SIC.name: IdentifiantBaseEmplacementDocument.LIBRE_GESTIONNAIRE.name,
    TypeEmplacementDocument.LIBRE_INTERNE_FAC.name: IdentifiantBaseEmplacementDocument.LIBRE_GESTIONNAIRE.name,
    TypeEmplacementDocument.LIBRE_RECLAMABLE_FAC.name: IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name,
    TypeEmplacementDocument.LIBRE_RECLAMABLE_SIC.name: IdentifiantBaseEmplacementDocument.LIBRE_CANDIDAT.name,
}


DocumentsIdentification = {
    'PHOTO_IDENTITE': _('Identification photo'),
    'CARTE_IDENTITE': _('Identity card (both sides)'),
    'PASSEPORT': _('Passport'),
}


DocumentsSystemeFAC = {
    'ATTESTATION_ACCORD_FACULTAIRE': _('Approval certificate of faculty'),
    'ATTESTATION_REFUS_FACULTAIRE': _('Refusal certificate of faculty'),
}


DocumentsSystemeSIC = {
    'ATTESTATION_ACCORD_SIC': _('Enrolment authorisation'),
    'ATTESTATION_ACCORD_ANNEXE_SIC': _('Annex 1 visa form'),
    'ATTESTATION_REFUS_SIC': _('Refusal certificate of SIC'),
}


DocumentsSysteme = {
    'DOSSIER_ANALYSE': _('Analysis folder'),
    **DocumentsSystemeFAC,
    **DocumentsSystemeSIC,
}


DocumentsEtudesSecondaires = {
    'DIPLOME_BELGE_DIPLOME': _('Secondary school diploma'),
    'DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_UE': _(
        "Copy of both sides of the definitive equivalency decision (accompanied, "
        "where applicable, by the DAES or undergraduate exam, in the case of restrictive equivalency)"
    ),
    'DIPLOME_ETRANGER_PREUVE_DECISION_EQUIVALENCE': _('Proof of equivalency request'),
    'DIPLOME_ETRANGER_DECISION_FINAL_EQUIVALENCE_HORS_UE': _(
        "Copy of both sides of the definitive equivalency decision by the Ministry of the French-speaking Community "
        "of Belgium (possibly accompanied by the DAES or the undergraduate studies exam, if your equivalency does "
        "not confer eligibility for the desired programme)"
    ),
    'DIPLOME_ETRANGER_DIPLOME': _('Secondary school diploma'),
    'DIPLOME_ETRANGER_TRADUCTION_DIPLOME': _('A translation of your secondary school diploma by a sworn translator'),
    'DIPLOME_ETRANGER_RELEVE_NOTES': _('A transcript for your last year of secondary school'),
    'DIPLOME_ETRANGER_TRADUCTION_RELEVE_NOTES': _(
        'A translation of your official transcript of marks for your final year of secondary school by a '
        'sworn translator'
    ),
    'ALTERNATIVE_SECONDAIRES_EXAMEN_ADMISSION_PREMIER_CYCLE': _(
        "Certificate of passing the bachelor's course entrance exam"
    ),
}


DocumentsConnaissancesLangues = {
    'CERTIFICAT_CONNAISSANCE_LANGUE': _('Certificate of language knowledge'),
}


DocumentsCurriculum = {
    'DIPLOME_EQUIVALENCE': _(
        "Copy of equivalency decision issued by the French Community of Belgium making your bachelor's diploma (bac+5) "
        "equivalent to the academic rank of a corresponding master's degree."
    ),
    'CURRICULUM': _('Detailed curriculum vitae, dated and signed'),
    'RELEVE_NOTES': _('Transcript'),
    'TRADUCTION_RELEVE_NOTES': _('Transcript translation'),
    'RELEVE_NOTES_ANNUEL': _('Transcript'),
    'TRADUCTION_RELEVE_NOTES_ANNUEL': _('Transcript translation'),
    'RESUME_MEMOIRE': _('Dissertation summary'),
    'DIPLOME': _('Diploma'),
    'TRADUCTION_DIPLOME': _('Diploma translation'),
    'CERTIFICAT_EXPERIENCE': _('Certificate of experience'),
}


DocumentsQuestionsSpecifiques = {
    'COPIE_TITRE_SEJOUR': _(
        'Copy of residence permit covering entire course, including assessment test (except for online courses).'
    ),
    'ATTESTATION_INSCRIPTION_REGULIERE': _('Certificate of regular enrolment'),
    'FORMULAIRE_MODIFICATION_INSCRIPTION': _('Change of enrolment form'),
    'ADDITIONAL_DOCUMENTS': _(
        'You can add any document you feel is relevant to your application '
        '(supporting documents, proof of language level, etc.).'
    ),
}


# The keys corresponding to the attributes (in uppercase) of the following domain models:
# admission.ddd.admission.formation_generale.domain.model._comptabilite.Comptabilite
# admission.ddd.admission.doctorat.preparation.domain.model._comptabilite.Comptabilite
DocumentsAssimilation = {
    'CARTE_RESIDENT_LONGUE_DUREE': _('Copy of both sides of EC long-term resident card (D or L Card)'),
    'CARTE_CIRE_SEJOUR_ILLIMITE_ETRANGER': _(
        "Copy of both sides of Certificate of Registration in the Foreigners Registry (CIRE), "
        "unlimited stay (B Card), or of Foreign National's Card, unlimited stay (C or K Card)"
    ),
    'CARTE_SEJOUR_MEMBRE_UE': _(
        'Copy of both sides of residence permit for a family member of a European Union citizen (F Card)'
    ),
    'CARTE_SEJOUR_PERMANENT_MEMBRE_UE': _(
        'Copy of both sides of permanent residence card of a family member of a European Union citizen (F+ Card)'
    ),
    'CARTE_A_B_REFUGIE': _('Copy of both sides of A or B Card (with "refugee" on card back)'),
    'ANNEXE_25_26_REFUGIES_APATRIDES': _(
        'Copy of Annex 25 or 26 completed by the Office of the Commissioner General for Refugees and Stateless Persons'
    ),
    'PREUVE_STATUT_APATRIDE': _(
        'Copy of official document from the local authority or Foreign Nationals Office proving stateless status'
    ),
    'CARTE_A_B': _('Copy of both sides of A or B Card'),
    'DECISION_PROTECTION_SUBSIDIAIRE': _('Copy of Foreign Nationals Office decision granting subsidiary protection'),
    'DECISION_PROTECTION_TEMPORAIRE': _('Copy of Foreign Nationals Office decision granting temporary protection'),
    'CARTE_A': _('Copy of both sides of A Card'),
    'TITRE_SEJOUR_3_MOIS_PROFESSIONEL': _('Copy of both sides of residence permit valid for more than 3 months'),
    'FICHES_REMUNERATION': _('Copy of 6 payslips issued in the 12 months preceding application'),
    'TITRE_SEJOUR_3_MOIS_REMPLACEMENT': _('Copy of both sides of residence permit valid for more than 3 months'),
    'PREUVE_ALLOCATIONS_CHOMAGE_PENSION_INDEMNITE': _(
        'Proof of receipt of unemployment benefit, pension or compensation from the mutual insurance company'
    ),
    'ATTESTATION_CPAS': _('Recent CPAS certificate of coverage'),
    'COMPOSITION_MENAGE_ACTE_NAISSANCE': _('Household composition, or copy of your birth certificate'),
    'ACTE_TUTELLE': _('Copy of guardianship appointment legalised by Belgian authorities'),
    'COMPOSITION_MENAGE_ACTE_MARIAGE': _(
        'Household composition or marriage certificate authenticated by the Belgian authorities'
    ),
    'ATTESTATION_COHABITATION_LEGALE': _('Certificate of legal cohabitation'),
    'CARTE_IDENTITE_PARENT': _('Copy of both sides of identity card of %(person_concerned)s'),
    'TITRE_SEJOUR_LONGUE_DUREE_PARENT': _(
        'Copy of both sides of long-term residence permit in Belgium of %(person_concerned)s (B, C, D, F, F+, '
        'K, L or M Card)'
    ),
    'ANNEXE_25_26_REFUGIES_APATRIDES_DECISION_PROTECTION_PARENT': _(
        'Copy of Annex 25 or 26 or A/B Card indicating refugee status or copy of Foreign Nationals '
        'Office decision confirming temporary/subsidiary protection of %(person_concerned)s or copy of official '
        'Foreign Nationals Office or municipality document proving the stateless status of %(person_concerned)s'
    ),
    'TITRE_SEJOUR_3_MOIS_PARENT': _(
        'Copy of both sides of residence permit valid for more than 3 months of %(person_concerned)s'
    ),
    'FICHES_REMUNERATION_PARENT': _(
        'Copy of 6 payslips issued in the 12 months preceding application or proof of receipt of unemployment benefit, '
        'pension or allowance from a mutual insurance company of %(person_concerned)s'
    ),
    'ATTESTATION_CPAS_PARENT': _('Recent CPAS certificate of coverage for %(person_concerned)s'),
    'DECISION_BOURSE_CFWB': _('Copy of decision to grant CFWB scholarship'),
    'ATTESTATION_BOURSIER': _(
        "Copy of holder's certificate of scholarship issued by the General Administration for Development Cooperation"
    ),
    'TITRE_IDENTITE_SEJOUR_LONGUE_DUREE_UE': _(
        'Copy of both sides of identity document proving long-term residence in a European Union member state'
    ),
    'TITRE_SEJOUR_BELGIQUE': _('Copy of both sides of residence permit in Belgium'),
}
DocumentsComptabilite = {
    'ATTESTATION_ABSENCE_DETTE_ETABLISSEMENT': ngettext_lazy(
        'Certificate stating no debts to the institution attended during the academic year '
        '%(academic_year)s: %(names)s.',
        'Certificates stating no debts to the institutions attended during the academic year '
        '%(academic_year)s: %(names)s.',
        'count',
    ),
    'ATTESTATION_ENFANT_PERSONNEL': _('Certificate for children of staff'),
    **DocumentsAssimilation,
}


DocumentsProjetRecherche = {
    'PREUVE_BOURSE': _('Proof of scholarship'),
    'DOCUMENTS_PROJET': _('PhD research project'),
    'PROPOSITION_PROGRAMME_DOCTORAL': _('PhD proposal'),
    'PROJET_FORMATION_COMPLEMENTAIRE': _('Complementary training proposition'),
    'GRAPHE_GANTT': _("Gantt chart"),
    'LETTRES_RECOMMANDATION': _("Letters of recommendation"),
}


DocumentsCotutelle = {
    'DEMANDE_OUVERTURE': _('Joint supervision request'),
    'CONVENTION': _('Joint supervision agreement'),
    'AUTRES_DOCUMENTS': _('Other documents relating to joint supervision'),
}


DocumentsSupervision = {
    'APPROBATION_PDF': _('Approbation by pdf'),
}

DocumentsSuiteAutorisation = {
    'VISA_ETUDES': _(
        'Copy of your student visa D (permission to stay longer than 90 days in Belgium) issued by the Belgian '
        'Embassy or Consulate.'
    ),
    'AUTORISATION_PDF_SIGNEE': _('The official French-language enrolment authorisation signed by you.'),
}


DOCUMENTS_A_NE_PAS_CONVERTIR_A_LA_SOUMISSION = {
    f'{OngletsDemande.IDENTIFICATION.name}.PHOTO_IDENTITE',
}
