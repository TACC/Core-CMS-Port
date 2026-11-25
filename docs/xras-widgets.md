# XRAS widgets in NAIRR

This document records what is known about the XRAS widgets embedded by the NAIRR port and the practical options for customizing their appearance.

## Widgets and documentation

NAIRR currently embeds two XRAS web components as CMS Snippets:

| Widget | NAIRR pages | Data feed | Official documentation |
| --- | --- | --- | --- |
| `@xras/projects-browser` | `generated/projects/awarded/` | `https://submit-nairr.xras.org/current-projects.json` | [Projects Browser README](https://github.com/access-ci-org/projects-browser#readme) |
| `@xras/resource-catalog` | `generated/opportunities/allocations/`, `education-call/`, `deep-partnerships/`, and `startup-project/` | `https://submit-nairr.xras.org/resources.json` | [Resource Catalog README](https://github.com/access-ci-org/resource-catalog#readme) |

The official READMEs document the mount element, the ESM import, the data URL option, and `disable_bootstrap`. The Resource Catalog README also documents category and feature filtering.

The Projects Browser README currently calls its data option `projects`. The NAIRR integration uses `api_url`, which is the option used by the deployed NAIRR widget. Confirm the option against the package version before changing it.

## What the browser shows

Both widgets render into an open Shadow DOM below their mount element. The widget owns the internal markup and injects Bootstrap 5.3.2 styles into that shadow root.

The Projects Browser currently renders Bootstrap-style pagination, including `.pagination`, `.page-item`, and `.page-link`. Its project browser also uses Bootstrap grid classes such as `.row`, `.col-sm-3`, and `.col-sm-9`.

The Resource Catalog currently renders Bootstrap-style grids, buttons, accordions, and tables. Its observed classes include `.row`, `.col-sm-4`, `.col-sm-8`, `.btn.btn-warning`, `.accordion`, `.accordion-item`, `.accordion-button`, `.accordion-collapse`, and `.accordion-body`.

The widgets do not expose observed CSS Shadow Parts: no internal elements currently have `part` attributes. Therefore document-level Core-Styles or NAIRR CSS cannot directly style those internal elements, even when the selector names match Bootstrap or Core-Styles classes.

## Customization options

### 1. Use the widget's supported configuration first

The documented `disable_bootstrap` option is the cleanest configuration hook:

```js
renderCatalog({
  api_url: "https://submit-nairr.xras.org/resources.json",
  disable_bootstrap: true
});
```

The Projects Browser README documents the same option. However, disabling the widget's Bootstrap does not make Core-Styles cross the Shadow DOM boundary. It is useful only when the replacement styles are also loaded inside the widget's shadow root or the widget itself provides another styling mechanism.

### 2. Ask upstream to expose a theme hook

The durable solution is an upstream API such as one of these:

- CSS custom properties that the widget actually consumes.
- CSS Shadow Parts, for example `part="pagination"`, styled with `#projects_browser_app::part(pagination)`.
- An `exportparts` mapping if the widget nests additional custom elements.
- A documented stylesheet or theme option that is inserted into the widget's shadow root.

At present, the widgets do not expose the observed internal elements through `part`, so `::part(...)` selectors cannot be used yet.

### 3. Inject styles into the open shadow root at runtime

Because the current roots are open, a small runtime bridge can insert a stylesheet without access to the widget source:

```js
const host = document.querySelector("#resource_catalog_app");
const root = host?.shadowRoot;

if (root && !root.querySelector("link[data-nairr-widget-theme]")) {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = "/static/nairr/css/xras-widget.css";
  link.dataset.nairrWidgetTheme = "";
  root.append(link);
}
```

The same approach can target `#projects_browser_app`. The stylesheet must use selectors for the widget's internal markup, for example `.pagination`, `.page-link`, `.btn-warning`, or `.accordion-button`, and must be loaded after the widget's own stylesheet when overrides depend on cascade order.

This is a workaround rather than a stable public API. It can break if the widget changes its internal class names, switches to a closed shadow root, recreates the root, or changes when it finishes rendering. A `MutationObserver` can wait for the root, but it does not remove those maintenance risks.

### 4. Style only the host from NAIRR CSS

Regular NAIRR CSS can style the light-DOM host itself, including its width, margins, and surrounding layout:

```css
#resource_catalog_app,
#projects_browser_app {
  width: 100%;
  margin-block: 2rem;
}
```

Selectors such as `#resource_catalog_app .btn-warning` do not reach the button inside the shadow root. `::slotted(...)` is also not applicable because the widget's internal controls are not slotted light-DOM children.

## Recommended path

For a short-term NAIRR visual adjustment, use a narrowly scoped runtime bridge and keep its selectors in a dedicated `xras-widget.css` file. Do not copy the widget's internal markup into CMS content or depend on broad global Bootstrap overrides.

For a maintainable solution, contribute or request an upstream theme API—preferably CSS custom properties for colors and spacing plus named CSS Shadow Parts for structural controls. Keep `disable_bootstrap` as an explicit option only when the replacement stylesheet is injected into the same shadow root.

## Local integration points

- [Projects Browser snippet](../cms/src/apps/cms_port/sites/nairr/projects_browser_snippets.py)
- [Resource Catalog snippets](../cms/src/apps/cms_port/sites/nairr/resource_catalog_snippets.py)
- [NAIRR site settings and styles](site-nairr.md)
