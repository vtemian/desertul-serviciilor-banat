const FILES = {
  uats: "data/uats_timis.geojson",
  services: "data/services_timis.geojson",
  vignettes: "data/vignettes.json",
};

const TRANSLATIONS = {
  ro: {
    "brand.title": "Deșertul de servicii, Banat",
    "brand.tagline": "Investiție, nu desființare.",
    "view.composite": "Acces total",
    "view.school": "Școli",
    "view.gp": "Medici de familie",
    "view.hospital": "Spitale",
    "nav.methodology": "Metodologie",
    "story.title": "Cei mai prost serviți cinci",
    "legend.title": "Scor compozit",
    "legend.distance": "Distanțe în linie dreaptă.",
    "footer.sources": "Sursa: SIIIR (Ministerul Educației, 2016), CNAS / CAS Timiș, ANCPI, INS Recensământ 2021.",
    "footer.disclaimer": "Acest site este o inițiativă civică independentă, nu reprezintă o poziție oficială PNL. Nu propune desființarea localităților.",
    "popup.composite": "Scor compozit",
    "popup.school_score": "Scor școli",
    "popup.gp_score": "Scor medici de familie",
    "popup.hospital_score": "Scor spitale",
    "popup.partial": "(date parțiale)",
  },
  en: {
    "brand.title": "Service Desert, Banat",
    "brand.tagline": "Investment, not abolition.",
    "view.composite": "Overall access",
    "view.school": "Schools",
    "view.gp": "Family doctors",
    "view.hospital": "Hospitals",
    "nav.methodology": "Methodology",
    "story.title": "The five worst-served",
    "legend.title": "Composite score",
    "legend.distance": "Straight-line distances.",
    "footer.sources": "Source: SIIIR (Ministry of Education, 2016), CNAS / CAS Timiș, ANCPI, INS Census 2021.",
    "footer.disclaimer": "This site is an independent civic initiative advocating for rural investment. It is not an official PNL position and does not propose abolishing localities.",
    "popup.composite": "Composite score",
    "popup.school_score": "School score",
    "popup.gp_score": "Family-doctor score",
    "popup.hospital_score": "Hospital score",
    "popup.partial": "(partial data)",
  },
};

let lang = "ro";
let uatsGeo = null;
let map = null;
let currentView = "composite";

const t = (k) => TRANSLATIONS[lang][k] ?? TRANSLATIONS.ro[k] ?? k;

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
}

function slugify(s) {
  return s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text != null) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}

function isNum(v) {
  return v != null && !Number.isNaN(Number(v));
}

function field(panel, labelKey, value) {
  const p = document.createElement("p");
  p.appendChild(el("strong", t(labelKey) + ": "));
  p.appendChild(document.createTextNode(value));
  panel.appendChild(p);
}

async function loadAll() {
  const [uats, services, vignettes] = await Promise.all([
    fetch(FILES.uats).then((r) => r.json()),
    fetch(FILES.services).then((r) => r.json()),
    fetch(FILES.vignettes).then((r) => r.json()),
  ]);
  return { uats, services, vignettes };
}

function initMap() {
  map = new maplibregl.Map({
    container: "map",
    style: {
      version: 8,
      sources: {
        basemap: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution: "(c) OpenStreetMap contributors",
        },
      },
      layers: [{ id: "basemap", type: "raster", source: "basemap" }],
    },
    center: [21.55, 45.85],
    zoom: 8.2,
    minZoom: 7.5,
    maxZoom: 14,
  });
  return new Promise((resolve) => map.on("load", resolve));
}

let selectedFeatureId = null;

function setupLayers(services) {
  map.addSource("uats", { type: "geojson", data: uatsGeo, generateId: true });
  map.addLayer({
    id: "uats-fill",
    type: "fill",
    source: "uats",
    paint: { "fill-color": ["get", "_display_color"], "fill-opacity": 0.78 },
  });
  map.addLayer({
    id: "uats-border",
    type: "line",
    source: "uats",
    paint: { "line-color": "#1a1410", "line-width": 0.6 },
  });
  map.addLayer({
    id: "uats-hover-outline",
    type: "line",
    source: "uats",
    paint: { "line-color": "#c9a86b", "line-width": 1.6 },
    filter: ["==", ["id"], -1],
  });
  map.addLayer({
    id: "uats-selected-fill",
    type: "fill",
    source: "uats",
    paint: { "fill-color": "#003DA5", "fill-opacity": 0.15 },
    filter: ["==", ["id"], -1],
  });
  map.addLayer({
    id: "uats-selected-outline",
    type: "line",
    source: "uats",
    paint: { "line-color": "#003DA5", "line-width": 2.4 },
    filter: ["==", ["id"], -1],
  });

  map.addSource("services", { type: "geojson", data: services });
  const colors = { school: "#fbb040", gp: "#7fb069", hospital: "#d62828" };
  for (const [layer, type] of [["schools-points", "school"], ["gps-points", "gp"], ["hospitals-points", "hospital"]]) {
    map.addLayer({
      id: layer,
      type: "circle",
      source: "services",
      filter: ["==", ["get", "type"], type],
      paint: {
        "circle-radius": 4,
        "circle-color": colors[type],
        "circle-stroke-color": "#1a1410",
        "circle-stroke-width": 1,
      },
      layout: { visibility: "none" },
    });
  }

  map.on("mousemove", "uats-fill", (e) => {
    if (!e.features || e.features.length === 0) return;
    const id = e.features[0].id;
    map.setFilter("uats-hover-outline", ["==", ["id"], id]);
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "uats-fill", () => {
    map.setFilter("uats-hover-outline", ["==", ["id"], -1]);
    map.getCanvas().style.cursor = "";
  });
}

function setView(view) {
  currentView = view;
  for (const f of uatsGeo.features) {
    f.properties._display_color = f.properties[`_color_${view}`] ?? f.properties._color_composite;
  }
  map.getSource("uats").setData(uatsGeo);
  const visible = {
    composite: [],
    school: ["schools-points"],
    gp: ["gps-points"],
    hospital: ["hospitals-points"],
  }[view] ?? [];
  for (const lyr of ["schools-points", "gps-points", "hospitals-points"]) {
    map.setLayoutProperty(lyr, "visibility", visible.includes(lyr) ? "visible" : "none");
  }
  document.querySelectorAll("[data-view]").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === view);
  });
  if (window.plausible) window.plausible("view_mode_change", { props: { project: "desertul", view } });
}

function highlightSelected(featureId) {
  selectedFeatureId = featureId;
  const f = featureId == null ? -1 : featureId;
  map.setFilter("uats-selected-fill", ["==", ["id"], f]);
  map.setFilter("uats-selected-outline", ["==", ["id"], f]);
}

function renderDetail(feature) {
  const p = feature.properties;
  const panel = document.getElementById("detail-panel");
  panel.classList.remove("hidden");
  while (panel.firstChild) panel.removeChild(panel.firstChild);

  panel.appendChild(el("h2", p.name));

  const compositeP = document.createElement("p");
  compositeP.className = "composite";
  compositeP.appendChild(el("strong", t("popup.composite") + ": "));
  const compositeVal = isNum(p.composite_score)
    ? `${Number(p.composite_score).toFixed(0)}/100`
    : "n/a";
  compositeP.appendChild(document.createTextNode(compositeVal));
  if (p.partial_data) {
    compositeP.appendChild(document.createTextNode(" "));
    compositeP.appendChild(el("em", t("popup.partial")));
  }
  panel.appendChild(compositeP);

  field(
    panel,
    "popup.school_score",
    isNum(p.school_score) ? `${Number(p.school_score).toFixed(0)}/100` : "n/a",
  );

  if (isNum(p.gp_score)) {
    field(panel, "popup.gp_score", `${Number(p.gp_score).toFixed(0)}/100`);
  }

  field(
    panel,
    "popup.hospital_score",
    isNum(p.hospital_score) ? `${Number(p.hospital_score).toFixed(0)}/100` : "n/a",
  );

  highlightSelected(feature.id);

  if (window.plausible) {
    window.plausible("permalink_visit", { props: { project: "desertul", uat: p.name } });
  }
  history.replaceState(null, "", "#" + slugify(p.name) + "-tm");
}

function renderStory(vignettes) {
  const ol = document.getElementById("story-list");
  while (ol.firstChild) ol.removeChild(ol.firstChild);
  for (const v of vignettes.vignettes) {
    const li = document.createElement("li");
    li.appendChild(el("strong", v.name));
    li.appendChild(document.createTextNode(` (${v.composite_score}/100)`));
    li.appendChild(document.createElement("br"));
    li.appendChild(document.createTextNode(v.headline[lang] ?? v.headline.ro));
    li.addEventListener("click", () => {
      const f = uatsGeo.features.find((feat) => feat.properties.siruta === v.siruta);
      if (f) renderDetail(f);
    });
    ol.appendChild(li);
  }
}

function openFromHash() {
  const slug = location.hash.slice(1);
  if (!slug) return;
  const f = uatsGeo.features.find((feat) => slugify(feat.properties.name) + "-tm" === slug);
  if (f) {
    renderDetail(f);
    if (window.plausible) {
      window.plausible("permalink_visit", { props: { project: "desertul", uat: f.properties.name, source: "hash" } });
    }
  }
}

(async function bootstrap() {
  const { uats, services, vignettes } = await loadAll();
  uatsGeo = uats;
  await initMap();
  setupLayers(services);
  applyI18n();
  renderStory(vignettes);
  setView("composite");
  openFromHash();

  document.querySelectorAll("[data-view]").forEach((b) =>
    b.addEventListener("click", () => setView(b.dataset.view)),
  );

  document.getElementById("lang-toggle").addEventListener("click", () => {
    lang = lang === "ro" ? "en" : "ro";
    document.documentElement.lang = lang;
    document.getElementById("lang-toggle").textContent = lang === "ro" ? "EN" : "RO";
    applyI18n();
    renderStory(vignettes);
    if (window.plausible) window.plausible("language_change", { props: { project: "desertul", lang } });
  });

  const methBtn = document.getElementById("open-methodology");
  if (methBtn) {
    methBtn.addEventListener("click", () => {
      const modal = document.getElementById("methodology-modal");
      if (modal && typeof modal.showModal === "function") {
        while (modal.firstChild) modal.removeChild(modal.firstChild);
        modal.appendChild(el("h2", t("brand.tagline")));
        modal.appendChild(el("p", t("footer.sources")));
        modal.appendChild(el("p", t("footer.disclaimer")));
        const close = el("button", "OK");
        close.addEventListener("click", () => modal.close());
        modal.appendChild(close);
        modal.showModal();
      }
      if (window.plausible) window.plausible("methodology_open", { props: { project: "desertul" } });
    });
  }

  map.on("click", "uats-fill", (e) => {
    if (e.features && e.features[0]) renderDetail(e.features[0]);
  });
  window.addEventListener("hashchange", openFromHash);
})();
