const who = document.querySelector("#who");
const usage = document.querySelector("#usage");
const recent = document.querySelector("#recent");
const summary = document.querySelector("#summary");
const matches = document.querySelector("#matches");
const steps = document.querySelector("#steps");
const saved = document.querySelector("#saved");
const planError = document.querySelector("#plan-error");
const replay = document.querySelector("#replay");
const modelNote = document.querySelector("#model-note");

let activePlan = null;
let playTimer = null;
let playIndex = 0;

function line(id, x1, y1, x2, y2) {
  const node = document.querySelector(id);
  node.setAttribute("x1", x1);
  node.setAttribute("y1", y1);
  node.setAttribute("x2", x2);
  node.setAttribute("y2", y2);
}

function renderPose(servos) {
  const shoulder = { x: 150, y: 168 };
  const shoulderAngle = ((90 - servos.shoulder) * Math.PI) / 180;
  const elbow = {
    x: shoulder.x + Math.cos(shoulderAngle) * 78,
    y: shoulder.y - Math.sin(shoulderAngle) * 78,
  };
  const forearmAngle = shoulderAngle - ((servos.elbow - 90) * Math.PI) / 180;
  const wrist = {
    x: elbow.x + Math.cos(forearmAngle) * 64,
    y: elbow.y - Math.sin(forearmAngle) * 64,
  };
  const spread = 6 + (servos.gripper / 180) * 18;
  const normal = forearmAngle + Math.PI / 2;
  line("#upper", shoulder.x, shoulder.y, elbow.x, elbow.y);
  line("#fore", elbow.x, elbow.y, wrist.x, wrist.y);
  line(
    "#grip-a",
    wrist.x,
    wrist.y,
    wrist.x + Math.cos(forearmAngle) * 16 + Math.cos(normal) * spread,
    wrist.y - Math.sin(forearmAngle) * 16 - Math.sin(normal) * spread,
  );
  line(
    "#grip-b",
    wrist.x,
    wrist.y,
    wrist.x + Math.cos(forearmAngle) * 16 - Math.cos(normal) * spread,
    wrist.y - Math.sin(forearmAngle) * 16 + Math.sin(normal) * spread,
  );
  const joint = document.querySelector("#elbow-joint");
  joint.setAttribute("cx", elbow.x);
  joint.setAttribute("cy", elbow.y);
  document.querySelector("#base-dial").setAttribute(
    "transform",
    `rotate(${servos.base - 90} 150 188)`,
  );
  for (const name of ["base", "shoulder", "elbow", "gripper"]) {
    document.querySelector(`#sv-${name}`).textContent = `${Math.round(servos[name])}°`;
  }
}

function stopPlay() {
  if (playTimer) {
    clearTimeout(playTimer);
    playTimer = null;
  }
}

function highlight(index) {
  document.querySelectorAll(".step").forEach((node, stepIndex) => {
    node.classList.toggle("active", stepIndex === index);
  });
}

function play() {
  if (!activePlan || !activePlan.frames.length) return;
  stopPlay();
  const tick = () => {
    const frame = activePlan.frames[playIndex];
    renderPose(frame.servos);
    highlight(playIndex);
    const wait = frame.duration_ms || 300;
    playIndex = (playIndex + 1) % activePlan.frames.length;
    playTimer = setTimeout(tick, wait);
  };
  tick();
}

function showPlan(plan) {
  activePlan = plan;
  playIndex = 0;
  summary.textContent = plan.summary;
  matches.innerHTML = "";
  for (const match of plan.matches) {
    const score = Math.max(0, Math.min(1, match.score));
    const node = document.createElement("article");
    node.className = "match";
    const header = document.createElement("header");
    const title = document.createElement("strong");
    title.textContent = match.title;
    const scoreNode = document.createElement("span");
    scoreNode.textContent = score.toFixed(2);
    header.append(title, scoreNode);
    const clause = document.createElement("small");
    clause.textContent = match.clause;
    const bar = document.createElement("div");
    bar.className = "bar";
    const fill = document.createElement("i");
    fill.style.width = `${Math.round(score * 100)}%`;
    bar.appendChild(fill);
    node.append(header, clause, bar);
    matches.appendChild(node);
  }
  steps.innerHTML = "";
  plan.frames.forEach((frame, index) => {
    const node = document.createElement("article");
    node.className = "step";
    const title = document.createElement("strong");
    title.textContent = frame.label;
    const detail = document.createElement("small");
    detail.textContent = `${frame.duration_ms} ms · base ${frame.servos.base} · shoulder ${frame.servos.shoulder} · elbow ${frame.servos.elbow} · gripper ${frame.servos.gripper}`;
    node.append(title, document.createElement("br"), detail);
    node.addEventListener("click", () => {
      stopPlay();
      playIndex = index;
      renderPose(frame.servos);
      highlight(index);
    });
    steps.appendChild(node);
  });
  replay.disabled = false;
  if (plan.frames[0]) renderPose(plan.frames[0].servos);
  play();
}

function renderSaved(plans) {
  saved.innerHTML = "";
  if (!plans.length) {
    saved.innerHTML = '<p class="empty">None yet.</p>';
    return;
  }
  for (const plan of plans) {
    const row = document.createElement("div");
    row.className = "entry";
    const open = document.createElement("button");
    open.className = "row";
    open.type = "button";
    const prompt = document.createElement("span");
    prompt.textContent = plan.prompt;
    const when = document.createElement("small");
    when.textContent = new Date(plan.created_at).toLocaleString();
    open.append(prompt, when);
    open.addEventListener("click", () => showPlan(plan));
    const remove = document.createElement("button");
    remove.className = "danger";
    remove.type = "button";
    remove.textContent = "Delete";
    remove.addEventListener("click", async () => {
      await api(`/api/plans/${plan.id}`, { method: "DELETE" });
      await refreshPlans();
    });
    row.append(open, remove);
    saved.appendChild(row);
  }
}

async function refreshPlans() {
  const data = await api("/api/plans");
  renderSaved(data.plans);
}

function renderUsage(user) {
  who.textContent = user.email;
  usage.textContent = `${user.usage_count} API call${user.usage_count === 1 ? "" : "s"} on this account. ${user.plan_count} saved plan${user.plan_count === 1 ? "" : "s"}.`;
  recent.innerHTML = "";
  for (const row of user.recent_usage || []) {
    const item = document.createElement("li");
    item.textContent = `${row.method} ${row.endpoint} → ${row.status_code}`;
    recent.appendChild(item);
  }
  document.querySelector("#admin-link").hidden = user.role !== "admin";
}

document.querySelector("#plan-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  planError.textContent = "";
  const button = event.target.querySelector("button");
  button.disabled = true;
  try {
    const prompt = new FormData(event.target).get("prompt");
    const result = await api("/api/plans", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    });
    showPlan(result.plan);
    const me = await api("/api/auth/me");
    renderUsage(me.user);
    await refreshPlans();
  } catch (error) {
    planError.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

replay.addEventListener("click", play);

const camera = document.querySelector("#camera");
const cameraStart = document.querySelector("#camera-start");
const cameraRead = document.querySelector("#camera-read");
const cameraError = document.querySelector("#camera-error");

cameraStart.addEventListener("click", async () => {
  cameraError.textContent = "";
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: 640, height: 480 },
      audio: false,
    });
    camera.srcObject = stream;
    camera.hidden = false;
    cameraRead.disabled = false;
    cameraStart.textContent = "Camera on";
  } catch (error) {
    cameraError.textContent = "The browser did not allow the camera.";
  }
});

async function captureClip() {
  const canvas = document.createElement("canvas");
  canvas.width = 288;
  canvas.height = 288;
  const context = canvas.getContext("2d");
  const frames = [];
  for (let index = 0; index < 8; index += 1) {
    const side = Math.min(camera.videoWidth, camera.videoHeight);
    const sx = (camera.videoWidth - side) / 2;
    const sy = (camera.videoHeight - side) / 2;
    context.drawImage(camera, sx, sy, side, side, 0, 0, 288, 288);
    frames.push(canvas.toDataURL("image/jpeg", 0.72));
    await new Promise((resolve) => setTimeout(resolve, 120));
  }
  return frames;
}

cameraRead.addEventListener("click", async () => {
  cameraError.textContent = "";
  if (!camera.videoWidth) {
    cameraError.textContent = "Wait for the camera picture, then try again.";
    return;
  }
  cameraRead.disabled = true;
  cameraRead.textContent = "Reading the clip…";
  try {
    const frames = await captureClip();
    const result = await api("/api/plans/mimic", {
      method: "POST",
      body: JSON.stringify({ frames }),
    });
    showPlan(result.plan);
    const me = await api("/api/auth/me");
    renderUsage(me.user);
    await refreshPlans();
  } catch (error) {
    cameraError.textContent = error.message;
  } finally {
    cameraRead.disabled = false;
    cameraRead.textContent = "Read my move";
  }
});

document.querySelector("#logout").addEventListener("click", async () => {
  await api("/api/auth/logout", { method: "POST" });
  window.location.href = "index.html";
});

api("/api/model")
  .then((model) => {
    if (model.loaded) {
      modelNote.textContent = `Local model ${model.name}. Weights are read from backend/models.`;
    }
  })
  .catch(() => {});

api("/api/auth/me")
  .then(async (result) => {
    renderUsage(result.user);
    await refreshPlans();
  })
  .catch(() => {
    window.location.href = "index.html";
  });
