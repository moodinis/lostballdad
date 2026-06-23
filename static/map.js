const map = L.map('map', { scrollWheelZoom: true }).setView([37.8, -96], 4);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
  maxZoom: 19,
  subdomains: 'abcd',
}).addTo(map);

function makeClusterIcon(color) {
  return function(cluster) {
    const n = cluster.getChildCount();
    const size = n < 6 ? 32 : n < 14 ? 38 : 46;
    return L.divIcon({
      html: `<div class="cluster-icon" style="width:${size}px;height:${size}px;background:${color};">${n}</div>`,
      className: '',
      iconSize: [size, size],
    });
  };
}

const clusterGroups = {};
Object.entries(ORG_META).forEach(([org, meta]) => {
  clusterGroups[org] = L.markerClusterGroup({
    iconCreateFunction: makeClusterIcon(meta.color),
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    maxClusterRadius: 40,
  });
  map.addLayer(clusterGroups[org]);
});

const markers = events.map(ev => {
  const color = ORG_META[ev.org]?.color ?? '#888';
  const icon = L.divIcon({
    className: '',
    html: `<div class="marker-pin" style="background:${color};"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
  const m = L.marker([ev.lat, ev.lng], { icon });
  m.bindPopup(`
    <div class="tip-card" style="border-left-color:${color};">
      <div class="org">${ORG_META[ev.org]?.label ?? ev.org}</div>
      <div class="name">${ev.name}</div>
      <div class="loc">${ev.city}, ${ev.state}</div>
      <div class="date">${ev.dates}</div>
      <a class="cta" href="${ev.link}" target="_blank" rel="noopener noreferrer">Visit event page ↗</a>
    </div>`, { className: 'tourney-tip', maxWidth: 260, autoPan: true });
  return m;
});

if (markers.length) {
  map.fitBounds(L.featureGroup(markers).getBounds(), { padding: [50, 50] });
}

const activeOrgs   = new Set(Object.keys(ORG_META));
const activeMonths = new Set(MONTHS);

function rebuild() {
  Object.values(clusterGroups).forEach(g => g.clearLayers());
  let count = 0;
  events.forEach((ev, i) => {
    if (activeOrgs.has(ev.org) && activeMonths.has(ev.month)) {
      clusterGroups[ev.org].addLayer(markers[i]);
      count++;
    }
  });
  document.getElementById('visibleCount').textContent = count;
}

rebuild();

document.querySelectorAll('.chip[data-org]').forEach(chip => {
  chip.addEventListener('click', () => {
    const org = chip.dataset.org;
    activeOrgs.has(org) ? activeOrgs.delete(org) : activeOrgs.add(org);
    chip.classList.toggle('off');
    rebuild();
  });
});

document.querySelectorAll('.chip[data-month]').forEach(chip => {
  chip.addEventListener('click', () => {
    const m = chip.dataset.month;
    activeMonths.has(m) ? activeMonths.delete(m) : activeMonths.add(m);
    chip.classList.toggle('off');
    rebuild();
  });
});
