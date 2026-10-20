(function () {
	/**
	 * Core-Styles bootstrap--nav-tabs: ul.nav.nav-tabs > li.nav-item > a.nav-link.active
	 * The showcase app toggles `.selected`; we mirror that to `.active`.
	 */
	var observer = null;

	function applyBootstrapTabMarkup(cats) {
		cats.classList.add('nav', 'nav-tabs');
		if (cats.getAttribute('role') !== 'tablist') {
			cats.setAttribute('role', 'tablist');
		}
		cats.querySelectorAll('li').forEach(function (li) {
			li.classList.add('nav-item');
		});
		cats.querySelectorAll('a[href]').forEach(function (a, index) {
			a.classList.add('nav-link');
			a.setAttribute('role', 'tab');
			if (!a.id) {
				a.id = 'pilotresources-tab-' + (a.getAttribute('data-cat') || index);
			}
		});
	}

	function syncCategoryTabActive(cats) {
		cats.querySelectorAll('a[href]').forEach(function (link) {
			var on = link.classList.contains('selected');
			link.classList.add('nav-link');
			link.classList.toggle('active', on);
			var aria = on ? 'true' : 'false';
			if (link.getAttribute('aria-selected') !== aria) {
				link.setAttribute('aria-selected', aria);
			}
		});
	}

	function enhanceCategoryTabs(root) {
		var cats = root.querySelector('.nairr-filters ul.cats');
		if (!cats) {
			return;
		}
		applyBootstrapTabMarkup(cats);
		syncCategoryTabActive(cats);
	}

	function enhancePagination(root) {
		root.querySelectorAll('.hz-pagination').forEach(function (el) {
			el.classList.add('pagination');
			el.querySelectorAll('a').forEach(function (a) {
				a.classList.add('page-link');
			});
		});
	}

	function enhance(root) {
		if (!root) {
			return;
		}
		if (observer) {
			observer.disconnect();
		}
		enhanceCategoryTabs(root);
		enhancePagination(root);
		if (observer) {
			observer.observe(root, { childList: true, subtree: true });
		}
	}

	function watch() {
		var app = document.getElementById('app');
		if (!app) {
			return;
		}
		var scheduled = false;
		observer = new MutationObserver(function () {
			if (scheduled) {
				return;
			}
			scheduled = true;
			requestAnimationFrame(function () {
				scheduled = false;
				enhance(app);
			});
		});
		enhance(app);
		app.addEventListener(
			'click',
			function (event) {
				if (event.target.closest('.nairr-filters ul.cats a[href]')) {
					requestAnimationFrame(function () {
						var cats = app.querySelector('.nairr-filters ul.cats');
						if (cats) {
							syncCategoryTabActive(cats);
						}
					});
				}
			},
			true
		);
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', watch);
	} else {
		watch();
	}
})();
