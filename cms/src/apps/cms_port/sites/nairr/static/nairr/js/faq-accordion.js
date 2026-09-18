// Expand/collapse every <details> accordion item on the NAIRR FAQ page.
//
// TODO(core-worthy): generalize into a reusable Core-CMS/core-styles
// accordion component instead of a NAIRR-specific script.
(function () {
  function setAllOpen(open) {
    document.querySelectorAll('.nairr-faq details').forEach(function (details) {
      details.open = open;
    });
  }

  function copyUrl(anchor) {
    var url = window.location.origin + window.location.pathname + '#' + anchor;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url);
    }
  }

  function openFromHash() {
    var hash = window.location.hash.slice(1);
    if (!hash) {
      return;
    }
    var details = document.getElementById(hash);
    if (details && details.tagName === 'DETAILS') {
      details.open = true;
    }
  }

  document.addEventListener('DOMContentLoaded', openFromHash);
  window.addEventListener('hashchange', openFromHash);

  document.addEventListener('click', function (event) {
    var expandLink = event.target.closest('.nairr-faq-expand-all');
    if (expandLink) {
      event.preventDefault();
      setAllOpen(true);
      return;
    }

    var collapseLink = event.target.closest('.nairr-faq-collapse-all');
    if (collapseLink) {
      event.preventDefault();
      setAllOpen(false);
      return;
    }

    var copyButton = event.target.closest('.nairr-faq-copy-url');
    if (copyButton) {
      event.preventDefault();
      copyUrl(copyButton.dataset.anchor);
    }
  });
})();
