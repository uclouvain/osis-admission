# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from .determiner_annee_academique_et_pot_service import (
    determiner_annee_academique_et_pot,
)
from .lister_demandes_service import lister_demandes
from .lister_propositions_candidat_service import lister_propositions_candidat
from .rechercher_formations_service import rechercher_formations
from .recuperer_documents_proposition_service import recuperer_documents_proposition
from .recuperer_documents_reclames_proposition_service import (
    recuperer_documents_reclames_proposition,
)
from .recuperer_elements_confirmation_service import recuperer_elements_confirmation
from .recuperer_formation_service import recuperer_formation
from .recuperer_proposition_service import recuperer_proposition
from .recuperer_resume_et_emplacements_document_proposition_service import (
    recuperer_resume_et_emplacements_documents_proposition,
)
from .recuperer_resume_proposition_service import recuperer_resume_proposition
from .verifier_proposition_service import verifier_proposition
