const CONTRACT_API_URL = 'http://localhost:8000/contract';
const VOICE_API_URL = 'http://localhost:8000/voice-query';

const TYPE_COLORS = {
  component: 0x58f3de,
  layer: 0x4ca7ff,
  process: 0xffb34b,
  data: 0xb9b6ff,
  named_entity: 0xf36bd7,
  default: 0x9aa6b2
};

const TYPE_TAG_COLORS = {
  component: '#0b887d',
  layer: '#175ea8',
  process: '#9a5b0f',
  data: '#5650a6',
  named_entity: '#8a247a',
  default: '#4f5a66'
};

const TYPE_DESCRIPTIONS = {
  component: 'A structural concept or system part extracted from the research material.',
  layer: 'A hierarchical stage or abstraction layer in the knowledge structure.',
  process: 'An operation, transformation, or mechanism described by the paper.',
  data: 'A signal, token, representation, or information object moving through the system.',
  named_entity: 'A named method, model, organization, dataset, or paper-specific entity.',
  default: 'A concept extracted from the uploaded research diagram or document.'
};

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x020611);
scene.fog = new THREE.FogExp2(0x020611, 0.035);

const camera = new THREE.PerspectiveCamera(64, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 3.1, 9.4);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.xr.enabled = true;
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.25;
document.body.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.055;
controls.minDistance = 4.2;
controls.maxDistance = 20;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.34;
controls.target.set(0, 1.15, 0);
controls.update();

['start', 'wheel', 'touchstart'].forEach(eventName => {
  controls.addEventListener(eventName, () => { controls.autoRotate = false; });
});

scene.add(new THREE.HemisphereLight(0x7ed6ff, 0x030711, 1.35));

const keyLight = new THREE.DirectionalLight(0xe6fbff, 1.8);
keyLight.position.set(5, 8, 6);
scene.add(keyLight);

const rimLight = new THREE.PointLight(0x58f3de, 2.6, 18);
rimLight.position.set(-5, 4, -5);
scene.add(rimLight);

const graphGroup = new THREE.Group();
graphGroup.position.set(0, 1.05, 0);
scene.add(graphGroup);

const nodeMeshes = {};
const nodeById = {};
const labelSprites = [];
const allNodeMeshes = [];
const edgeMap = {};
const edgeDetailsByNode = {};
const edgeMeshes = [];
const edgePulses = [];
const glowObjects = [];

let currentContract = null;
let selectedNodeId = null;
let recognition = null;
let isMicActive = false;

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const tooltip = document.getElementById('tooltip');
const clock = new THREE.Clock();

initXRButton();
addEnvironment();
loadContract();

function unwrapContract(data) {
  return data?.contract || data;
}

function normalizeType(type) {
  return TYPE_COLORS[type] ? type : 'default';
}

function fetchJson(url) {
  return fetch(url).then(response => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  });
}

function loadContract() {
  fetchJson(CONTRACT_API_URL)
    .catch(() => fetchJson('contract.json'))
    .then(data => {
      currentContract = unwrapContract(data);
      buildGraph(currentContract);
      setHudCounts(currentContract);
      finishLoading();
    })
    .catch(error => {
      console.error('Failed to load contract data:', error);
      const loading = document.getElementById('loading');
      if (loading) loading.textContent = 'Could not load graph contract';
    });
}

function setHudCounts(contract) {
  const nodeCount = document.getElementById('node-count');
  const edgeCount = document.getElementById('edge-count');
  const stats = document.getElementById('stats');
  const legend = document.getElementById('legend');

  if (nodeCount) nodeCount.textContent = contract.nodes?.length || 0;
  if (edgeCount) edgeCount.textContent = contract.edges?.length || 0;
  if (stats) stats.style.display = 'block';
  if (legend) legend.style.display = 'block';
}

function finishLoading() {
  const loading = document.getElementById('loading');
  if (!loading) return;
  loading.style.opacity = '0';
  setTimeout(() => loading.remove(), 550);
}

function buildGraph(contract) {
  const nodes = contract.nodes || [];
  const edges = contract.edges || [];
  const layout = buildForceLayout(nodes, edges);
  const degree = countDegree(nodes, edges);

  nodes.forEach(node => {
    const positioned = {
      ...node,
      type: normalizeType(node.type),
      x: layout[node.id]?.x || 0,
      y: layout[node.id]?.y || 0,
      z: layout[node.id]?.z || 0,
      degree: degree[node.id] || 0
    };
    nodeById[node.id] = positioned;
    edgeMap[node.id] = [];
    edgeDetailsByNode[node.id] = [];
  });

  edges.forEach(edge => {
    if (nodeById[edge.from] && nodeById[edge.to]) {
      edgeMap[edge.from].push(edge.to);
      edgeMap[edge.to].push(edge.from);
      edgeDetailsByNode[edge.from].push({ nodeId: edge.to, label: edge.label || 'related_to', direction: 'out' });
      edgeDetailsByNode[edge.to].push({ nodeId: edge.from, label: edge.label || 'related_to', direction: 'in' });
    }
  });

  Object.values(nodeById).forEach(node => buildNode(node));
  edges.forEach((edge, index) => buildEdge(edge, index, edges.length));
  addConstellationHalo();
}

function countDegree(nodes, edges) {
  const degree = {};
  nodes.forEach(node => { degree[node.id] = 0; });
  edges.forEach(edge => {
    if (degree[edge.from] !== undefined) degree[edge.from] += 1;
    if (degree[edge.to] !== undefined) degree[edge.to] += 1;
  });
  return degree;
}

function buildForceLayout(nodes, edges) {
  const positions = {};
  const velocities = {};
  const radius = Math.max(3.4, Math.sqrt(nodes.length || 1) * 1.15);

  nodes.forEach((node, index) => {
    const angle = index * 2.399963;
    positions[node.id] = new THREE.Vector3(
      Number.isFinite(node.x) ? node.x * 2.4 : Math.cos(angle) * radius,
      Number.isFinite(node.y) ? node.y * 1.5 + 0.65 : Math.sin(index * 1.71) * 1.7 + 0.65,
      Number.isFinite(node.z) ? node.z * 2.4 : Math.sin(angle) * radius
    );
    velocities[node.id] = new THREE.Vector3();
  });

  const nodeIds = nodes.map(node => node.id);
  for (let step = 0; step < 120; step++) {
    for (let i = 0; i < nodeIds.length; i++) {
      for (let j = i + 1; j < nodeIds.length; j++) {
        const a = positions[nodeIds[i]];
        const b = positions[nodeIds[j]];
        const delta = a.clone().sub(b);
        const dist = Math.max(delta.length(), 0.45);
        const force = delta.normalize().multiplyScalar(0.018 / (dist * dist));
        velocities[nodeIds[i]].add(force);
        velocities[nodeIds[j]].sub(force);
      }
    }

    edges.forEach(edge => {
      const a = positions[edge.from];
      const b = positions[edge.to];
      if (!a || !b) return;
      const delta = b.clone().sub(a);
      const dist = Math.max(delta.length(), 0.01);
      const target = 2.1;
      const force = delta.normalize().multiplyScalar((dist - target) * 0.006);
      velocities[edge.from].add(force);
      velocities[edge.to].sub(force);
    });

    nodeIds.forEach(id => {
      positions[id].add(velocities[id]);
      positions[id].multiplyScalar(0.998);
      velocities[id].multiplyScalar(0.84);
    });
  }

  return Object.fromEntries(Object.entries(positions).map(([id, position]) => [id, position]));
}

function buildNode(node) {
  const color = TYPE_COLORS[node.type] || TYPE_COLORS.default;
  const importance = Math.min(node.degree, 6);
  const radius = 0.22 + importance * 0.028;
  const group = new THREE.Group();
  group.position.copy(new THREE.Vector3(node.x, node.y, node.z));
  group.userData = { ...node, radius, baseY: node.y };

  const core = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 32, 24),
    new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: 1.2,
      roughness: 0.22,
      metalness: 0.18
    })
  );
  core.userData = group.userData;
  group.add(core);

  const glow = new THREE.Mesh(
    new THREE.SphereGeometry(radius * 2.35, 32, 24),
    new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.16,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  );
  group.add(glow);
  glowObjects.push({ object: glow, base: radius * 2.35, speed: 0.7 + Math.random() * 0.45 });

  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(radius * 1.62, 0.011, 8, 72),
    new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.45,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  );
  ring.rotation.x = Math.PI / 2.2;
  group.add(ring);

  if (node.degree >= 3) {
    const light = new THREE.PointLight(color, 0.85, 4.2);
    light.position.set(0, 0, 0);
    group.add(light);
  }

  const label = makeLabel(node.label, color, 0.82 + Math.min(node.degree, 5) * 0.045);
  label.position.set(0, radius + 0.48, 0);
  group.add(label);
  labelSprites.push(label);

  graphGroup.add(group);
  nodeMeshes[node.id] = group;
  allNodeMeshes.push(core);
}

function makeLabel(text, color, scale = 1) {
  const canvas = document.createElement('canvas');
  canvas.width = 640;
  canvas.height = 160;
  const ctx = canvas.getContext('2d');
  const display = text.length > 34 ? `${text.slice(0, 31)}...` : text;

  const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
  gradient.addColorStop(0, 'rgba(5, 14, 28, 0.18)');
  gradient.addColorStop(0.5, 'rgba(8, 22, 48, 0.74)');
  gradient.addColorStop(1, 'rgba(5, 14, 28, 0.18)');

  ctx.fillStyle = gradient;
  roundRect(ctx, 56, 38, 528, 76, 22);
  ctx.fill();
  ctx.strokeStyle = `#${color.toString(16).padStart(6, '0')}`;
  ctx.globalAlpha = 0.42;
  ctx.stroke();
  ctx.globalAlpha = 1;

  ctx.fillStyle = 'rgba(238, 250, 255, 0.94)';
  ctx.font = '600 34px Segoe UI, Arial, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(display, 320, 77);

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthWrite: false
  });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(1.95 * scale, 0.49 * scale, 1);
  return sprite;
}

function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}

function buildEdge(edge, index, totalEdges) {
  const a = nodeMeshes[edge.from];
  const b = nodeMeshes[edge.to];
  if (!a || !b) return;

  const start = a.position.clone();
  const end = b.position.clone();
  const midpoint = start.clone().add(end).multiplyScalar(0.5);
  const lift = Math.min(1.85, 0.65 + start.distanceTo(end) * 0.12);
  midpoint.y += lift;
  midpoint.x += Math.sin(index * 1.37) * 0.18;
  midpoint.z += Math.cos(index * 1.19) * 0.18;

  const curve = new THREE.QuadraticBezierCurve3(start, midpoint, end);
  const points = curve.getPoints(44);
  const color = blendEdgeColor(a.userData.type, b.userData.type);

  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({
    color,
    transparent: true,
    opacity: 0.54,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });
  const line = new THREE.Line(geometry, material);
  line.userData = { ...edge, curve, baseOpacity: 0.54 };
  graphGroup.add(line);
  edgeMeshes.push(line);

  const glowLine = new THREE.Line(
    geometry.clone(),
    new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity: 0.16,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  );
  glowLine.scale.setScalar(1.003);
  graphGroup.add(glowLine);

  if (index < 56) {
    const pulseCount = totalEdges > 18 ? 1 : 2;
    for (let i = 0; i < pulseCount; i++) {
      addEdgeParticle(curve, index, i, color);
    }
  }
}

function blendEdgeColor(typeA, typeB) {
  if (typeA === 'process' || typeB === 'process') return 0xffcf83;
  if (typeA === 'named_entity' || typeB === 'named_entity') return 0xd891ff;
  if (typeA === 'layer' || typeB === 'layer') return 0x6cbaff;
  return 0x8df7ff;
}

function addEdgeParticle(curve, edgeIndex, particleIndex, color) {
  const particle = new THREE.Mesh(
    new THREE.SphereGeometry(0.052, 12, 10),
    new THREE.MeshBasicMaterial({
      color: 0xf5fbff,
      transparent: true,
      opacity: 0.92,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  );
  const halo = new THREE.Mesh(
    new THREE.SphereGeometry(0.13, 12, 10),
    new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.18,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  );
  particle.add(halo);
  graphGroup.add(particle);
  edgePulses.push({
    mesh: particle,
    curve,
    speed: 0.16 + Math.random() * 0.18,
    progress: ((edgeIndex * 0.071) + particleIndex * 0.5) % 1
  });
}

function highlightNode(nodeId) {
  if (selectedNodeId === nodeId) {
    resetHighlight();
    return;
  }

  selectedNodeId = nodeId;
  const connected = new Set([nodeId, ...(edgeMap[nodeId] || [])]);

  Object.values(nodeMeshes).forEach(group => {
    const id = group.userData.id;
    const active = id === nodeId;
    const related = connected.has(id);
    group.traverse(child => {
      if (child.material?.opacity !== undefined) {
        child.material.opacity = active ? child.material.opacity : related ? Math.max(child.material.opacity, 0.38) : 0.12;
      }
    });
    group.scale.setScalar(active ? 1.42 : related ? 1.12 : 0.92);
  });

  edgeMeshes.forEach(line => {
    const on = line.userData.from === nodeId || line.userData.to === nodeId;
    line.material.opacity = on ? 0.95 : 0.07;
    line.material.color.set(on ? 0xf5fbff : 0x10213a);
  });

  showInfoPanel(nodeById[nodeId]);
}

function resetHighlight() {
  selectedNodeId = null;

  Object.values(nodeMeshes).forEach(group => {
    group.scale.setScalar(1);
    group.traverse(child => {
      if (child.material?.opacity !== undefined) {
        if (child.type === 'Sprite') child.material.opacity = 1;
        else if (child.geometry?.type === 'SphereGeometry') child.material.opacity = child.material.transparent ? 0.16 : 1;
        else child.material.opacity = 0.45;
      }
    });
  });

  edgeMeshes.forEach(line => {
    line.material.opacity = line.userData.baseOpacity || 0.54;
    line.material.color.set(blendEdgeColor(
      nodeById[line.userData.from]?.type,
      nodeById[line.userData.to]?.type
    ));
  });

  hideInfoPanel();
}

function showInfoPanel(node) {
  if (!node) return;
  const panel = document.getElementById('info-panel');
  const typeColor = TYPE_TAG_COLORS[node.type] || TYPE_TAG_COLORS.default;
  const connectedIds = edgeMap[node.id] || [];
  const connectionDetails = edgeDetailsByNode[node.id] || [];

  document.getElementById('info-name').textContent = node.label;
  document.getElementById('info-type').textContent = node.type.replace('_', ' ');
  document.getElementById('info-type').style.background = typeColor;
  document.getElementById('info-description').textContent = describeNode(node, connectionDetails);

  const container = document.getElementById('info-connections');
  container.innerHTML = '';
  if (!connectionDetails.length) {
    const empty = document.createElement('span');
    empty.className = 'connection-pill';
    empty.textContent = 'No direct links';
    container.appendChild(empty);
  } else {
    connectionDetails.slice(0, 14).forEach(detail => {
      const pill = document.createElement('span');
      pill.className = 'connection-pill';
      const neighbor = nodeById[detail.nodeId]?.label || detail.nodeId;
      const arrow = detail.direction === 'out' ? '->' : '<-';
      pill.textContent = `${detail.label} ${arrow} ${neighbor}`;
      container.appendChild(pill);
    });
  }

  if (panel) panel.style.display = 'block';
}

function describeNode(node, connections = []) {
  const base = TYPE_DESCRIPTIONS[node.type] || TYPE_DESCRIPTIONS.default;
  const label = node.label.toLowerCase();
  const relationSummary = summarizeRelations(connections);
  const linkText = connections.length === 1 ? '1 direct relationship' : `${connections.length} direct relationships`;

  const roleRules = [
    {
      match: ['multi-head attention', 'multi head attention'],
      text: 'Internally, it runs several attention heads in parallel, lets each head focus on different token relationships, then combines those views into one richer representation.'
    },
    {
      match: ['self-attention', 'self attention', 'attention'],
      text: 'Internally, it compares tokens with other tokens, assigns importance weights, and pulls the most relevant context into the current representation.'
    },
    {
      match: ['encoder'],
      text: 'Internally, it reads the input sequence, mixes token meaning with context, and produces representations that later modules can consume.'
    },
    {
      match: ['decoder'],
      text: 'Internally, it uses previous output state plus encoded context to predict or construct the next output representation.'
    },
    {
      match: ['feed forward', 'ffn', 'mlp'],
      text: 'Internally, it applies dense transformations after attention, expanding and compressing features so each position can refine its representation.'
    },
    {
      match: ['norm', 'normalization'],
      text: 'Internally, it stabilizes values between stages, keeping activations balanced so deeper layers remain trainable and predictable.'
    },
    {
      match: ['add', 'residual'],
      text: 'Internally, it preserves an earlier signal and adds the transformed output back in, helping information flow through many layers.'
    },
    {
      match: ['positional encoding', 'position encoding'],
      text: 'Internally, it injects order information so the model can distinguish where each token appears in the sequence.'
    },
    {
      match: ['embedding'],
      text: 'Internally, it converts symbols or tokens into numeric vectors that downstream layers can compare, transform, and combine.'
    },
    {
      match: ['input token', 'input tokens'],
      text: 'Internally, this is the starting data stream: text units are converted into vectors before contextual processing begins.'
    },
    {
      match: ['output token', 'output tokens'],
      text: 'Internally, this is the generated or predicted data stream produced after the model transforms context into an answer or sequence.'
    },
    {
      match: ['convolution', 'cnn', 'kernel'],
      text: 'Internally, it scans local regions, detects reusable patterns, and builds feature maps that higher layers can interpret.'
    },
    {
      match: ['blockchain', 'block', 'hash', 'transaction'],
      text: 'Internally, it represents an ordered trust structure where records are linked, verified, and made difficult to alter.'
    }
  ];

  const specific = roleRules.find(rule => rule.match.some(term => label.includes(term)))?.text;
  const role = specific || `${base} Internally, this node acts as a paper concept in the graph; its exact meaning is inferred from the OCR text and its neighboring relationships.`;
  return `${role} It has ${linkText}.${relationSummary}`;
}

function summarizeRelations(connections = []) {
  if (!connections.length) return '';
  const examples = connections.slice(0, 3).map(detail => {
    const neighbor = nodeById[detail.nodeId]?.label || detail.nodeId;
    return `${detail.label} ${neighbor}`;
  });
  return ` Key links: ${examples.join(', ')}.`;
}

function hideInfoPanel() {
  const panel = document.getElementById('info-panel');
  if (panel) panel.style.display = 'none';
}

window.resetHighlight = resetHighlight;

function addEnvironment() {
  const floor = new THREE.GridHelper(42, 42, 0x1f9fff, 0x10213a);
  floor.position.y = -2.1;
  floor.material.transparent = true;
  floor.material.opacity = 0.18;
  scene.add(floor);

  const floorGlow = new THREE.Mesh(
    new THREE.CircleGeometry(18, 96),
    new THREE.MeshBasicMaterial({
      color: 0x0a3b66,
      transparent: true,
      opacity: 0.13,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  );
  floorGlow.rotation.x = -Math.PI / 2;
  floorGlow.position.y = -2.12;
  scene.add(floorGlow);

  addStars(1200, 72, 0.78);
  addStars(240, 38, 0.9, 0x7ed6ff);
  addNebula();
}

function addStars(count, spread, opacity, color = 0xffffff) {
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    positions[i * 3] = (Math.random() - 0.5) * spread;
    positions[i * 3 + 1] = (Math.random() - 0.25) * spread * 0.72;
    positions[i * 3 + 2] = (Math.random() - 0.5) * spread;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({
    color,
    size: 0.045,
    transparent: true,
    opacity,
    depthWrite: false
  });
  scene.add(new THREE.Points(geometry, material));
}

function addNebula() {
  const geometry = new THREE.SphereGeometry(11.5, 48, 32);
  const material = new THREE.MeshBasicMaterial({
    color: 0x153a68,
    transparent: true,
    opacity: 0.055,
    blending: THREE.AdditiveBlending,
    side: THREE.BackSide,
    depthWrite: false
  });
  const nebula = new THREE.Mesh(geometry, material);
  nebula.position.set(0, 1.2, 0);
  scene.add(nebula);
}

function addConstellationHalo() {
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(5.4, 0.012, 8, 192),
    new THREE.MeshBasicMaterial({
      color: 0x58f3de,
      transparent: true,
      opacity: 0.12,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  );
  ring.rotation.x = Math.PI / 2;
  graphGroup.add(ring);
}

function initXRButton() {
  const button = document.getElementById('vr-btn');
  if (!button) return;

  if (!navigator.xr) {
    button.textContent = 'XR Not Supported';
    button.disabled = true;
    return;
  }

  navigator.xr.isSessionSupported('immersive-vr').then(supported => {
    if (!supported) {
      button.textContent = 'XR Not Supported';
      button.disabled = true;
      return;
    }

    button.textContent = 'Enter XR Mode';
    let session = null;
    button.onclick = () => {
      if (!session) {
        navigator.xr.requestSession('immersive-vr', { optionalFeatures: ['local-floor', 'bounded-floor'] })
          .then(nextSession => {
            session = nextSession;
            button.textContent = 'Exit XR Mode';
            renderer.xr.setSession(nextSession);
            graphGroup.position.set(0, 1.2, -3.2);
            nextSession.addEventListener('end', () => {
              session = null;
              button.textContent = 'Enter XR Mode';
              graphGroup.position.set(0, 1.05, 0);
            });
          });
      } else {
        session.end();
      }
    };
  });
}

window.addEventListener('mousemove', event => {
  updateMouse(event);
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(allNodeMeshes, false);
  if (hits.length) {
    const data = hits[0].object.userData;
    showTooltip(event, data);
    document.body.style.cursor = 'pointer';
  } else {
    tooltip.style.display = 'none';
    document.body.style.cursor = 'default';
  }
});

window.addEventListener('click', event => {
  updateMouse(event);
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(allNodeMeshes, false);
  if (hits.length) highlightNode(hits[0].object.userData.id);
  else resetHighlight();
});

window.addEventListener('keydown', event => {
  if (event.key === 'Escape') resetHighlight();
});

function updateMouse(event) {
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
}

function showTooltip(event, data) {
  const typeColor = TYPE_TAG_COLORS[data.type] || TYPE_TAG_COLORS.default;
  document.getElementById('tt-type').textContent = data.type.replace('_', ' ');
  document.getElementById('tt-type').style.background = typeColor;
  document.getElementById('tt-label').textContent = data.label;
  document.getElementById('tt-id').textContent = `${data.degree || 0} relationships`;
  document.getElementById('tt-description').textContent = describeNode(data, edgeDetailsByNode[data.id] || []);
  tooltip.style.display = 'block';
  tooltip.style.left = `${Math.min(event.clientX + 16, window.innerWidth - 300)}px`;
  tooltip.style.top = `${Math.max(event.clientY - 12, 16)}px`;
}

[0, 1].forEach(index => {
  const controller = renderer.xr.getController(index);
  controller.addEventListener('selectstart', () => {
    const rotation = new THREE.Matrix4().identity().extractRotation(controller.matrixWorld);
    const ray = new THREE.Raycaster();
    ray.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    ray.ray.direction.set(0, 0, -1).applyMatrix4(rotation);
    const hits = ray.intersectObjects(allNodeMeshes, false);
    if (hits.length) highlightNode(hits[0].object.userData.id);
    else resetHighlight();
  });
  scene.add(controller);

  const laser = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, 0, -4)
  ]);
  controller.add(new THREE.Line(
    laser,
    new THREE.LineBasicMaterial({
      color: 0x9befff,
      transparent: true,
      opacity: 0.32,
      blending: THREE.AdditiveBlending
    })
  ));
});

function initVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    const status = document.getElementById('voice-status');
    if (status) status.textContent = 'Speech input needs Chrome or Edge';
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.onresult = event => {
    const question = event.results[0][0].transcript;
    const status = document.getElementById('voice-status');
    if (status) status.textContent = `You asked: "${question}"`;
    sendVoiceQuery(question);
  };
  recognition.onerror = () => {
    isMicActive = false;
    updateMicButton();
  };
  recognition.onend = () => {
    isMicActive = false;
    updateMicButton();
  };
}

function toggleMic() {
  if (!recognition) initVoice();
  if (!recognition) return;

  if (isMicActive) {
    recognition.stop();
    isMicActive = false;
  } else {
    recognition.start();
    isMicActive = true;
    const status = document.getElementById('voice-status');
    if (status) status.textContent = 'Listening...';
  }
  updateMicButton();
}

function updateMicButton() {
  const button = document.getElementById('mic-btn');
  if (!button) return;
  button.textContent = isMicActive ? 'Stop listening' : 'Ask and speak a question';
  button.style.background = isMicActive
    ? 'linear-gradient(135deg, rgba(155, 40, 70, 0.72), rgba(52, 17, 36, 0.74))'
    : 'linear-gradient(135deg, rgba(44, 69, 148, 0.62), rgba(11, 25, 56, 0.7))';
}

async function sendVoiceQuery(question) {
  if (!currentContract) {
    speakAnswer('The graph is still loading. Please try again in a moment.');
    return;
  }

  const activeNodeId = selectedNodeId || currentContract.nodes?.[0]?.id;
  if (!activeNodeId) return;

  try {
    const response = await fetch(VOICE_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        active_node_id: activeNodeId,
        contract: currentContract
      })
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    const answerText = result.answer || result.adaptive_response?.answer || 'No answer returned.';
    const box = document.getElementById('voice-answer-box');
    const answer = document.getElementById('voice-answer');
    if (answer) answer.textContent = answerText;
    if (box) box.style.display = 'block';
    if (result.highlight_node) highlightNode(result.highlight_node);
    speakAnswer(answerText);
  } catch (error) {
    console.error('Voice query failed:', error);
    speakAnswer('I could not reach the voice tutor endpoint.');
  }
}

function speakAnswer(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  window.speechSynthesis.speak(utterance);
}

window.toggleMic = toggleMic;

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

renderer.setAnimationLoop(() => {
  const delta = clock.getDelta();
  const elapsed = clock.elapsedTime;

  graphGroup.rotation.y += delta * 0.035;

  edgePulses.forEach(pulse => {
    pulse.progress += pulse.speed * delta;
    if (pulse.progress > 1) pulse.progress -= 1;
    pulse.mesh.position.copy(pulse.curve.getPoint(pulse.progress));
    const scale = 0.82 + Math.sin(elapsed * 7 + pulse.progress * 9) * 0.18;
    pulse.mesh.scale.setScalar(scale);
  });

  glowObjects.forEach((entry, index) => {
    const pulse = 1 + Math.sin(elapsed * entry.speed + index) * 0.08;
    entry.object.scale.setScalar(pulse);
    entry.object.material.opacity = 0.12 + Math.sin(elapsed * entry.speed + index * 0.5) * 0.035;
  });

  Object.values(nodeMeshes).forEach((group, index) => {
    const important = group.userData.degree >= 3;
    const bob = Math.sin(elapsed * 1.2 + index * 0.77) * (important ? 0.08 : 0.045);
    group.position.y = group.userData.baseY + bob;
    group.rotation.y += delta * (important ? 0.42 : 0.22);
  });

  labelSprites.forEach(sprite => {
    sprite.quaternion.copy(camera.quaternion);
  });

  controls.update();
  renderer.render(scene, camera);
});
