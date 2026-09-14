
/* ¦¦ ADVANCED 3D SCENE: CRYSTAL + ORBITS + PARTICLES ¦¦ */
(function initThreeJS() {
  const container = document.getElementById('three-canvas-container');
  if (!container || typeof THREE === 'undefined') return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.z = 7;

  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(renderer.domElement);

  const group = new THREE.Group();
  scene.add(group);

  // 1. Center Crystal (Core & Wireframe)
  const coreMaterial = new THREE.MeshPhongMaterial({ color: 0xa78bfa, emissive: 0x3b0764, shininess: 100, flatShading: true });
  const wireMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true, transparent: true, opacity: 0.15 });
  const geometry = new THREE.IcosahedronGeometry(1.2, 1);
  const coreMesh = new THREE.Mesh(geometry, coreMaterial);
  const wireMesh = new THREE.Mesh(new THREE.IcosahedronGeometry(1.25, 1), wireMaterial);
  group.add(coreMesh);
  group.add(wireMesh);

  // 2. Data Orbit Rings
  const ringMat = new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true, transparent: true, opacity: 0.08 });
  const ring1 = new THREE.Mesh(new THREE.TorusGeometry(2.4, 0.01, 4, 60), ringMat);
  ring1.rotation.x = Math.PI / 2;
  const ring2 = new THREE.Mesh(new THREE.TorusGeometry(3.0, 0.01, 4, 60), ringMat);
  ring2.rotation.y = Math.PI / 3;
  ring2.rotation.x = Math.PI / 6;
  group.add(ring1);
  group.add(ring2);

  // 3. Orbiting Data Nodes (Cubes)
  const nodesGroup = new THREE.Group();
  const nodeGeo = new THREE.BoxGeometry(0.12, 0.12, 0.12);
  const nodeMat = new THREE.MeshPhongMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 0.8 });
  for(let i=0; i<10; i++) {
    const node = new THREE.Mesh(nodeGeo, nodeMat);
    const radius = 2.4 + (Math.random() * 0.6);
    const angle = (i / 10) * Math.PI * 2;
    node.position.set(Math.cos(angle) * radius, (Math.random() - 0.5) * 1.5, Math.sin(angle) * radius);
    node.userData = { rx: (Math.random() - 0.5) * 0.05, ry: (Math.random() - 0.5) * 0.05 };
    nodesGroup.add(node);
  }
  group.add(nodesGroup);

  // 4. Particle Data Dust
  const particleCount = 250;
  const particleGeo = new THREE.BufferGeometry();
  const particlePos = new Float32Array(particleCount * 3);
  for(let i=0; i<particleCount*3; i+=3) {
      const radius = 1.8 + Math.random() * 3.5;
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos(Math.random() * 2 - 1);
      particlePos[i] = radius * Math.sin(phi) * Math.cos(theta);
      particlePos[i+1] = radius * Math.sin(phi) * Math.sin(theta);
      particlePos[i+2] = radius * Math.cos(phi);
  }
  particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));
  const particleMat = new THREE.PointsMaterial({ color: 0xa78bfa, size: 0.05, transparent: true, opacity: 0.6 });
  const particleSystem = new THREE.Points(particleGeo, particleMat);
  group.add(particleSystem);

  // Lights
  const light = new THREE.DirectionalLight(0xffffff, 1);
  light.position.set(5, 5, 5);
  scene.add(light);
  scene.add(new THREE.AmbientLight(0x404040));

  // Connect to landing.js via global vars
  window.threeTargetColor = null;
  window.threeCoreMat = coreMaterial;
  window.threeParticleMat = particleMat;

  function animate() {
    requestAnimationFrame(animate);
    
    // Lerp colors from intersection observer
    if (window.threeTargetColor) {
      coreMaterial.color.lerp(window.threeTargetColor, 0.05);
      particleMat.color.lerp(window.threeTargetColor, 0.05);
    }
    
    // Base scroll rotation
    const scrollY = window.scrollY || 0;
    group.rotation.y = scrollY * 0.0015;
    group.rotation.x = scrollY * 0.0008;
    
    // Animations
    coreMesh.rotation.y += 0.003;
    coreMesh.rotation.x += 0.001;
    ring1.rotation.z -= 0.0015;
    ring2.rotation.z += 0.002;

    nodesGroup.rotation.y += 0.004;
    nodesGroup.rotation.z -= 0.001;
    nodesGroup.children.forEach(node => {
       node.rotation.x += node.userData.rx;
       node.rotation.y += node.userData.ry;
    });
    
    particleSystem.rotation.y += 0.001;
    particleSystem.rotation.x -= 0.0005;

    // Levitation
    group.position.y = Math.sin(Date.now() * 0.0015) * 0.15;

    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener('resize', () => {
    if(!container.clientWidth) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  });
})();

