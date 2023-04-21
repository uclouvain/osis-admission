/*
 *
 * OSIS stands for Open Student Information System. It's an application
 * designed to manage the core business of higher education institutions,
 * such as universities, faculties, institutes and professional schools.
 * The core business involves the administration of students, teachers,
 * courses, programs and so on.
 *
 * Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * A copy of this license - GNU General Public License - is available
 * at the root of the source code of this program.  If not,
 * see http://www.gnu.org/licenses/.
 *
 */

/**
 * Write text to clipboard when the user clicks on a button (requires jquery + tooltip.js from bootstrap)
 * @param clipboardSelector
 * @param resetTitleAfter Reset the button title after a specific duration (in s)
 */
function writeTextToClipboard(clipboardSelector, resetTitleAfter=3) {
    // Each clipboard element must have a button and something having a 'copy-text' class from which the text is copied
    const initialTooltipText = gettext('Copy to clipboard');
    const tooltipTextOnSuccess = gettext('Copied!');
    const tooltipTextOnFailure = gettext('Impossible to copy');

    $(clipboardSelector).each(function() {
        const buttonComponent = $(this).find('button');

        buttonComponent.attr({
            'title': initialTooltipText,
            'data-toggle': 'tooltip',
            'data-trigger': 'hover',
        })

        buttonComponent.on('click', () => {
            // Copy text content to clipboard
            const textComponent = $(this).find('.copy-to-clipboard-text').get(0);
            navigator.clipboard.writeText(textComponent.textContent).then(() => {
                buttonComponent.attr('data-original-title', tooltipTextOnSuccess).tooltip('show');
                buttonComponent.attr('data-original-title', initialTooltipText);
            }, () => {
                buttonComponent.attr('data-original-title', tooltipTextOnFailure).tooltip('show');
                buttonComponent.attr('data-original-title', initialTooltipText);
            });
        });
    })
    $(clipboardSelector + ' button[data-toggle="tooltip"]').tooltip();
}
