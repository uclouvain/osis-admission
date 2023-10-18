# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

# Association between a read-only tab name (path name) and a permission
READ_ACTIONS_BY_TAB = {
    # Personal data
    'coordonnees': 'admission.view_admission_coordinates',
    'cotutelle': 'admission.view_admission_cotutelle',
    'person': 'admission.view_admission_person',
    # Training choice
    'training-choice': 'admission.view_admission_training_choice',
    # Previous experience
    'curriculum': 'admission.view_admission_curriculum',
    'education': 'admission.view_admission_secondary_studies',
    'languages': 'admission.view_admission_languages',
    # Project
    'project': 'admission.view_admission_project',
    'supervision': 'admission.view_admission_supervision',
    # Additional information
    'accounting': 'admission.view_admission_accounting',
    # Confirmation exam
    'confirmation': 'admission.view_admission_confirmation',
    'extension-request': 'admission.view_admission_confirmation',
    # History
    'history': 'admission.view_historyentry',
    'history-all': 'admission.view_historyentry',
    # Mails
    'send-mail': 'admission.send_message',
    # Training
    'training': 'admission.view_training',
    'doctoral-training': 'admission.view_doctoral_training',
    'complementary-training': 'admission.view_complementary_training',
    'course-enrollment': 'admission.view_course_enrollment',
    # Jury
    'jury-preparation': 'admission.view_admission_jury',
    'jury': 'admission.view_admission_jury',
    # Management
    'internal-note': 'admission.view_internalnote',
    'debug': 'admission.view_debug_info',
    'comments': 'admission.view_enrolment_application',
    'checklist': 'admission.view_checklist',
    # Documents
    'documents': 'admission.view_documents_management',
}

# Association between a write-only tab name (path name) and a permission
UPDATE_ACTIONS_BY_TAB = {
    # Personal data
    'coordonnees': 'admission.change_admission_coordinates',
    'cotutelle': 'admission.change_admission_cotutelle',
    'person': 'admission.change_admission_person',
    # Training choice
    'training-choice': 'admission.change_admission_training_choice',
    # Previous experience
    'curriculum': 'admission.change_admission_curriculum',
    'education': 'admission.change_admission_secondary_studies',
    'languages': 'admission.change_admission_languages',
    # Project
    'project': 'admission.change_admission_project',
    'supervision': 'admission.change_admission_supervision',
    # Additional information
    'accounting': 'admission.change_admission_accounting',
    # Confirmation exam
    'confirmation': 'admission.change_admission_confirmation',
    'extension-request': 'admission.change_admission_confirmation_extension',
    # Mails
    'send-mail': 'admission.send_message',
    # Training
    'training': '',
    'doctoral-training': '',
    'complementary-training': '',
    'course-enrollment': '',
    # Management
    'documents': 'admission.view_documents_management',
    # Jury
    'jury-preparation': 'admission.change_admission_jury',
    'jury': 'admission.change_admission_jury',
}
