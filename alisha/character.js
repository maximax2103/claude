// 3D Alisha Character — Three.js voxel/box pixel-art style
// Matches the pixel art reference: dark red hair, white shirt with heart, black pants, white shoes

class AlinaCharacter {
  constructor(container) {
    this.container = container;
    this.time = 0;
    this.state = 'idle';
    this.targetState = 'idle';
    this.speakInterval = null;

    this._initScene();
    this._buildCharacter();
    this._setupLights();
    this._animate();
  }

  _initScene() {
    const w = this.container.clientWidth || 320;
    const h = this.container.clientHeight || 420;

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.container.appendChild(this.renderer.domElement);

    // Scene
    this.scene = new THREE.Scene();

    // Camera
    this.camera = new THREE.PerspectiveCamera(42, w / h, 0.1, 100);
    this.camera.position.set(0, 1.2, 6.5);
    this.camera.lookAt(0, 0.8, 0);

    // Root group for whole character
    this.root = new THREE.Group();
    this.scene.add(this.root);

    // Resize
    window.addEventListener('resize', () => this._onResize());
  }

  _onResize() {
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    if (!w || !h) return;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  _box(w, h, d, color) {
    const geo = new THREE.BoxGeometry(w, h, d);
    const mat = new THREE.MeshLambertMaterial({ color });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = true;
    return mesh;
  }

  _place(mesh, x, y, z) {
    mesh.position.set(x, y, z);
    return mesh;
  }

  _setupLights() {
    // Ambient
    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambient);

    // Key light (warm front)
    const key = new THREE.DirectionalLight(0xfff4e6, 1.0);
    key.position.set(2, 4, 5);
    key.castShadow = true;
    this.scene.add(key);

    // Fill light (cool side)
    const fill = new THREE.DirectionalLight(0xe6eeff, 0.4);
    fill.position.set(-3, 2, 2);
    this.scene.add(fill);

    // Rim light (from behind)
    const rim = new THREE.DirectionalLight(0xffd6ff, 0.3);
    rim.position.set(0, 3, -4);
    this.scene.add(rim);
  }

  _buildCharacter() {
    // Color palette
    const C = {
      skin:      0xFECBA1,
      skinSh:    0xE0A07A,
      hair:      0x5C1F2E,
      hairMid:   0x7A2D40,
      hairHi:    0x9B4055,
      eye:       0x1A0810,
      eyeWh:     0xFFFFFF,
      white:     0xF8F8F8,
      shirtSh:   0xD8D8D8,
      heart:     0xFF2244,
      heartDk:   0xCC1133,
      collar:    0x111111,
      pants:     0x141420,
      shoe:      0xF0F0F0,
      shoeBlk:   0x111111,
      grass:     0x2E7D32,
      grassLt:   0x43A047,
      grassDk:   0x1B5E20,
      blush:     0xFFB0B8,
      mouth:     0xC46060,
    };

    const b = (w, h, d, c) => this._box(w, h, d, c);
    const p = (mesh, x, y, z) => { mesh.position.set(x, y, z); return mesh; };
    const add = (...meshes) => meshes.forEach(m => this.root.add(m));

    // ─── GRASS BASE ───────────────────────────────
    const grass = b(3.2, 0.28, 1.4, C.grass);
    p(grass, 0, -2.56, 0);
    const grassL = b(0.5, 0.18, 1.2, C.grassLt);
    p(grassL, -0.9, -2.38, 0);
    const grassR = b(0.4, 0.18, 1.0, C.grassLt);
    p(grassR, 0.8, -2.38, 0.1);
    const grassBlade1 = b(0.1, 0.25, 0.1, C.grassLt);
    p(grassBlade1, -1.1, -2.3, 0.3);
    const grassBlade2 = b(0.1, 0.22, 0.1, C.grassLt);
    p(grassBlade2, 0.95, -2.3, -0.2);
    add(grass, grassL, grassR, grassBlade1, grassBlade2);

    // ─── SHOES ────────────────────────────────────
    const shoeL = b(0.42, 0.22, 0.52, C.shoe);
    p(shoeL, -0.25, -2.17, 0.03);
    const solL = b(0.44, 0.09, 0.54, C.shoeBlk);
    p(solL, -0.25, -2.28, 0.03);
    const shoeR = b(0.42, 0.22, 0.52, C.shoe);
    p(shoeR, 0.25, -2.17, 0.03);
    const solR = b(0.44, 0.09, 0.54, C.shoeBlk);
    p(solR, 0.25, -2.28, 0.03);
    add(shoeL, solL, shoeR, solR);

    // ─── LEGS (pants) ─────────────────────────────
    const legL = b(0.38, 1.15, 0.38, C.pants);
    p(legL, -0.25, -1.5, 0);
    const legR = b(0.38, 1.15, 0.38, C.pants);
    p(legR, 0.25, -1.5, 0);
    add(legL, legR);

    // ─── TORSO / SHIRT ────────────────────────────
    const torso = b(0.92, 1.05, 0.46, C.white);
    p(torso, 0, -0.3, 0);

    // Shirt shadow sides
    const shtShdL = b(0.05, 1.05, 0.46, C.shirtSh);
    p(shtShdL, -0.435, -0.3, 0);
    const shtShdR = b(0.05, 1.05, 0.46, C.shirtSh);
    p(shtShdR, 0.435, -0.3, 0);

    // Collar
    const collar = b(0.48, 0.16, 0.47, C.collar);
    p(collar, 0, 0.26, 0);

    // Heart (pixel cross shape)
    const heartM = b(0.3, 0.24, 0.47, C.heart);
    p(heartM, 0, -0.28, 0);
    const heartTL = b(0.14, 0.13, 0.47, C.heart);
    p(heartTL, -0.08, -0.15, 0);
    const heartTR = b(0.14, 0.13, 0.47, C.heart);
    p(heartTR, 0.08, -0.15, 0);
    add(torso, shtShdL, shtShdR, collar, heartM, heartTL, heartTR);

    // ─── ARMS ─────────────────────────────────────
    this.leftArm = new THREE.Group();
    const lArmUp = b(0.26, 0.52, 0.32, C.white);
    p(lArmUp, 0, 0, 0);
    const lArmLo = b(0.23, 0.46, 0.29, C.skin);
    p(lArmLo, 0, -0.49, 0);
    const lHand = b(0.21, 0.2, 0.27, C.skin);
    p(lHand, 0, -0.76, 0.02);
    this.leftArm.add(lArmUp, lArmLo, lHand);
    this.leftArm.position.set(-0.62, -0.08, 0);
    this.root.add(this.leftArm);

    this.rightArm = new THREE.Group();
    const rArmUp = b(0.26, 0.52, 0.32, C.white);
    p(rArmUp, 0, 0, 0);
    const rArmLo = b(0.23, 0.46, 0.29, C.skin);
    p(rArmLo, 0, -0.49, 0);
    const rHand = b(0.21, 0.2, 0.27, C.skin);
    p(rHand, 0, -0.76, 0.02);
    this.rightArm.add(rArmUp, rArmLo, rHand);
    this.rightArm.position.set(0.62, -0.08, 0);
    this.root.add(this.rightArm);

    // ─── HEAD ─────────────────────────────────────
    this.headGroup = new THREE.Group();

    // Face (skin)
    const face = b(0.82, 0.78, 0.58, C.skin);
    p(face, 0, 0, 0);

    // Chin shadow
    const chinSh = b(0.82, 0.1, 0.56, C.skinSh);
    p(chinSh, 0, -0.34, 0);

    // Eyes
    const eyeL = b(0.14, 0.14, 0.59, C.eye);
    p(eyeL, -0.2, 0.06, 0);
    const eyeR = b(0.14, 0.14, 0.59, C.eye);
    p(eyeR, 0.2, 0.06, 0);

    // Eye highlights
    const eyeHL = b(0.05, 0.05, 0.60, C.eyeWh);
    p(eyeHL, -0.16, 0.10, 0);
    const eyeHR = b(0.05, 0.05, 0.60, C.eyeWh);
    p(eyeHR, 0.24, 0.10, 0);

    // Eyelashes (tiny dark strip above eyes)
    const lashL = b(0.17, 0.04, 0.60, C.eye);
    p(lashL, -0.2, 0.145, 0);
    const lashR = b(0.17, 0.04, 0.60, C.eye);
    p(lashR, 0.2, 0.145, 0);

    // Nose (subtle bump)
    const nose = b(0.07, 0.06, 0.595, C.skinSh);
    p(nose, 0, -0.06, 0);

    // Mouth
    this.mouthMesh = b(0.16, 0.055, 0.595, C.mouth);
    p(this.mouthMesh, 0, -0.2, 0);

    // Blush
    const blushL = b(0.13, 0.08, 0.59, C.blush);
    p(blushL, -0.3, -0.04, 0);
    blushL.material = new THREE.MeshLambertMaterial({ color: C.blush, transparent: true, opacity: 0.55 });
    const blushR = b(0.13, 0.08, 0.59, C.blush);
    p(blushR, 0.3, -0.04, 0);
    blushR.material = new THREE.MeshLambertMaterial({ color: C.blush, transparent: true, opacity: 0.55 });

    // ─── HAIR ─────────────────────────────────────
    // Back hair (wider, behind face)
    const hairBack = b(0.95, 1.15, 0.22, C.hair);
    p(hairBack, 0, -0.02, -0.35);

    // Top of head (hair)
    const hairTop = b(0.88, 0.38, 0.64, C.hair);
    p(hairTop, 0, 0.43, 0);
    const hairCrown = b(0.52, 0.17, 0.66, C.hairMid);
    p(hairCrown, 0, 0.6, 0);

    // Side hair flowing down
    const hairSL = b(0.22, 0.95, 0.58, C.hairMid);
    p(hairSL, -0.53, -0.08, 0);
    const hairSR = b(0.22, 0.95, 0.58, C.hairMid);
    p(hairSR, 0.53, -0.08, 0);

    // Hair highlights (lighter streak)
    const hairHiL = b(0.07, 0.45, 0.60, C.hairHi);
    p(hairHiL, -0.46, 0.12, 0);
    const hairHiR = b(0.07, 0.45, 0.60, C.hairHi);
    p(hairHiR, 0.46, 0.12, 0);

    // Hair fringe / bangs
    const bangC = b(0.45, 0.14, 0.60, C.hair);
    p(bangC, 0, 0.26, 0);
    const bangL = b(0.15, 0.2, 0.60, C.hair);
    p(bangL, -0.32, 0.22, 0);
    const bangR = b(0.15, 0.2, 0.60, C.hair);
    p(bangR, 0.32, 0.22, 0);

    this.headGroup.add(
      hairBack, hairTop, hairCrown, hairSL, hairSR, hairHiL, hairHiR,
      bangC, bangL, bangR,
      face, chinSh,
      eyeL, eyeR, eyeHL, eyeHR, lashL, lashR,
      nose, this.mouthMesh, blushL, blushR
    );

    this.headGroup.position.set(0, 0.92, 0);
    this.root.add(this.headGroup);

    // Shift root so character stands at y=0
    this.root.position.set(0, 0.3, 0);
  }

  setState(state) {
    this.targetState = state;
    if (state !== this.state) {
      this.state = state;
    }
  }

  startSpeaking() {
    this.setState('speaking');
  }

  stopSpeaking() {
    this.setState('idle');
  }

  showHappy() {
    this.setState('happy');
    setTimeout(() => this.setState('idle'), 2200);
  }

  showThinking() {
    this.setState('thinking');
  }

  _animate() {
    this._rafId = requestAnimationFrame(() => this._animate());
    const delta = 0.016;
    this.time += delta;
    this._update(delta);
    this.renderer.render(this.scene, this.camera);
  }

  _update(delta) {
    const t = this.time;

    // Idle float
    const floatY = Math.sin(t * 1.1) * 0.07;
    this.root.position.y = 0.3 + floatY;

    // Subtle sway
    this.root.rotation.z = Math.sin(t * 0.7) * 0.015;

    // Arm swing (gentle idle)
    this.leftArm.rotation.z  =  0.06 + Math.sin(t * 1.1) * 0.04;
    this.rightArm.rotation.z = -0.06 - Math.sin(t * 1.1) * 0.04;

    // Head
    if (this.state === 'speaking') {
      this.headGroup.rotation.x = Math.sin(t * 7) * 0.025;
      this.headGroup.rotation.z = Math.sin(t * 5) * 0.018;
      // Mouth animation
      const m = (Math.sin(t * 14) + 1) * 0.5;
      this.mouthMesh.scale.y = 1 + m * 2.0;
      this.mouthMesh.position.y = -0.2 - m * 0.025;
    } else if (this.state === 'happy') {
      this.root.position.y = 0.3 + Math.abs(Math.sin(t * 5)) * 0.18;
      this.headGroup.rotation.z = Math.sin(t * 4) * 0.06;
      this.leftArm.rotation.z  =  0.3 + Math.sin(t * 5) * 0.15;
      this.rightArm.rotation.z = -0.3 - Math.sin(t * 5) * 0.15;
      this.mouthMesh.scale.y = 1.5;
    } else if (this.state === 'thinking') {
      this.headGroup.rotation.z = 0.12;
      this.headGroup.rotation.x = -0.05;
      this.rightArm.rotation.z = -0.45;
      this.rightArm.rotation.x = 0.3;
      this.mouthMesh.scale.y = 0.7;
    } else {
      // Reset to idle
      this.headGroup.rotation.x += (0 - this.headGroup.rotation.x) * 0.1;
      this.headGroup.rotation.z += (0 - this.headGroup.rotation.z) * 0.1;
      this.mouthMesh.scale.y += (1 - this.mouthMesh.scale.y) * 0.15;
      this.mouthMesh.position.y += (-0.2 - this.mouthMesh.position.y) * 0.15;
      this.rightArm.rotation.x += (0 - this.rightArm.rotation.x) * 0.1;
    }
  }

  destroy() {
    cancelAnimationFrame(this._rafId);
    this.renderer.dispose();
    if (this.renderer.domElement.parentNode) {
      this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
    }
  }
}
