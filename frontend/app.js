import { clearGeminiChat, createGeminiChatView } from "./gemini-chat.js?v=flash-36";

const $ = (selector) => document.querySelector(selector);
const view = $("#view");
const dialog = $("#dialog");
const form = $("#editor");
const pageSize = 20;
const triage = ["critical", "urgent", "less_urgent", "non_urgent"];
const outcomes = ["discharged", "admitted", "transferred"];
const caseStatuses = ["waiting", "in_treatment", ...outcomes];
const appointmentStatuses = ["scheduled", "completed", "cancelled"];
const roles = ["staff", "admin"];
const openStatuses = ["waiting", "in_treatment"];

function field(name, label, type = "text", required = false, options) {
  return { name, label, type, required, options };
}

const patient = field("patient_id", "Patient", "reference", true, "patients");
const doctor = field("doctor_id", "Doctor", "reference", true, "doctors");
const status = field("status", "Status", "select", true, appointmentStatuses);
const caseFields = [
  { ...patient, required: false },
  field("patient_description", "Description if patient is unknown", "textarea"),
  field("complaint", "Presenting complaint", "textarea", true),
  field("triage_level", "Triage priority", "select", true, triage),
];
const accountFields = [
  field("username", "Username", "text", true),
  field("password", "Password", "password", true),
];
const registrationFields = [...accountFields, field("full_name", "Full name")];

const pages = {
  overview: { title: "Operations overview", description: "Monitor appointments and emergency activity across the hospital." },
  "gemini-chat": {
    title: "Gemini chat",
    description: "Send test prompts to Gemini 3.6 Flash and inspect its responses.",
  },
  patients: {
    title: "Patients", description: "Find and manage patient records.", create: "Add patient",
    columns: [["name", "Patient"], ["phone", "Phone"], ["email", "Email"], ["blood_group", "Blood group"]],
    filters: [field("name", "Search by name", "search")],
    fields: [
      field("name", "Full name", "text", true), field("date_of_birth", "Date of birth", "date"),
      field("gender", "Gender", "select", false, ["Male", "Female", "Other"]), field("phone", "Phone", "tel"),
      field("email", "Email", "email"), field("blood_group", "Blood group", "select", false, ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
      field("address", "Address", "textarea"),
    ],
  },
  appointments: {
    title: "Appointments", description: "Schedule visits and manage bookings.", create: "Book appointment",
    columns: [["patient_name", "Patient"], ["doctor_name", "Doctor"], ["appointment_time", "Appointment time"], ["status", "Status"]],
    filters: [field("date", "Date", "date"), { ...status, required: false }],
    fields: [patient, doctor, field("appointment_time", "Appointment time", "datetime-local", true),
      field("reason", "Visit reason", "textarea"), status],
  },
  emergency: {
    title: "Emergency", description: "Review the triage queue and manage emergency cases.", create: "Register case",
    columns: [["patient", "Patient"], ["triage_level", "Triage"], ["status", "Status"], ["doctor_name", "Assigned doctor"], ["arrived_at", "Arrived"]],
    filters: [field("scope", "View", "select", true, [["queue", "Waiting queue"], ["all", "All cases"]]),
      field("status", "Status", "select", false, caseStatuses), field("triage_level", "Triage", "select", false, triage)],
    fields: caseFields,
  },
  doctors: {
    title: "Doctors", description: "Manage clinicians and their department assignments.", create: "Add doctor",
    columns: [["name", "Doctor"], ["specialization", "Specialization"], ["department", "Department"], ["email", "Email"]],
    fields: [field("name", "Full name", "text", true), field("specialization", "Specialization", "text", true),
      field("department_id", "Department", "reference", false, "departments"), field("phone", "Phone", "tel"), field("email", "Email", "email")],
  },
  departments: {
    title: "Departments", description: "Manage hospital departments.", create: "Add department",
    columns: [["name", "Department"], ["description", "Description"]],
    fields: [field("name", "Department name", "text", true), field("description", "Description", "textarea", true)],
  },
  staff: {
    title: "Staff accounts", description: "Manage staff and administrator access.", create: "Create account",
    columns: [["username", "Username"], ["full_name", "Full name"], ["role", "Role"]],
    fields: [...registrationFields, field("role", "Role", "select", true, roles)],
  },
};

let token = sessionStorage.getItem("medops-token") || "";
let user = null;
let activePage = "";
let offset = 0;
let filters = {};
let renderVersion = 0;
let dialogVersion = 0;
let submitAction;

function node(tag, content, className) {
  const element = document.createElement(tag);
  if (content !== undefined) element.textContent = content;
  if (className) element.className = className;
  return element;
}

function button(label, action, style = "secondary") {
  const element = node("button", label, `button ${style}`);
  element.type = "button";
  element.addEventListener("click", action);
  return element;
}

function link(label, href, className) {
  const element = node("a", label, className);
  element.href = href;
  return element;
}

function titleCase(value) {
  return String(value).replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());
}

function setSession(nextToken, nextUser) {
  token = nextToken;
  user = nextUser;
  if (!nextUser) clearGeminiChat();
  if (token) sessionStorage.setItem("medops-token", token);
  else sessionStorage.removeItem("medops-token");
  $("#identity").textContent = user ? `${user.full_name || user.username} · ${titleCase(user.role)}` : "";
  $("#account-button").textContent = user ? "Sign out" : "Sign in";
  $("#staff-link").hidden = user?.role !== "admin";
  updateCreateButton();
}

async function request(path, { method = "GET", body } = {}) {
  const headers = { Accept: "application/json" };
  const sentToken = token;
  if (sentToken) headers.Authorization = `Bearer ${sentToken}`;
  if (body instanceof URLSearchParams) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }
  const response = await fetch(path, { method, headers, body });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && sentToken && token === sentToken && path !== "/auth/login") {
      setSession("", null);
      if (activePage) void renderPage();
      throw new Error("Your session expired. Sign in again to continue.");
    }
    const detail = Array.isArray(data?.detail)
      ? data.detail.map(({ loc, msg }) => `${loc.slice(1).join(".") || "Request"}: ${msg}`).join(" · ")
      : data?.detail;
    throw new Error(detail || `The API returned HTTP ${response.status}.`);
  }
  return data;
}

function list(path, params = {}) {
  const query = new URLSearchParams(params);
  return request(`${path}?${query}`);
}

async function getAll(resource) {
  const rows = [];
  while (true) {
    const batch = await list(`/${resource}/`, { limit: 100, offset: rows.length });
    rows.push(...batch);
    if (batch.length < 100) return rows;
  }
}

function notify(message, error = false) {
  const notice = $("#notice");
  notice.textContent = message;
  notice.classList.toggle("error", error);
  notice.hidden = !message;
}

function dateLabel(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function displayValue(key, row) {
  if (key === "patient") return row.patient_name || row.patient_description || "Unknown patient";
  if (key === "department") return row.department ?? "—";
  if (key === "wait_minutes") return `${row[key]} min`;
  if (key.endsWith("_at") || key === "appointment_time") return dateLabel(row[key]);
  return row[key] ?? "—";
}

function table(rows, columns, actions) {
  if (!rows.length) return node("p", "No records found.", "empty");
  const wrapper = node("div", undefined, "table-scroll");
  wrapper.tabIndex = 0;
  wrapper.setAttribute("aria-label", "Records table");
  wrapper.setAttribute("role", "region");
  const grid = node("table");
  const header = grid.createTHead().insertRow();
  for (const [, label] of columns) {
    const cell = node("th", label);
    cell.scope = "col";
    header.append(cell);
  }
  if (actions) {
    const cell = node("th", "Actions");
    cell.scope = "col";
    header.append(cell);
  }
  const body = grid.createTBody();
  for (const row of rows) {
    const tr = body.insertRow();
    for (const [key] of columns) {
      const cell = tr.insertCell();
      const value = displayValue(key, row);
      if ((key === "status" || key === "triage_level") && row[key]) {
        cell.append(node("span", titleCase(value), `badge ${row[key]}`));
      } else {
        cell.textContent = value;
      }
    }
    if (actions) tr.insertCell().append(actions(row));
  }
  wrapper.append(grid);
  return wrapper;
}

function panel(title, caption, target, content) {
  const section = node("section", undefined, "panel");
  const heading = node("div", undefined, "panel-heading");
  const copy = node("div");
  copy.append(node("h2", title), node("p", caption));
  heading.append(copy, link("View all", `#${target}`));
  section.append(heading, content);
  return section;
}

function dateKey(date) {
  return [date.getFullYear(), date.getMonth() + 1, date.getDate()]
    .map((part) => String(part).padStart(2, "0")).join("-");
}

async function overview() {
  const now = new Date();
  const today = dateKey(now);
  const [appointments, waiting, treatment, doctors] = await Promise.all([
    list("/appointments/", { date: today, limit: 100 }),
    list("/emergency/queue", { limit: 100 }),
    list("/emergency/", { status: "in_treatment", limit: 100 }),
    list("/doctors/", { limit: 100 }),
  ]);
  const fragment = document.createDocumentFragment();
  const hero = node("section", undefined, "hero");
  const copy = node("div");
  copy.append(node("h2", "Today at the hospital"),
    node("p", new Intl.DateTimeFormat(undefined, { dateStyle: "full" }).format(now)),
    link("Open emergency queue", "#emergency", "button secondary"));
  hero.append(copy);

  const metrics = node("div", undefined, "metrics");
  const summary = [
    ["▤", "Today's appointments", appointments.length, `appointments?date=${today}`],
    ["✚", "Waiting in emergency", waiting.length, "emergency"],
    ["◴", "Cases in treatment", treatment.length, "emergency?scope=all&status=in_treatment"],
    ["♙", "Registered doctors", doctors.length, "doctors"],
  ];
  for (const [icon, label, count, target] of summary) {
    const card = link(undefined, `#${target}`, "metric");
    const mark = node("span", icon, "metric-icon");
    mark.setAttribute("aria-hidden", "true");
    card.append(mark, node("small", label), node("strong", count === 100 ? "100+" : count));
    metrics.append(card);
  }

  const grid = node("div", undefined, "dashboard-grid");
  grid.append(
    panel("Emergency queue", "Ordered by triage priority and arrival", "emergency",
      table(waiting.slice(0, 5), [["patient", "Patient"], ["triage_level", "Triage"], ["wait_minutes", "Wait"]])),
    panel("Today's appointments", "Scheduled visits and appointment status", `appointments?date=${today}`,
      table(appointments.slice(0, 5), [["patient_name", "Patient"], ["appointment_time", "Time"], ["status", "Status"]])),
  );
  fragment.append(hero, metrics, grid);
  return fragment;
}

function inputField(spec, value, options = spec.options, emptyLabel = "Select…") {
  const label = node("label", spec.label, "field");
  const isSelect = Array.isArray(options);
  const input = node(isSelect ? "select" : spec.type === "textarea" ? "textarea" : "input");
  if (isSelect) {
    input.add(new Option(emptyLabel, ""));
    for (const option of options) {
      const [key, caption] = Array.isArray(option) ? option : [option, titleCase(option)];
      input.add(new Option(caption, key));
    }
  } else if (input.tagName === "INPUT") {
    input.type = spec.type;
    if (spec.type === "password") input.autocomplete = "new-password";
  }
  input.name = spec.name;
  input.required = spec.required;
  input.value = value ?? "";
  label.append(input);
  return label;
}

function filterForm(definitions) {
  const bar = node("form", undefined, "filters");
  for (const spec of definitions) {
    const control = inputField(spec, filters[spec.name], spec.options, "Any");
    if (activePage === "emergency" && spec.name !== "scope") {
      control.querySelector("select").disabled = filters.scope === "queue";
    }
    bar.append(control);
  }
  const apply = node("button", "Apply filters", "button secondary");
  const reset = button("Reset", () => setPageFilters({}));
  bar.append(apply, reset);
  bar.addEventListener("change", (event) => {
    if (event.target.name === "scope") setPageFilters({ scope: event.target.value || "queue" });
  });
  bar.addEventListener("submit", (event) => {
    event.preventDefault();
    const selected = Object.fromEntries([...new FormData(bar)].filter(([, value]) => value.trim()));
    setPageFilters(selected);
  });
  return bar;
}

function setPageFilters(nextFilters) {
  const query = new URLSearchParams(nextFilters);
  const target = `#${activePage}${query.size ? `?${query}` : ""}`;
  if (location.hash === target) {
    offset = 0;
    void renderPage();
  } else {
    location.hash = target;
  }
}

function pagination(hasMore, count) {
  const row = node("div", undefined, "pagination");
  const move = (step) => {
    offset += step * pageSize;
    void renderPage();
  };
  const previous = button("Previous", () => move(-1));
  const next = button("Next", () => move(1));
  previous.disabled = offset === 0;
  next.disabled = !hasMore;
  row.append(node("span", count ? `${offset + 1}–${offset + count}` : "0 records"), previous, next);
  return row;
}

async function recordList(page, start, selectedFilters) {
  if (page === "staff" && user?.role !== "admin") {
    return node("p", "Sign in as an administrator to manage staff accounts.", "panel empty");
  }
  const config = pages[page];
  const { scope, ...params } = selectedFilters;
  const queue = page === "emergency" && scope === "queue";
  let rows;
  if (page === "staff") {
    rows = (await request("/auth/users")).slice(start, start + pageSize + 1);
  } else {
    rows = await list(queue ? "/emergency/queue" : `/${page}/`, {
      ...(queue ? {} : params), limit: pageSize + 1, offset: start,
    });
  }
  const hasMore = rows.length > pageSize;
  rows = rows.slice(0, pageSize);
  if (page === "doctors") {
    const departmentIds = [...new Set(rows.map((row) => row.department_id).filter(Boolean))];
    const departments = await Promise.all(departmentIds.map((id) => request(`/departments/${id}`)));
    const names = new Map(departments.map(({ id, name }) => [id, name]));
    rows = rows.map((row) => ({ ...row, department: names.get(row.department_id) }));
  }
  const section = node("section", undefined, "panel");
  if (config.filters) section.append(filterForm(config.filters));
  section.append(table(rows, config.columns, (row) => rowActions(page, row)), pagination(hasMore, rows.length));
  return section;
}

function updateCreateButton() {
  const create = $("#create");
  const label = pages[activePage]?.create;
  create.textContent = label || "";
  create.hidden = !label || !user || (activePage === "staff" && user.role !== "admin");
}

async function renderPage() {
  const version = ++renderVersion;
  const config = pages[activePage];
  $("#page-title").textContent = config.title;
  $("#page-description").textContent = config.description;
  $("#breadcrumb").textContent = activePage === "staff" ? "Staff accounts" : titleCase(activePage);
  document.title = `${config.title} | MedOps`;
  for (const anchor of document.querySelectorAll("nav a")) {
    if (anchor.hash === `#${activePage}`) anchor.setAttribute("aria-current", "page");
    else anchor.removeAttribute("aria-current");
  }
  updateCreateButton();
  view.setAttribute("aria-busy", "true");
  view.replaceChildren(node("p", "Loading…", "panel empty"));
  try {
    const content = activePage === "overview"
      ? await overview()
      : activePage === "gemini-chat"
        ? createGeminiChatView({
          request,
          user,
          onSignIn: () => {
            if (user) {
              setSession("", null);
              changedRecords("Signed out. Sign in with an administrator account to use Gemini chat.");
            }
            accountDialog();
          },
        })
        : await recordList(activePage, offset, filters);
    if (version === renderVersion) view.replaceChildren(content);
  } catch (error) {
    if (version === renderVersion) {
      view.replaceChildren(node("p", `Unable to load this view. ${error.message}`, "panel empty"));
    }
  } finally {
    if (version === renderVersion) view.removeAttribute("aria-busy");
  }
}

function navigate() {
  const [route, query] = location.hash.slice(1).split("?");
  activePage = Object.hasOwn(pages, route) ? route : "overview";
  const search = new URLSearchParams(query);
  const defaults = activePage === "emergency" ? { scope: "queue" } : {};
  filters = { ...defaults };
  for (const spec of pages[activePage].filters || []) {
    const value = search.get(spec.name);
    if (value && (!spec.options || spec.options.some((option) => (Array.isArray(option) ? option[0] : option) === value))) {
      filters[spec.name] = value;
    }
  }
  offset = 0;
  notify("");
  void renderPage();
}

function openDialog(title, label, action) {
  const version = ++dialogVersion;
  $("#dialog-title").textContent = title;
  $("#dialog-fields").replaceChildren();
  $("#form-error").hidden = true;
  $("#submit").textContent = label || "";
  $("#submit").hidden = !label;
  $("#submit").disabled = false;
  submitAction = action;
  if (!dialog.open) dialog.showModal();
  return version;
}

function showFormError(message) {
  $("#form-error").textContent = message;
  $("#form-error").hidden = false;
}

async function collectOptions(spec) {
  if (spec.type !== "reference") return spec.options;
  let records;
  if (spec.options === "emergency-doctors") {
    const departments = await getAll("departments");
    const department = departments.find(({ name }) => name === "Emergency Medicine");
    records = department ? await request(`/departments/${department.id}/doctors`) : [];
  } else {
    records = await getAll(spec.options);
  }
  return records.map(({ id, name }) => [id, `${name} (#${id})`]);
}

async function editDialog({ title, label = "Save", fields, values = {}, save, extraControl }) {
  const version = openDialog(title, label);
  const area = $("#dialog-fields");
  $("#submit").disabled = true;
  const needsReferences = fields.some((spec) => spec.type === "reference");
  if (needsReferences) area.append(node("p", "Loading available records…"));
  try {
    const choices = await Promise.all(fields.map(collectOptions));
    if (version !== dialogVersion || !dialog.open) return;
    area.replaceChildren();
    fields.forEach((spec, index) => {
      let initial = values[spec.name];
      if (spec.type === "datetime-local") initial = initial?.slice(0, 16);
      const selected = choices[index];
      const control = inputField(spec, initial, selected, spec.required ? "Select…" : "None");
      const input = control.lastElementChild;
      if (spec.name === "username") input.autocomplete = "username";
      if (spec.name === "password" && label === "Sign in") input.autocomplete = "current-password";
      area.append(control);
    });
    if (extraControl) area.append(extraControl);
    const initial = new FormData(form);
    submitAction = async () => {
      const inputs = new FormData(form);
      const data = {};
      const changes = {};
      for (const spec of fields) {
        const raw = inputs.get(spec.name) ?? "";
        const value = spec.type === "password" ? raw : raw.trim();
        if (spec.required && !value) throw new Error(`${spec.label} is required.`);
        data[spec.name] = value ? (spec.type === "reference" ? Number(value) : value) : null;
        if (raw !== initial.get(spec.name)) changes[spec.name] = data[spec.name];
      }
      await save(data, changes);
    };
    $("#submit").disabled = false;
    const firstControl = area.querySelector("input, select, textarea");
    firstControl?.focus();
  } catch (error) {
    if (version === dialogVersion && dialog.open) {
      area.replaceChildren();
      showFormError(`Unable to load available records. ${error.message}`);
    }
  }
}

function detailDialog(page, row) {
  openDialog(page === "emergency" ? `Emergency case #${row.id}` : `Record #${row.id}`);
  const details = node("dl", undefined, "detail");
  const labels = new Map([...pages[page].fields.map((spec) => [spec.name, spec.label]), ...pages[page].columns]);
  for (const [key] of Object.entries(row)) {
    details.append(node("dt", labels.get(key) || titleCase(key)),
      node("dd", displayValue(key, row)));
  }
  $("#dialog-fields").append(details);
}

function recordPath(page, row) {
  if (page === "staff") return row ? `/auth/users/${row.id}` : "/auth/register";
  return row ? `/${page}/${row.id}` : `/${page}/`;
}

function changedRecords(message) {
  notify(message);
  void renderPage();
}

function openRecordEditor(page, row) {
  const config = pages[page];
  const defaults = { appointments: { status: "scheduled" }, staff: { role: "staff" } };
  editDialog({
    title: row ? (page === "emergency" ? "Edit emergency case" : `Edit record #${row.id}`) : config.create,
    label: row ? "Save changes" : config.create,
    fields: config.fields,
    values: row || defaults[page],
    save: async (data, changes) => {
      if (page === "emergency" && !data.patient_id && !data.patient_description) {
        throw new Error("Select a patient or provide a description for an unknown patient.");
      }
      if (row && !Object.keys(changes).length) return;
      const clearFields = row && Object.values(changes).includes(null);
      if (clearFields && page === "emergency") {
        throw new Error("The API can replace patient details on an open case. Fill in the field to change its value.");
      }
      // PATCH leaves null fields intact. PUT can clear optional fields.
      const method = row ? (clearFields ? "PUT" : "PATCH") : "POST";
      await request(recordPath(page, row), { method, body: method === "PATCH" ? changes : data });
      changedRecords(row ? "Changes saved." : "Record created.");
    },
  });
}

function emergencyAction(row, action) {
  const assigning = action === "assign";
  const label = assigning ? (row.doctor_id ? "Reassign doctor" : "Assign doctor") : "Close case";
  const fields = assigning
    ? [{ ...doctor, options: "emergency-doctors" }]
    : [field("outcome", "Outcome", "select", true, outcomes), field("notes", "Closing notes", "textarea")];
  editDialog({
    title: label,
    label,
    fields,
    values: row,
    save: async (body) => {
      await request(`/emergency/${row.id}/${action}`, { method: "PATCH", body });
      if (assigning && filters.scope === "queue") offset = 0;
      changedRecords(assigning ? "Doctor assigned." : "Case closed.");
    },
  });
}

function confirmDelete(page, row) {
  openDialog(`Delete record #${row.id}?`, "Delete record", async () => {
    await request(recordPath(page, row), { method: "DELETE" });
    offset = 0;
    changedRecords("Record deleted.");
  });
  $("#dialog-fields").append(node("p",
    page === "patients" || page === "doctors"
      ? "Deleting this record also deletes its appointments. This action is permanent."
      : "This action is permanent."));
  $("#submit").classList.add("danger");
}

function rowActions(page, row) {
  const actions = node("div", undefined, "table-actions");
  actions.append(button("Details", () => detailDialog(page, row)));
  const editable = page !== "staff" && (page !== "emergency" || openStatuses.includes(row.status));
  if (user && editable) actions.append(button("Edit", () => openRecordEditor(page, row)));
  if (user && page === "emergency" && editable) {
    actions.append(button(row.doctor_id ? "Reassign" : "Assign", () => emergencyAction(row, "assign")));
    if (row.status === "in_treatment") actions.append(button("Close case", () => emergencyAction(row, "close")));
  }
  if (user?.role === "admin" && (page !== "staff" || row.id !== user.id)) {
    actions.append(button("Delete", () => confirmDelete(page, row), "danger"));
  }
  return actions;
}

async function signIn(credentials) {
  const { access_token: nextToken } = await request("/auth/login", {
    method: "POST", body: new URLSearchParams(credentials),
  });
  token = nextToken;
  try {
    const account = await request("/auth/me");
    setSession(nextToken, account);
    changedRecords("Signed in.");
  } catch (error) {
    setSession("", null);
    throw error;
  }
}

function accountDialog() {
  const setup = button("Set up first admin", () => {
    editDialog({
      title: "Set up first admin",
      label: "Create admin",
      fields: registrationFields,
      save: async ({ username, password, full_name }) => {
        await request("/auth/register", { method: "POST", body: { username, password, full_name } });
        await signIn({ username, password });
      },
    });
  });
  setup.classList.add("setup-button");
  editDialog({ title: "Staff sign-in", label: "Sign in", fields: accountFields, save: signIn, extraControl: setup });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!submitAction || $("#submit").disabled) return;
  const version = dialogVersion;
  $("#submit").disabled = true;
  $("#cancel-dialog").disabled = true;
  $("#close-dialog").disabled = true;
  $("#form-error").hidden = true;
  try {
    await submitAction();
    if (version === dialogVersion) dialog.close();
  } catch (error) {
    if (version === dialogVersion) showFormError(error.message);
  } finally {
    $("#submit").disabled = false;
    $("#cancel-dialog").disabled = false;
    $("#close-dialog").disabled = false;
  }
});

dialog.addEventListener("cancel", (event) => {
  if ($("#close-dialog").disabled) event.preventDefault();
});

dialog.addEventListener("close", () => {
  dialogVersion += 1;
  $("#submit").classList.remove("danger");
  $("#dialog-fields").replaceChildren();
  submitAction = undefined;
});

$("#close-dialog").addEventListener("click", () => dialog.close());
$("#cancel-dialog").addEventListener("click", () => dialog.close());
$("#account-button").addEventListener("click", () => {
  if (user) {
    setSession("", null);
    changedRecords("Signed out.");
  } else {
    accountDialog();
  }
});
$("#create").addEventListener("click", () => openRecordEditor(activePage));
$("#refresh").addEventListener("click", () => {
  notify("");
  void renderPage();
});
$(".skip-link").addEventListener("click", (event) => {
  event.preventDefault();
  $("#content").focus();
});
window.addEventListener("hashchange", navigate);

async function start() {
  if (token) {
    $("#account-button").disabled = true;
    try {
      setSession(token, await request("/auth/me"));
    } catch {
      setSession("", null);
    } finally {
      $("#account-button").disabled = false;
    }
  }
  navigate();
}

void start();
