// ================================================================
// ArchViz-XR — main.js
// Ro · Week 4: Performance-optimised build
// Edges = Lines (not tubes) · Basic materials · Max 20 pulses
// ================================================================

const SCALE        = 3;
const NODE_RADIUS  = 0.18;
const LABEL_OFFSET = 0.32;

const TYPE_COLORS = {
  component:    0x5DCAA5,
  layer:        0x378ADD,
  process:      0xEF9F27,
  data:         0xAFA9EC,
  named_entity: 0xE06FBF,
  default:      0x888780
};

const TYPE_TAG_COLORS = {
  component:    '#0F6E56',
  layer:        '#185FA5',
  process:      '#854F0B',
  data:         '#4A4580',
  named_entity: '#8B2265',
  default:      '#5F5E5A'
};

const EDGE_COLOR = 0x5566bb;
const BG_COLOR   = 0x0a0a0f;
const CONTRACT_API_URL = 'http://localhost:8000/contract';

// ── SCENE ──────────────────────────────────────────────────────
const scene = new THREE.Scene();
scene.background = new THREE.Color(BG_COLOR);

// ── CAMERA ─────────────────────────────────────────────────────
const camera = new THREE.PerspectiveCamera(
  75, window.innerWidth / window.innerHeight, 0.1, 1000
);
camera.position.set(0, 1.6, 6);

// ── RENDERER ───────────────────────────────────────────────────
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.xr.enabled = true;
document.body.appendChild(renderer.domElement);

// ── VR BUTTON (inline) ─────────────────────────────────────────
(function initVRButton() {
  const btn = document.getElementById('vr-btn');
  if (!btn) return;
  if (!navigator.xr) {
    btn.textContent = 'VR Not Available';
    btn.disabled = true; return;
  }
  navigator.xr.isSessionSupported('immersive-vr').then(supported => {
    if (!supported) { btn.textContent = 'VR Not Supported'; btn.disabled = true; return; }
    btn.textContent = 'Enter VR';
    let session = null;
    btn.onclick = () => {
      if (!session) {
        navigator.xr.requestSession('immersive-vr', {
          optionalFeatures: ['local-floor', 'bounded-floor']
        }).then(s => {
          session = s;
          btn.textContent = 'Exit VR';
          renderer.xr.setSession(s);
          graphGroup.position.set(0, 1.2, -3);
          s.addEventListener('end', () => {
            session = null;
            btn.textContent = 'Enter VR';
            graphGroup.position.set(0, 1.2, -2);
          });
        });
      } else { session.end(); }
    };
  });
})();

// ── ORBIT CONTROLS ─────────────────────────────────────────────
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance   = 1;
controls.maxDistance   = 20;
controls.target.set(0, 1.6, 0);
controls.update();

// ── LIGHTS ─────────────────────────────────────────────────────
scene.add(new THREE.AmbientLight(0xffffff, 0.7));
const dir = new THREE.DirectionalLight(0xffffff, 0.6);
dir.position.set(5, 10, 5);
scene.add(dir);

// ── GRAPH GROUP ────────────────────────────────────────────────
const graphGroup = new THREE.Group();
graphGroup.position.set(0, 1.2, -2);
scene.add(graphGroup);

// ── STORAGE ────────────────────────────────────────────────────
const nodeMeshes    = {};
const allNodeMeshes = [];
const edgeMap       = {};   // id → [connected ids]
const edgeMeshes    = [];   // for highlight
const edgePulses    = [];   // max 20
let currentContract = null;

// ── LABEL SPRITE ───────────────────────────────────────────────
function makeLabel(text, scale = 1.0) {
  const canvas = document.createElement('canvas');
  canvas.width = 256; canvas.height = 64;
  const ctx    = canvas.getContext('2d');
  ctx.fillStyle = 'rgba(8,8,20,0.80)';
  ctx.fillRect(4, 4, 248, 56);
  const display = text.length > 28 ? text.substring(0, 28) + '…' : text;
  ctx.fillStyle = '#ffffff';
  ctx.font      = '500 20px sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(display, 128, 32);
  const mat = new THREE.SpriteMaterial({
    map: new THREE.CanvasTexture(canvas), transparent: true, depthWrite: false
  });
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set(scale * 1.1, scale * 0.28, 1);
  return sprite;
}

// ── BUILD NODES ────────────────────────────────────────────────
function buildNodes(nodes) {
  // Share ONE geometry + create individual materials
  const geo = new THREE.SphereGeometry(NODE_RADIUS, 12, 12);

  nodes.forEach(node => {
    const hex = TYPE_COLORS[node.type] ?? TYPE_COLORS.default;
    // MeshBasicMaterial — no lighting calc, much faster
    const mat  = new THREE.MeshBasicMaterial({ color: hex });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(node.x * SCALE, node.y * SCALE, node.z * SCALE);
    mesh.userData = { id: node.id, label: node.label, type: node.type };
    graphGroup.add(mesh);
    nodeMeshes[node.id] = mesh;
    allNodeMeshes.push(mesh);
    edgeMap[node.id] = [];

    const label = makeLabel(node.label);
    label.position.set(
      node.x * SCALE,
      node.y * SCALE + NODE_RADIUS + LABEL_OFFSET,
      node.z * SCALE
    );
    graphGroup.add(label);
  });
}

// ── BUILD EDGES — using Lines, not TubeGeometry ────────────────
function buildEdges(edges) {
  const lineMat = new THREE.LineBasicMaterial({
    color: EDGE_COLOR, transparent: true, opacity: 0.45
  });

  // Pulse geometry — tiny sphere, shared
  const pulseGeo = new THREE.SphereGeometry(0.055, 6, 6);
  let   pulseCount = 0;

  edges.forEach((edge, i) => {
    const a = nodeMeshes[edge.from];
    const b = nodeMeshes[edge.to];
    if (!a || !b) { console.warn(`⚠️ skipped: ${edge.from}→${edge.to}`); return; }

    edgeMap[edge.from]?.push(edge.to);
    edgeMap[edge.to]?.push(edge.from);

    // Straight line between nodes
    const points = [a.position.clone(), b.position.clone()];
    const geo    = new THREE.BufferGeometry().setFromPoints(points);
    const line   = new THREE.Line(geo, lineMat.clone());
    line.userData = { from: edge.from, to: edge.to };
    graphGroup.add(line);
    edgeMeshes.push(line);

    // Add pulse only for every 3rd edge (max 20 total) — performance
    if (pulseCount < 20 && i % 3 === 0) {
      const pulseMat = new THREE.MeshBasicMaterial({
        color: 0xaaccff, transparent: true, opacity: 0.9
      });
      const pulse = new THREE.Mesh(pulseGeo, pulseMat);
      graphGroup.add(pulse);

      // Straight line curve — pulse travels exactly along the edge
      const curve = new THREE.LineCurve3(
        a.position.clone(),
        b.position.clone()
      );

      edgePulses.push({
        mesh: pulse, curve,
        speed:    0.2 + Math.random() * 0.25,
        progress: i / edges.length
      });
      pulseCount++;
    }
  });

  console.log(`✅ Built ${edges.length} edges · ${pulseCount} pulses`);
}

// ── HIGHLIGHT ──────────────────────────────────────────────────
let selectedNodeId = null;

function highlightNode(nodeId) {
  if (selectedNodeId === nodeId) { resetHighlight(); return; }
  selectedNodeId = nodeId;
  const connected = new Set([nodeId, ...(edgeMap[nodeId] ?? [])]);

  allNodeMeshes.forEach(m => {
    const hex = TYPE_COLORS[m.userData.type] ?? TYPE_COLORS.default;
    if (m.userData.id === nodeId) {
      m.material.color.set(0xffffff); m.scale.setScalar(1.5);
    } else if (connected.has(m.userData.id)) {
      m.material.color.set(hex);      m.scale.setScalar(1.15);
    } else {
      m.material.color.set(0x222230); m.scale.setScalar(1.0);
    }
  });

  edgeMeshes.forEach(l => {
    const on = l.userData.from === nodeId || l.userData.to === nodeId;
    l.material.color.set(on ? 0x88aaff : 0x111122);
    l.material.opacity = on ? 0.9 : 0.08;
  });

  showInfoPanel(nodeMeshes[nodeId]?.userData);
}

function resetHighlight() {
  selectedNodeId = null;
  allNodeMeshes.forEach(m => {
    m.material.color.set(TYPE_COLORS[m.userData.type] ?? TYPE_COLORS.default);
    m.scale.setScalar(1.0);
  });
  edgeMeshes.forEach(l => {
    l.material.color.set(EDGE_COLOR); l.material.opacity = 0.45;
  });
  hideInfoPanel();
}

// ── INFO PANEL ─────────────────────────────────────────────────
function showInfoPanel(u) {
  if (!u) return;
  const panel = document.getElementById('info-panel');
  const tc    = TYPE_TAG_COLORS[u.type] ?? TYPE_TAG_COLORS.default;
  document.getElementById('info-name').textContent        = u.label;
  document.getElementById('info-type').textContent        = u.type;
  document.getElementById('info-type').style.background   = tc;
  document.getElementById('info-id').textContent          = 'id: ' + u.id;
  document.getElementById('info-connections').textContent =
    `${edgeMap[u.id]?.length ?? 0} connections`;
  if (panel) panel.style.display = 'block';
}

function hideInfoPanel() {
  const p = document.getElementById('info-panel');
  if (p) p.style.display = 'none';
}
window.resetHighlight = resetHighlight;

// ── FLOOR + STARS ──────────────────────────────────────────────
function addFloor() {
  scene.add(new THREE.GridHelper(30, 30, 0x1a1a2e, 0x0f0f1a));
}

function addStars() {
  const count = 800;
  const pos   = new Float32Array(count * 3).map(() => (Math.random() - 0.5) * 80);
  const geo   = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  scene.add(new THREE.Points(geo, new THREE.PointsMaterial({
    color: 0xffffff, size: 0.07, transparent: true, opacity: 0.5
  })));
}

// ── LOAD JSON ──────────────────────────────────────────────────
function fetchJson(url) {
  return fetch(url).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  });
}

fetchJson(CONTRACT_API_URL)
  .catch(() => fetchJson('contract.json'))
  .then(data => {
    currentContract = data;
    console.log(`📦 Loaded: ${data.nodes.length} nodes · ${data.edges.length} edges`);
    buildNodes(data.nodes);
    buildEdges(data.edges);
    addFloor();
    addStars();

    const nc = document.getElementById('node-count');
    const ec = document.getElementById('edge-count');
    const st = document.getElementById('stats');
    if (nc) nc.textContent   = data.nodes.length;
    if (ec) ec.textContent   = data.edges.length;
    if (st) st.style.display = 'block';

    const lg = document.getElementById('legend');
    if (lg) lg.style.display = 'flex';

    const loading = document.getElementById('loading');
    if (loading) { loading.style.opacity = '0'; setTimeout(() => loading.remove(), 500); }
  })
  .catch(err => console.error('Failed to load contract data:', err));

// ── HOVER + CLICK ──────────────────────────────────────────────
const raycaster = new THREE.Raycaster();
const mouse     = new THREE.Vector2();
const tooltip   = document.getElementById('tooltip');

window.addEventListener('mousemove', e => {
  mouse.x =  (e.clientX / window.innerWidth)  * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(allNodeMeshes, false);
  if (hits.length > 0) {
    const { id, label, type } = hits[0].object.userData;
    const tc = TYPE_TAG_COLORS[type] ?? TYPE_TAG_COLORS.default;
    document.getElementById('tt-type').textContent        = type  ?? '';
    document.getElementById('tt-type').style.background   = tc;
    document.getElementById('tt-type').style.color        = '#fff';
    document.getElementById('tt-type').style.padding      = '2px 8px';
    document.getElementById('tt-type').style.borderRadius = '10px';
    document.getElementById('tt-label').textContent       = label ?? '';
    document.getElementById('tt-id').textContent          = 'id: ' + (id ?? '');
    tooltip.style.display = 'block';
    tooltip.style.left    = (e.clientX + 16) + 'px';
    tooltip.style.top     = (e.clientY - 10) + 'px';
    document.body.style.cursor = 'pointer';
  } else {
    tooltip.style.display = 'none';
    document.body.style.cursor = 'default';
  }
});

window.addEventListener('click', e => {
  mouse.x =  (e.clientX / window.innerWidth)  * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(allNodeMeshes, false);
  hits.length > 0 ? highlightNode(hits[0].object.userData.id) : resetHighlight();
});

window.addEventListener('keydown', e => { if (e.key === 'Escape') resetHighlight(); });

// ── VR CONTROLLERS ─────────────────────────────────────────────
[0, 1].forEach(i => {
  const ctrl = renderer.xr.getController(i);
  ctrl.addEventListener('selectstart', () => {
    const m = new THREE.Matrix4().identity().extractRotation(ctrl.matrixWorld);
    const r = new THREE.Raycaster();
    r.ray.origin.setFromMatrixPosition(ctrl.matrixWorld);
    r.ray.direction.set(0, 0, -1).applyMatrix4(m);
    const hits = r.intersectObjects(allNodeMeshes, false);
    hits.length > 0 ? highlightNode(hits[0].object.userData.id) : resetHighlight();
  });
  scene.add(ctrl);
  const lineGeo = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0,0,0), new THREE.Vector3(0,0,-4)
  ]);
  ctrl.add(new THREE.Line(lineGeo,
    new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.25 })
  ));
});

// ── VOICE ──────────────────────────────────────────────────────
const VOICE_API_URL = 'http://localhost:8000/voice-query';
let recognition = null, isMicActive = false;

function initVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { console.warn('Speech API needs Chrome'); return; }
  recognition = new SR();
  recognition.lang = 'en-US'; recognition.interimResults = false;
  recognition.onresult = e => {
    const q  = e.results[0][0].transcript;
    const st = document.getElementById('voice-status');
    if (st) st.textContent = `You asked: "${q}"`;
    sendVoiceQuery(q);
  };
  recognition.onerror = () => { isMicActive = false; updateMicBtn(); };
  recognition.onend   = () => { isMicActive = false; updateMicBtn(); };
}

function speakAnswer(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'en-US'; window.speechSynthesis.speak(u);
}

async function sendVoiceQuery(question) {
  if (!currentContract) {
    speakAnswer('The graph is still loading. Please try again in a moment.');
    return;
  }

  const activeNodeId = selectedNodeId || currentContract.nodes?.[0]?.id;
  if (!activeNodeId) return;

  try {
    const res = await fetch(VOICE_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        active_node_id: activeNodeId,
        contract: currentContract
      })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const result = await res.json();
    const box = document.getElementById('voice-answer-box');
    const answer = document.getElementById('voice-answer');
    if (answer) answer.textContent = result.answer;
    if (box) box.style.display = 'block';
    if (result.highlight_node) highlightNode(result.highlight_node);
    speakAnswer(result.answer);
  } catch (err) {
    console.error('Voice query failed:', err);
    speakAnswer('I could not reach the voice tutor endpoint.');
  }
}

function toggleMic() {
  if (!recognition) initVoice();
  if (!recognition) return;
  if (isMicActive) { recognition.stop(); isMicActive = false; }
  else {
    recognition.start(); isMicActive = true;
    const s = document.getElementById('voice-status');
    if (s) s.textContent = '🎤 Listening...';
  }
  updateMicBtn();
}

function updateMicBtn() {
  const b = document.getElementById('mic-btn');
  if (!b) return;
  b.textContent = isMicActive ? '🔴 Stop' : '🎤 Ask';
  b.style.background = isMicActive ? '#8B2222' : '#1a1a3a';
}
window.toggleMic = toggleMic;

// ── RESIZE ─────────────────────────────────────────────────────
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ── ANIMATION LOOP ─────────────────────────────────────────────
const clock = new THREE.Clock();

renderer.setAnimationLoop(() => {
  const delta = clock.getDelta();
  edgePulses.forEach(p => {
    p.progress += p.speed * delta;
    if (p.progress > 1) p.progress -= 1;
    p.mesh.position.copy(p.curve.getPoint(p.progress));
  });
  controls.update();
  renderer.render(scene, camera);
});
