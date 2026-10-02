'use strict';
{
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    function showCmsLoader() {
        try {
            window.top.CMS.API.Toolbar.showLoader();
            return;
        } catch (err) {
            // Page tree is often in a sideframe; fall back to the current window.
        }
        try {
            window.CMS.API.Toolbar.showLoader();
        } catch (err) {
            // Not in the CMS admin chrome (e.g. plain Django admin).
        }
    }

    ready(function() {
        const form = document.querySelector('form.cms-port-page-action-confirm');
        if (!form) {
            return;
        }

        form.addEventListener('submit', function() {
            form.classList.add('is-busy');

            const submit = form.querySelector('[type="submit"]');
            if (submit) {
                submit.disabled = true;
                submit.setAttribute('aria-disabled', 'true');
            }

            const progress = document.getElementById('cms-port-page-action-progress');
            if (progress) {
                progress.hidden = false;
            }

            showCmsLoader();
        });
    });
}
