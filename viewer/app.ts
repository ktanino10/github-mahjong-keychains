import {
  Box3, DirectionalLight, Group, HemisphereLight,
  MathUtils, Mesh, MeshStandardMaterial, Object3D, PerspectiveCamera,
  NeutralToneMapping, PMREMGenerator, Scene, Spherical, SRGBColorSpace, Vector3, WebGLRenderer,
} from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { isTranslationKey, translations, type Language, type TranslationKey } from "./i18n";

const designIds = ["git_branch", "octocat", "hatsu", "chun", "haku", "iisou"] as const;
type Design = typeof designIds[number];
type Selection = Design | "all";
type View = "front" | "back" | "side" | "angle";
type HardwareKind = "ball" | "clasp";
type ViewerError = "webgl" | "lost" | "model";
interface DesignModel {
  id: Design;
  root: Object3D;
  body: Object3D;
  hardware: Object3D;
  hardwareOptions: Record<HardwareKind, Object3D>;
}

const labels: Record<Selection, TranslationKey> = {
  all: "allSelection",
  git_branch: "branchSelection",
  octocat: "octocatSelection",
  hatsu: "hatsuSelection",
  chun: "chunSelection",
  haku: "hakuSelection",
  iisou: "iisouSelection",
};
const presets: Record<View, { theta: number; phi: number }> = {
  front: { theta: 0, phi: Math.PI / 2 },
  back: { theta: Math.PI, phi: Math.PI / 2 },
  side: { theta: Math.PI / 2, phi: Math.PI / 2 },
  angle: { theta: Math.PI / 5, phi: Math.PI / 2 - 0.17 },
};

function element<T extends HTMLElement>(selector: string, type: { new(): T }): T {
  const result = document.querySelector(selector);
  if (!(result instanceof type)) throw new Error(`Required viewer control is missing: ${selector}`);
  return result;
}

const viewport = element("#viewport", HTMLElement);
const loader = element("#loader", HTMLDivElement);
const poster = element("#poster", HTMLImageElement);
const errorPanel = element("#error", HTMLDivElement);
const errorTitle = element("#error-title", HTMLElement);
const errorMessage = element("#error-message", HTMLParagraphElement);
const fieldsets = [
  element("#design-controls", HTMLFieldSetElement),
  element("#display-controls", HTMLFieldSetElement),
  element("#view-controls", HTMLFieldSetElement),
];
const nameLabel = element("#selection-name", HTMLSpanElement);
const angleLabel = element("#angle", HTMLSpanElement);
const dial = document.querySelector<SVGGElement>("#dial-pointer");
if (!dial) throw new Error("Rotation dial is missing.");
const hardwareInput = element("#show-hardware", HTMLInputElement);
const hardwareTypeInput = element("#hardware-type", HTMLSelectElement);
const hardwareNote = element("#hardware-note", HTMLParagraphElement);
const autoButton = element("#auto-rotate", HTMLButtonElement);
const rotationState = element("#rotation-state", HTMLSpanElement);
const greenChip = element("#green-chip", HTMLSpanElement);
const colorCount = element("#color-count", HTMLElement);
const viewButtons = [...document.querySelectorAll<HTMLButtonElement>("button[data-view]")];
const savedHtml = "<!doctype html>\n" + document.documentElement.outerHTML;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
let language: Language = location.hash === "#en" || (location.hash !== "#ja" && document.documentElement.lang === "en") ? "en" : "ja";
let viewerError: ViewerError | null = null;
let refreshDynamic = (): void => {
  nameLabel.textContent = text("allSelection");
  hardwareNote.textContent = text("ballNote");
  rotationState.textContent = text("off");
  colorCount.textContent = text("colorsAll");
};

function text(key: TranslationKey): string {
  return translations[language][key];
}

function refreshError(): void {
  if (!viewerError) return;
  const keys: Record<ViewerError, [TranslationKey, TranslationKey]> = {
    webgl: ["webglTitle", "webglMessage"],
    lost: ["lostTitle", "lostMessage"],
    model: ["modelTitle", "modelMessage"],
  };
  const [title, message] = keys[viewerError];
  errorTitle.textContent = text(title);
  errorMessage.textContent = text(message);
}

function applyLanguage(next: Language): void {
  language = next;
  document.documentElement.lang = next;
  document.title = text("title");
  for (const [dataAttribute, attribute] of [
    ["data-i18n", null], ["data-i18n-aria", "aria-label"], ["data-i18n-alt", "alt"],
  ] as const) {
    document.querySelectorAll<HTMLElement>(`[${dataAttribute}]`).forEach((node) => {
      const key = node.getAttribute(dataAttribute) ?? "";
      if (!isTranslationKey(key)) throw new Error(`Unknown translation key: ${key}`);
      if (attribute) node.setAttribute(attribute, text(key));
      else node.textContent = text(key);
    });
  }
  document.querySelectorAll<HTMLButtonElement>("[data-set-language]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.setLanguage === next));
  });
  refreshDynamic();
  refreshError();
}

document.querySelectorAll<HTMLButtonElement>("[data-set-language]").forEach((button) => {
  button.addEventListener("click", () => {
    const next = button.dataset.setLanguage;
    if (next !== "ja" && next !== "en") throw new Error("Unknown display language.");
    applyLanguage(next);
    history.replaceState(null, "", `#${next}`);
  });
});
applyLanguage(language);

element("#save-html", HTMLButtonElement).addEventListener("click", () => {
  const saved = new DOMParser().parseFromString(savedHtml, "text/html");
  saved.documentElement.lang = language;
  const documentText = "<!doctype html>\n" + saved.documentElement.outerHTML;
  const url = URL.createObjectURL(new Blob([documentText], { type: "text/html;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "github-mahjong-keychains-360.html";
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
});
element("#reload", HTMLButtonElement).addEventListener("click", () => location.reload());

function showError(kind: ViewerError, error?: unknown): void {
  viewerError = kind;
  document.body.dataset.state = "error";
  fieldsets.forEach((fieldset) => { fieldset.disabled = true; });
  loader.hidden = true;
  poster.hidden = false;
  refreshError();
  errorPanel.hidden = false;
  if (error) console.error(errorTitle.textContent, error);
}

function isSelection(value: string): value is Selection {
  return value === "all" || isDesign(value);
}

function isDesign(value: unknown): value is Design {
  return typeof value === "string" && designIds.some((id) => id === value);
}

function isView(value: string | undefined): value is View {
  return value !== undefined && Object.hasOwn(presets, value);
}

function decodeModel(): ArrayBuffer {
  const data = document.querySelector("#model-data")?.textContent?.trim();
  if (!data) throw new Error("The embedded model data is missing.");
  const text = atob(data);
  const buffer = new ArrayBuffer(text.length);
  const bytes = new Uint8Array(buffer);
  for (let index = 0; index < text.length; index++) bytes[index] = text.charCodeAt(index);
  return buffer;
}

async function main(): Promise<void> {
  const canvas = document.createElement("canvas");
  canvas.className = "three-canvas";
  canvas.tabIndex = 0;
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", text("keyboard"));
  const context = canvas.getContext("webgl2", { antialias: true, alpha: true });
  if (!context) {
    showError("webgl");
    return;
  }

  const renderer = new WebGLRenderer({ canvas, context, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = NeutralToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.setClearColor(0x000000, 0);
  viewport.append(canvas);
  const scene = new Scene();
  const room = new RoomEnvironment();
  const pmrem = new PMREMGenerator(renderer);
  const environment = pmrem.fromScene(room, 0.03);
  scene.environment = environment.texture;
  scene.environmentIntensity = 0.6;
  room.dispose();
  pmrem.dispose();
  scene.add(new HemisphereLight(0xffffff, 0xc9d5c8, 0.75));
  const key = new DirectionalLight(0xffffff, 1.9);
  key.position.set(-70, 100, 170);
  scene.add(key);
  const fill = new DirectionalLight(0xffffff, 0.65);
  fill.position.set(90, 20, 110);
  scene.add(fill);
  const back = new DirectionalLight(0xffffff, 1.25);
  back.position.set(-30, 40, -170);
  scene.add(back);

  const camera = new PerspectiveCamera(32, 1, 0.1, 2400);
  camera.up.set(0, 1, 0);
  const controls = new OrbitControls(camera, canvas);
  controls.enablePan = false;
  controls.enableDamping = false;
  controls.rotateSpeed = 0.7;
  controls.zoomSpeed = 0.75;
  controls.autoRotateSpeed = 1.1;
  controls.minPolarAngle = 0.03;
  controls.maxPolarAngle = Math.PI - 0.03;

  const gltf = await new GLTFLoader().parseAsync(decodeModel(), "");
  const collection = new Group();
  collection.scale.setScalar(1000);
  scene.add(collection);
  collection.add(gltf.scene);
  const models: DesignModel[] = [];
  gltf.scene.traverse((object) => {
    if (object.userData.role !== "design") return;
    const id: unknown = object.userData.design;
    if (!isDesign(id)) {
      throw new Error("The model contains an unknown design.");
    }
    const body = object.children.find((child) => child.userData.role === "body");
    const hardware = object.children.find((child) => child.userData.role === "hardware");
    if (!body || !hardware) throw new Error(`Model components are missing: ${id}`);
    const ball = hardware.children.find((child) => child.userData.kind === "ball");
    const clasp = hardware.children.find((child) => child.userData.kind === "clasp");
    if (!ball || !clasp) throw new Error(`Purchased hardware options are missing: ${id}`);
    models.push({ id, root: object, body, hardware, hardwareOptions: { ball, clasp } });
  });
  if (models.length !== designIds.length || new Set(models.map((model) => model.id)).size !== designIds.length) {
    throw new Error("The viewer needs exactly six finished designs.");
  }
  models.sort((a, b) => designIds.indexOf(a.id) - designIds.indexOf(b.id));
  let printedMeshCount = 0;
  gltf.scene.traverse((object) => {
    if (!(object instanceof Mesh)) return;
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    if (object.userData.role === "body") printedMeshCount++;
    for (const material of materials) {
      if (material instanceof MeshStandardMaterial) {
        material.envMapIntensity = object.userData.role === "hardware" ? 1.1 : 0.4;
        if (object.userData.role === "body") material.roughness = 0.42;
      }
    }
  });
  if (printedMeshCount !== 19) throw new Error("The nineteen printable color parts were not retained.");

  let selection: Selection = "all";
  let hardwareKind: HardwareKind = "ball";
  let spinning = false;
  let activeView: View | null = "angle";
  let fitDistance = 240;
  let pendingFrame: number | null = null;
  let previousTime = 0;
  let ready = false;
  let lastAngle = -1;
  let updatingPreset = false;
  let contextLost = false;
  refreshDynamic = () => {
    nameLabel.textContent = text(labels[selection]);
    canvas.setAttribute("aria-label", `${text(labels[selection])}. ${text("keyboard")}`);
    rotationState.textContent = text(spinning ? "on" : "off");
    colorCount.textContent = text(selection === "octocat" || selection === "haku" ? "colorsTwo"
      : selection === "all" ? "colorsAll"
        : selection === "hatsu" ? "colorsFour" : "colorsThree");
    hardwareNote.textContent = text(hardwareKind === "ball" ? "ballNote" : "claspNote");
  };

  function layoutModels(): void {
    const visible = models.filter((model) => model.root.visible);
    const columns = Math.min(visible.length, window.innerWidth <= 800 ? 3 : 6);
    const rows = Math.ceil(visible.length / columns);
    const rowHeight = hardwareInput.checked ? hardwareKind === "ball" ? 0.09 : 0.078 : 0.044;
    visible.forEach((model, index) => {
      const row = Math.floor(index / columns);
      const rowCount = Math.min(columns, visible.length - row * columns);
      model.root.position.x = (index % columns - (rowCount - 1) / 2) * 0.036;
      model.root.position.y = ((rows - 1) / 2 - row) * rowHeight;
    });
  }

  function updateHardware(): void {
    models.forEach((model) => {
      model.hardware.visible = hardwareInput.checked;
      model.hardwareOptions.ball.visible = hardwareKind === "ball";
      model.hardwareOptions.clasp.visible = hardwareKind === "clasp";
    });
    viewport.dataset.hardware = String(hardwareInput.checked);
    viewport.dataset.hardwareType = hardwareKind;
    layoutModels();
    refreshDynamic();
  }

  function schedule(): void {
    if (pendingFrame === null && !document.hidden && !contextLost) {
      pendingFrame = requestAnimationFrame(render);
    }
  }

  function syncAngle(): void {
    const degrees = MathUtils.radToDeg(controls.getAzimuthalAngle());
    const normalized = ((degrees % 360) + 360) % 360;
    const integer = Math.round(normalized) % 360;
    viewport.dataset.angle = normalized.toFixed(2);
    viewport.dataset.polar = MathUtils.radToDeg(controls.getPolarAngle()).toFixed(2);
    viewport.dataset.distance = camera.position.distanceTo(controls.target).toFixed(3);
    if (integer !== lastAngle) {
      angleLabel.innerHTML = `${String(integer).padStart(3, "0")}<span>°</span>`;
      dial?.setAttribute("transform", `rotate(${integer} 32 32)`);
      lastAngle = integer;
    }
  }

  function render(time: number): void {
    pendingFrame = null;
    const elapsed = previousTime ? Math.min((time - previousTime) / 1000, 1) : 0;
    previousTime = time;
    controls.autoRotate = spinning && !document.hidden;
    controls.update(elapsed);
    renderer.render(scene, camera);
    syncAngle();
    if (spinning) schedule();
  }

  function setSpinning(value: boolean): void {
    spinning = value;
    controls.autoRotate = value && !document.hidden;
    autoButton.setAttribute("aria-pressed", String(value));
    rotationState.textContent = text(value ? "on" : "off");
    viewport.dataset.spinning = String(value);
    if (value) {
      activeView = null;
      viewButtons.forEach((button) => button.setAttribute("aria-pressed", "false"));
    }
    schedule();
  }

  function visibleBounds(): Box3 {
    scene.updateMatrixWorld(true);
    const box = new Box3();
    for (const model of models) {
      if (!model.root.visible) continue;
      box.expandByObject(model.body, true);
      if (hardwareInput.checked) box.expandByObject(model.hardwareOptions[hardwareKind], true);
    }
    if (box.isEmpty()) throw new Error("The visible model bounds are empty.");
    return box;
  }

  function calculateFit(box: Box3): number {
    const size = box.getSize(new Vector3());
    // Frame the full horizontal rotation envelope, not just the initial front.
    const horizontal = Math.hypot(size.x, size.z);
    const vertical = size.y;
    const tangent = Math.tan(MathUtils.degToRad(camera.fov / 2));
    const padding = window.innerWidth <= 480 ? 1.34 : 1.29;
    return Math.max(vertical / (2 * tangent), horizontal / (2 * tangent * camera.aspect)) * padding
      + horizontal * 0.25;
  }

  function frame(view: View | null, preserveZoom = false): void {
    const box = visibleBounds();
    const zoomFactor = preserveZoom ? camera.position.distanceTo(controls.target) / fitDistance : 1;
    const spherical = new Spherical().setFromVector3(camera.position.clone().sub(controls.target));
    const angles = view ? presets[view] : { theta: spherical.theta, phi: spherical.phi };
    fitDistance = calculateFit(box);
    controls.minDistance = fitDistance * 0.24;
    controls.maxDistance = fitDistance * 3.1;
    const radius = MathUtils.clamp(fitDistance * zoomFactor, controls.minDistance, controls.maxDistance);
    controls.target.copy(box.getCenter(new Vector3()));
    const next = new Spherical(radius, angles.phi, angles.theta);
    camera.position.copy(controls.target).add(new Vector3().setFromSpherical(next));
    updatingPreset = true;
    controls.update(0);
    updatingPreset = false;
    if (view) activeView = view;
    viewButtons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.view === activeView));
    });
    syncAngle();
    schedule();
  }

  function changeSelection(value: Selection): void {
    setSpinning(false);
    selection = value;
    models.forEach((model) => {
      model.root.visible = value === "all" || value === model.id;
    });
    greenChip.hidden = value === "octocat" || value === "chun" || value === "haku";
    element("#light-green-chip", HTMLSpanElement).hidden = value !== "all" && value !== "hatsu";
    element("#red-chip", HTMLSpanElement).hidden = value !== "all" && value !== "chun";
    viewport.dataset.selection = value;
    viewport.dataset.visibleDesigns = String(models.filter((model) => model.root.visible).length);
    updateHardware();
    frame("angle");
  }

  function zoom(multiplier: number): void {
    setSpinning(false);
    const offset = camera.position.clone().sub(controls.target);
    offset.setLength(MathUtils.clamp(offset.length() * multiplier, controls.minDistance, controls.maxDistance));
    camera.position.copy(controls.target).add(offset);
    controls.update(0);
    schedule();
  }

  function resize(): void {
    const { width, height } = viewport.getBoundingClientRect();
    if (width <= 0 || height <= 0) return;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    if (ready) {
      layoutModels();
      frame(null, true);
    }
    schedule();
  }

  controls.addEventListener("change", () => {
    if (!updatingPreset) schedule();
    syncAngle();
  });
  controls.addEventListener("start", () => {
    setSpinning(false);
    activeView = null;
    canvas.classList.add("is-dragging");
    viewButtons.forEach((button) => button.setAttribute("aria-pressed", "false"));
  });
  controls.addEventListener("end", () => canvas.classList.remove("is-dragging"));
  for (const input of document.querySelectorAll<HTMLInputElement>('input[name="design"]')) {
    input.addEventListener("change", () => {
      if (isSelection(input.value)) changeSelection(input.value);
    });
  }
  hardwareInput.addEventListener("change", () => {
    updateHardware();
    frame(null);
  });
  hardwareTypeInput.addEventListener("change", () => {
    const next = hardwareTypeInput.value;
    if (next !== "ball" && next !== "clasp") throw new Error("Unknown hardware selection.");
    hardwareKind = next;
    updateHardware();
    frame(null);
  });
  autoButton.addEventListener("click", () => setSpinning(!spinning));
  viewButtons.forEach((button) => button.addEventListener("click", () => {
    if (!isView(button.dataset.view)) return;
    setSpinning(false);
    frame(button.dataset.view);
  }));
  element("#fit", HTMLButtonElement).addEventListener("click", () => {
    setSpinning(false);
    frame(activeView);
  });
  element("#zoom-in", HTMLButtonElement).addEventListener("click", () => zoom(0.82));
  element("#zoom-out", HTMLButtonElement).addEventListener("click", () => zoom(1 / 0.82));
  canvas.addEventListener("keydown", (event) => {
    if (event.key === "Home") {
      event.preventDefault();
      setSpinning(false);
      frame("angle");
      return;
    }
    if (["+", "=", "-", "_"].includes(event.key)) {
      event.preventDefault();
      zoom(["+", "="].includes(event.key) ? 0.82 : 1 / 0.82);
      return;
    }
    if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
    event.preventDefault();
    setSpinning(false);
    activeView = null;
    const offset = new Spherical().setFromVector3(camera.position.clone().sub(controls.target));
    const step = Math.PI / 18;
    if (event.key === "ArrowLeft") offset.theta -= step;
    if (event.key === "ArrowRight") offset.theta += step;
    if (event.key === "ArrowUp") offset.phi -= step;
    if (event.key === "ArrowDown") offset.phi += step;
    offset.phi = MathUtils.clamp(offset.phi, controls.minPolarAngle, controls.maxPolarAngle);
    camera.position.copy(controls.target).add(new Vector3().setFromSpherical(offset));
    controls.update(0);
    viewButtons.forEach((button) => button.setAttribute("aria-pressed", "false"));
    schedule();
  });
  reducedMotion.addEventListener("change", () => {
    if (reducedMotion.matches) setSpinning(false);
  });
  document.addEventListener("visibilitychange", () => {
    previousTime = 0;
    if (document.hidden && pendingFrame !== null) {
      cancelAnimationFrame(pendingFrame);
      pendingFrame = null;
    } else schedule();
  });
  canvas.addEventListener("webglcontextlost", (event) => {
    event.preventDefault();
    contextLost = true;
    setSpinning(false);
    if (pendingFrame !== null) cancelAnimationFrame(pendingFrame);
    pendingFrame = null;
    showError("lost");
  });

  resize();
  ready = true;
  changeSelection(selection);
  const observer = new ResizeObserver(resize);
  observer.observe(viewport);
  document.body.dataset.state = "ready";
  viewport.dataset.meshes = String(printedMeshCount);
  viewport.dataset.designs = String(models.length);
  fieldsets.forEach((fieldset) => { fieldset.disabled = false; });
  loader.hidden = true;
  poster.hidden = true;
  renderer.render(scene, camera);
  syncAngle();
  schedule();
  window.addEventListener("pagehide", (event) => {
    if (event.persisted) return;
    observer.disconnect();
    if (pendingFrame !== null) cancelAnimationFrame(pendingFrame);
    controls.dispose();
    environment.dispose();
    scene.traverse((object) => {
      if (!(object instanceof Mesh)) return;
      object.geometry.dispose();
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      materials.forEach((material) => material.dispose());
    });
    renderer.dispose();
  });
}

void main().catch((error: unknown) => {
  showError("model", error);
});
