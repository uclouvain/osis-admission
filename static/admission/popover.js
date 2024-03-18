/*
 *
 * OSIS stands for Open Student Information System. It's an application
 * designed to manage the core business of higher education institutions,
 * such as universities, faculties, institutes and professional schools.
 * The core business involves the administration of students, teachers,
 * courses, programs and so on.
 *
 * Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

function initializePopover(configuration) {
  $(function () {
    $('body').popover(Object.assign({
      selector: '.popover-buttons',
      html: 'true',
      placement: 'auto top',
      toggle: 'popover',
      trigger: 'focus',
    }, configuration));

    $('body').on('mousedown', '.popover', function(e) {
      e.preventDefault();
      return false;
    });
  });
}
function initializeLazyPopover(configuration) {
  /**
   * Display popovers whose content is loaded asynchronously. The 'data-lazy-popover-url' attribute must be set on
   * the element and must point to the URL of the content to be loaded.
   */
  $(function () {
    $('body').on('click', '[data-lazy-popover-url]', function(e) {
      const dataset = $(this)[0].dataset;

      if (dataset.computedPopover === '1') return;

      $.get(dataset.lazyPopoverUrl, (data) => {
        $(this).popover(Object.assign({
          content: data,
          html: 'true',
          placement: 'auto',
          toggle: 'popover',
          trigger: 'focus',
          title: $(this)[0].dataset.title || '',
        }, configuration));

        $(this).popover('show');

        dataset.computedPopover = '1';
      });
    });
  });
}
