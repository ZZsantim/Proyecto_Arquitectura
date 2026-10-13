const loginPanel = document.querySelector("#login-panel");
const recordPanel = document.querySelector("#record-panel");
const loginForm = document.querySelector("#login-form");
const searchForm = document.querySelector("#search-form");
const loginMessage = document.querySelector("#login-message");
const searchMessage = document.querySelector("#search-message");
const recordContent = document.querySelector("#record-content");
const logoutButton = document.querySelector("#logout-button");
let token = null;
let currentVehicleId = null;

function message(element, text, success = false) {
  element.textContent = text;
  element.classList.toggle("success", success);
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}

function addDefinition(list, label, value) {
  list.append(element("dt", label), element("dd", value || "No registrado"));
}

function addEditableField(form, labelText, name, value, maxLength, multiline = false) {
  const label = element("label", labelText);
  label.htmlFor = name;
  const field = element(multiline ? "textarea" : "input");
  field.id = name;
  field.name = name;
  field.maxLength = maxLength;
  field.value = value || "";
  form.append(label, field);
}

function renderTechnicalRecord(record) {
  recordContent.replaceChildren();
  currentVehicleId = record.id;

  const title = element(
    "h2",
    `${record.vehicle_type} · ${record.serial_number}`,
    "record-heading",
  );
  recordContent.append(title);
  if (record.make_model) recordContent.append(element("p", record.make_model, "muted"));

  const grid = element("div", undefined, "record-grid");
  const batteryCard = element("section", undefined, "data-card");
  batteryCard.append(element("h3", "Batería"));
  const battery = element("dl");
  const batteryData = record.battery || {};
  addDefinition(battery, "Voltaje", batteryData.voltage);
  addDefinition(battery, "Amperaje", batteryData.amperage);
  addDefinition(battery, "Capacidad", batteryData.capacity);
  addDefinition(battery, "Tipo de celdas", batteryData.cell_type);
  addDefinition(battery, "Notas técnicas", batteryData.technical_notes);
  batteryCard.append(battery);

  const controllerCard = element("section", undefined, "data-card");
  controllerCard.append(element("h3", "Controlador"));
  const controller = element("dl");
  const controllerData = record.controller || {};
  addDefinition(controller, "Modelo", controllerData.model);
  addDefinition(controller, "Firmware", controllerData.firmware);
  addDefinition(controller, "Modificaciones", controllerData.modifications);
  controllerCard.append(controller);
  grid.append(batteryCard, controllerCard);
  recordContent.append(grid);

  const editSpecifications = element("details", undefined, "record-heading");
  editSpecifications.append(element("summary", "Registrar/editar especificaciones"));
  const specificationsForm = element("form", undefined, "specification-form");
  specificationsForm.setAttribute(
    "aria-label",
    "Actualizar especificaciones de batería y controlador",
  );
  specificationsForm.append(element("h3", "Batería"));
  addEditableField(specificationsForm, "Voltaje", "battery-voltage", batteryData.voltage, 80);
  addEditableField(
    specificationsForm,
    "Amperaje",
    "battery-amperage",
    batteryData.amperage,
    80,
  );
  addEditableField(
    specificationsForm,
    "Capacidad",
    "battery-capacity",
    batteryData.capacity,
    80,
  );
  addEditableField(
    specificationsForm,
    "Tipo de celdas",
    "battery-cell-type",
    batteryData.cell_type,
    120,
  );
  addEditableField(
    specificationsForm,
    "Notas técnicas",
    "battery-technical-notes",
    batteryData.technical_notes,
    4000,
    true,
  );
  specificationsForm.append(element("h3", "Controlador"));
  addEditableField(
    specificationsForm,
    "Modelo",
    "controller-model",
    controllerData.model,
    120,
  );
  addEditableField(
    specificationsForm,
    "Firmware",
    "controller-firmware",
    controllerData.firmware,
    120,
  );
  addEditableField(
    specificationsForm,
    "Modificaciones",
    "controller-modifications",
    controllerData.modifications,
    4000,
    true,
  );
  const saveSpecifications = element("button", "Guardar especificaciones", "button");
  saveSpecifications.type = "submit";
  specificationsForm.append(saveSpecifications);
  specificationsForm.addEventListener("submit", updateSpecifications);
  editSpecifications.append(specificationsForm);
  recordContent.append(editSpecifications);

  const historySection = element("section", undefined, "record-heading");
  historySection.append(element("h3", "Historial de reparaciones"));
  if (record.repairs.length === 0) {
    historySection.append(element("p", "No hay reparaciones registradas.", "muted"));
  } else {
    const history = element("ul", undefined, "history-list");
    for (const repair of record.repairs) {
      const item = element("li", undefined, "history-item");
      item.append(element("strong", `${repair.service_date} · ${repair.summary}`));
      if (repair.technical_details) item.append(element("p", repair.technical_details));
      history.append(item);
    }
    historySection.append(history);
  }
  recordContent.append(historySection);

  const observationsSection = element("section", undefined, "record-heading");
  observationsSection.append(element("h3", "Observaciones técnicas"));
  const form = element("form", undefined, "observation-form");
  const label = element("label", "Nueva observación (texto plano, máximo 2.000 caracteres)");
  label.htmlFor = "observation-content";
  const textarea = element("textarea");
  textarea.id = "observation-content";
  textarea.name = "content";
  textarea.maxLength = 2000;
  textarea.required = true;
  const submit = element("button", "Guardar observación", "button");
  submit.type = "submit";
  form.append(label, textarea, submit);
  form.addEventListener("submit", saveObservation);
  observationsSection.append(form);

  const observations = element("ul", undefined, "history-list");
  observations.setAttribute("aria-label", "Observaciones existentes");
  for (const observation of record.observations) {
    const item = element("li", undefined, "history-item");
    item.append(
      element(
        "strong",
        `${new Date(observation.created_at).toLocaleString("es-CO")} · ${observation.author_username}`,
      ),
      element("p", observation.content),
    );
    observations.append(item);
  }
  observationsSection.append(observations);
  recordContent.append(observationsSection);
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body) headers.set("Content-Type", "application/json");
  return fetch(path, { ...options, headers, cache: "no-store" });
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  message(loginMessage, "Verificando acceso…");
  const formData = new FormData(loginForm);
  try {
    const response = await request("/api/v1/auth/token", {
      method: "POST",
      body: JSON.stringify({
        username: formData.get("username"),
        password: formData.get("password"),
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "No fue posible iniciar sesión.");
    token = data.access_token;
    loginPanel.hidden = true;
    recordPanel.hidden = false;
    logoutButton.hidden = false;
    message(loginMessage, "");
    document.querySelector("#serial-number").focus();
  } catch (error) {
    message(loginMessage, error.message || "No fue posible conectar con la API.");
  }
});

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  message(searchMessage, "Buscando expediente…");
  recordContent.replaceChildren();
  const serial = document.querySelector("#serial-number").value.trim();
  try {
    const response = await request(
      `/api/v1/technical-records/by-serial/${encodeURIComponent(serial)}`,
    );
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "No fue posible consultar el expediente.");
    renderTechnicalRecord(data);
    message(searchMessage, "Expediente cargado.", true);
  } catch (error) {
    message(searchMessage, error.message || "No fue posible conectar con la API.");
  }
});

async function saveObservation(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const textarea = form.elements.namedItem("content");
  const button = form.querySelector("button");
  button.disabled = true;
  message(searchMessage, "Guardando observación…");
  try {
    const response = await request(
      `/api/v1/technical-records/${encodeURIComponent(currentVehicleId)}/observations`,
      { method: "POST", body: JSON.stringify({ content: textarea.value }) },
    );
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "No fue posible guardar la observación.");
    message(searchMessage, "Observación guardada.", true);
    const serial = document.querySelector("#serial-number").value;
    const refresh = await request(
      `/api/v1/technical-records/by-serial/${encodeURIComponent(serial)}`,
    );
    const record = await refresh.json();
    if (!refresh.ok) throw new Error(record.detail || "No fue posible actualizar el expediente.");
    renderTechnicalRecord(record);
  } catch (error) {
    message(searchMessage, error.message || "No fue posible conectar con la API.");
    button.disabled = false;
  }
}

async function updateSpecifications(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  const button = form.querySelector("button");
  button.disabled = true;
  message(searchMessage, "Guardando especificaciones…");
  const valueOrNull = (name) => {
    const value = formData.get(name).trim();
    return value || null;
  };
  try {
    const response = await request(
      `/api/v1/technical-records/${encodeURIComponent(currentVehicleId)}/specifications`,
      {
        method: "PUT",
        body: JSON.stringify({
          battery: {
            voltage: valueOrNull("battery-voltage"),
            amperage: valueOrNull("battery-amperage"),
            capacity: valueOrNull("battery-capacity"),
            cell_type: valueOrNull("battery-cell-type"),
            technical_notes: valueOrNull("battery-technical-notes"),
          },
          controller: {
            model: valueOrNull("controller-model"),
            firmware: valueOrNull("controller-firmware"),
            modifications: valueOrNull("controller-modifications"),
          },
        }),
      },
    );
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "No fue posible actualizar las especificaciones.");
    }
    renderTechnicalRecord(data);
    message(searchMessage, "Especificaciones actualizadas.", true);
  } catch (error) {
    message(searchMessage, error.message || "No fue posible conectar con la API.");
    button.disabled = false;
  }
}

logoutButton.addEventListener("click", () => {
  token = null;
  currentVehicleId = null;
  recordContent.replaceChildren();
  recordPanel.hidden = true;
  logoutButton.hidden = true;
  loginPanel.hidden = false;
  loginForm.reset();
  message(loginMessage, "Sesión cerrada.", true);
  document.querySelector("#username").focus();
});
