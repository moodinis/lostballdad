const map = L.map('map', { scrollWheelZoom: true }).setView([37.8, -96], 4);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
  maxZoom: 19,
}).addTo(map);

// One cluster group for all organizers, so events at the same spot share a cluster instead of
// separate per-org clusters stacking on top of each other. Mixed clusters are drawn as a ring
// split by organizer color.
function clusterIcon(cluster) {
  const n = cluster.getChildCount();
  const size = n < 6 ? 32 : n < 14 ? 38 : 46;
  const counts = {};
  cluster.getAllChildMarkers().forEach(m => { counts[m.options.org] = (counts[m.options.org] || 0) + 1; });
  let deg = 0;
  const stops = Object.entries(counts).map(([org, c]) => {
    const color = ORG_META[org]?.color ?? '#888';
    const from = deg;
    deg += (c / n) * 360;
    return `${color} ${from}deg ${deg}deg`;
  });
  return L.divIcon({
    html: `<div class="cluster-icon" style="width:${size}px;height:${size}px;background:conic-gradient(${stops.join(',')});"><span>${n}</span></div>`,
    className: '',
    iconSize: [size, size],
  });
}

const clusterGroup = L.markerClusterGroup({
  iconCreateFunction: clusterIcon,
  spiderfyOnMaxZoom: true,
  showCoverageOnHover: false,
  maxClusterRadius: 40,
});
map.addLayer(clusterGroup);

const markers = events.map(ev => {
  const color = ORG_META[ev.org]?.color ?? '#888';
  const icon = L.divIcon({
    className: '',
    html: `<div class="marker-pin" style="background:${color};"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
  const m = L.marker([ev.lat, ev.lng], { icon, org: ev.org });
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
  clusterGroup.clearLayers();
  const visible = markers.filter((m, i) => activeOrgs.has(events[i].org) && activeMonths.has(events[i].month));
  clusterGroup.addLayers(visible);
  const count = visible.length;
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
