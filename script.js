const STORAGE_KEY = "advancedComplaintPortalDraftV2";

const complaintForm = document.getElementById("complaintForm");
const transactionTableBody = document.getElementById("transactionTableBody");
const evidenceTableBody = document.getElementById("evidenceTableBody");

const addTransactionBtn = document.getElementById("addTransactionBtn");
const addEvidenceBtn = document.getElementById("addEvidenceBtn");
const fillLastSenderBtn = document.getElementById("fillLastSenderBtn");
const saveDraftBtn = document.getElementById("saveDraftBtn");
const clearDraftBtn = document.getElementById("clearDraftBtn");
const resetFormBtn = document.getElementById("resetFormBtn");
const previewBtn = document.getElementById("previewBtn");

const totalAmountEl = document.getElementById("totalAmount");
const transactionCountEl = document.getElementById("transactionCount");
const reviewBox = document.getElementById("reviewBox");
const saveStatus = document.getElementById("saveStatus");
const messageBox = document.getElementById("messageBox");

const transactionRowTemplate = document.getElementById("transactionRowTemplate");
const evidenceRowTemplate = document.getElementById("evidenceRowTemplate");

let autoSaveTimer = null;

function init() {
  bindEvents();
  restoreDraft();

  if (!transactionTableBody.querySelector("tr")) addTransactionRow();
  if (!evidenceTableBody.querySelector("tr")) addEvidenceRow();

  updateTransactionSummary();
  updateRowNumbers();
  syncEvidenceTransactionOptions();
  renderReview();
}

function bindEvents() {
  addTransactionBtn.addEventListener("click", () => {
    addTransactionRow();
    updateTransactionSummary();
    updateRowNumbers();
    syncEvidenceTransactionOptions();
    scheduleAutoSave();
  });

  addEvidenceBtn.addEventListener("click", () => {
    addEvidenceRow();
    updateRowNumbers();
    scheduleAutoSave();
  });

  if (fillLastSenderBtn) {
    fillLastSenderBtn.addEventListener("click", reuseLastSenderDetails);
  }
  saveDraftBtn.addEventListener("click", saveDraft);
  clearDraftBtn.addEventListener("click", clearDraft);
  resetFormBtn.addEventListener("click", resetWholeForm);
  previewBtn.addEventListener("click", renderReview);

  complaintForm.addEventListener("input", () => {
    updateTransactionSummary();
    syncEvidenceTransactionOptions();
    renderReview();
    scheduleAutoSave();
  });

  complaintForm.addEventListener("change", (event) => {
    if (event.target.matches('input[name="evidenceFile[]"]')) {
      const fileBox = event.target.closest("td").querySelector(".file-name");
      if (fileBox) {
        const file = event.target.files && event.target.files[0] ? event.target.files[0].name : "";
        fileBox.textContent = file || "No file selected";
      }
    }

    updateTransactionSummary();
    syncEvidenceTransactionOptions();
    renderReview();
    scheduleAutoSave();
  });

  transactionTableBody.addEventListener("click", handleTransactionTableClick);
  evidenceTableBody.addEventListener("click", handleEvidenceTableClick);

  complaintForm.addEventListener("submit", handleSubmit);
}

function addTransactionRow(data = {}) {
  const fragment = transactionRowTemplate.content.cloneNode(true);
  const row = fragment.querySelector("tr");

  row.querySelector('input[name="transactionId[]"]').value = data.transactionId || "";
  row.querySelector('input[name="transactionDate[]"]').value = data.transactionDate || "";
  row.querySelector('input[name="transactionTime[]"]').value = data.transactionTime || "";
  row.querySelector('input[name="transactionAmount[]"]').value = data.transactionAmount || "";
  row.querySelector('input[name="senderBank[]"]').value = data.senderBank || "";
  row.querySelector('input[name="senderAccount[]"]').value = data.senderAccount || "";
  row.querySelector('input[name="receiverBank[]"]').value = data.receiverBank || "";
  row.querySelector('select[name="transactionMode[]"]').value = data.transactionMode || "";
  row.querySelector('input[name="transactionRemark[]"]').value = data.transactionRemark || "";

  transactionTableBody.appendChild(row);
  updateRowNumbers();
}

function addEvidenceRow(data = {}) {
  const fragment = evidenceRowTemplate.content.cloneNode(true);
  const row = fragment.querySelector("tr");

  row.querySelector('select[name="evidenceType[]"]').value = data.evidenceType || "";
  row.querySelector('input[name="evidenceDescription[]"]').value = data.evidenceDescription || "";

  evidenceTableBody.appendChild(row);
  syncEvidenceTransactionOptions();

  const refSelect = row.querySelector('select[name="evidenceTransactionRef[]"]');
  if (data.evidenceTransactionRef) {
    setSelectValueIfExists(refSelect, data.evidenceTransactionRef);
  }

  updateRowNumbers();
}

function handleTransactionTableClick(event) {
  event.preventDefault();
  event.stopPropagation();
  console.log("Transaction delete clicked:", event.target);
  const target = event.target;

  if (target.classList.contains("delete-transaction")) {
    target.closest("tr").remove();
    updateTransactionSummary();
    updateRowNumbers();
    syncEvidenceTransactionOptions();
    renderReview();
    saveDraft();
  }

  if (target.classList.contains("duplicate-transaction")) {
    const row = target.closest("tr");
    const data = {
      transactionId: "",
      transactionDate: row.querySelector('input[name="transactionDate[]"]').value,
      transactionTime: row.querySelector('input[name="transactionTime[]"]').value,
      transactionAmount: row.querySelector('input[name="transactionAmount[]"]').value,
      senderBank: row.querySelector('input[name="senderBank[]"]').value,
      senderAccount: row.querySelector('input[name="senderAccount[]"]').value,
      receiverBank: row.querySelector('input[name="receiverBank[]"]').value,
      transactionMode: row.querySelector('select[name="transactionMode[]"]').value,
      transactionRemark: row.querySelector('input[name="transactionRemark[]"]').value
    };

    addTransactionRow(data);
    updateTransactionSummary();
    updateRowNumbers();
    syncEvidenceTransactionOptions();
    renderReview();
    saveDraft();
  }
}

function handleEvidenceTableClick(event) {
  const target = event.target;

  // ✅ ONLY block delete button, NOT everything
  if (target.classList.contains("delete-evidence")) {
    event.preventDefault();
    event.stopPropagation();

    target.closest("tr").remove();
    updateRowNumbers();
    renderReview();
    saveDraft();
  }
}

function updateRowNumbers() {
  transactionTableBody.querySelectorAll("tr").forEach((row, index) => {
    row.querySelector(".row-number").textContent = index + 1;
  });

  evidenceTableBody.querySelectorAll("tr").forEach((row, index) => {
    row.querySelector(".row-number").textContent = index + 1;
  });
}

function updateTransactionSummary() {
  const transactionRows = transactionTableBody.querySelectorAll("tr");
  let total = 0;

  transactionRows.forEach((row) => {
    const amount = parseFloat(row.querySelector('input[name="transactionAmount[]"]').value) || 0;
    total += amount;
  });

  transactionCountEl.textContent = transactionRows.length;
  totalAmountEl.textContent = total.toFixed(2);

  // Client-side risk level preview
  const risk = calculateClientRisk(total);
  const riskEl = document.getElementById('riskPreview');
  if (riskEl) {
    riskEl.textContent = risk;
    riskEl.className = `risk-preview risk-${risk.toLowerCase().replace(' ', '-')}`;
  }
}

function calculateClientRisk(amount) {
  if (amount >= 500000) return 'CRITICAL';
  if (amount >= 100000) return 'HIGH';
  if (amount >= 50000) return 'MEDIUM';
  return 'LOW';
}

function getTransactionReferenceList() {
  const refs = [];

  transactionTableBody.querySelectorAll("tr").forEach((row, index) => {
    const txId = row.querySelector('input[name="transactionId[]"]').value.trim();
    const date = row.querySelector('input[name="transactionDate[]"]').value.trim();
    const amount = row.querySelector('input[name="transactionAmount[]"]').value.trim();

    let label = txId || `Transaction ${index + 1}`;
    if (date || amount) {
      label += ` (${date || "-"} / ₹${amount || "0"})`;
    }

    refs.push({
      value: txId || `Transaction ${index + 1}`,
      label
    });
  });

  return refs;
}

function syncEvidenceTransactionOptions() {
  const options = getTransactionReferenceList();

  evidenceTableBody.querySelectorAll('select[name="evidenceTransactionRef[]"]').forEach((select) => {
    const currentValue = select.value;
    select.innerHTML = '<option value="">Select transaction</option>';

    options.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.value;
      option.textContent = item.label;
      select.appendChild(option);
    });

    if (currentValue) {
      setSelectValueIfExists(select, currentValue);
    }
  });
}

function setSelectValueIfExists(select, value) {
  const option = Array.from(select.options).find((item) => item.value === value);
  if (option) {
    select.value = value;
  }
}

function reuseLastSenderDetails() {
  const rows = transactionTableBody.querySelectorAll("tr");
  if (rows.length < 2) {
    showMessage("Add at least two transaction rows to reuse sender details.", false);
    return;
  }

  const lastRow = rows[rows.length - 2];
  const currentRow = rows[rows.length - 1];

  const bank = lastRow.querySelector('input[name="senderBank[]"]').value;
  const account = lastRow.querySelector('input[name="senderAccount[]"]').value;

  currentRow.querySelector('input[name="senderBank[]"]').value = bank;
  currentRow.querySelector('input[name="senderAccount[]"]').value = account;

  renderReview();
  saveDraft();
  showMessage("Sender bank and account copied to the latest row.", true);
}

function collectFormData() {
  const data = {
    victimName: document.getElementById("victimName").value.trim(),
    victimPhone: document.getElementById("victimPhone").value.trim(),
    victimAltPhone: document.getElementById("victimAltPhone").value.trim(),
    victimEmail: document.getElementById("victimEmail").value.trim(),
    victimAddress: document.getElementById("victimAddress").value.trim(),
    complaintTitle: document.getElementById("complaintTitle").value.trim(),
    crimeCategory: document.getElementById("crimeCategory").value,
    incidentDate: document.getElementById("incidentDate").value,
    incidentTime: document.getElementById("incidentTime").value,
    incidentDescription: document.getElementById("incidentDescription").value.trim(),
    suspectDetails: document.getElementById("suspectDetails").value.trim(),
    declaration: document.getElementById("declaration").checked,
    transactions: [],
    evidences: []
  };

  transactionTableBody.querySelectorAll("tr").forEach((row) => {
    data.transactions.push({
      transactionId: row.querySelector('input[name="transactionId[]"]').value.trim(),
      transactionDate: row.querySelector('input[name="transactionDate[]"]').value,
      transactionTime: row.querySelector('input[name="transactionTime[]"]').value,
      transactionAmount: row.querySelector('input[name="transactionAmount[]"]').value.trim(),
      senderBank: row.querySelector('input[name="senderBank[]"]').value.trim(),
      senderAccount: row.querySelector('input[name="senderAccount[]"]').value.trim(),
      receiverBank: row.querySelector('input[name="receiverBank[]"]').value.trim(),
      transactionMode: row.querySelector('select[name="transactionMode[]"]').value,
      transactionRemark: row.querySelector('input[name="transactionRemark[]"]').value.trim()
    });
  });

  evidenceTableBody.querySelectorAll("tr").forEach((row) => {
    const fileInput = row.querySelector('input[name="evidenceFile[]"]');
    const fileName = fileInput.files && fileInput.files[0] ? fileInput.files[0].name : "";

    data.evidences.push({
      evidenceType: row.querySelector('select[name="evidenceType[]"]').value,
      evidenceTransactionRef: row.querySelector('select[name="evidenceTransactionRef[]"]').value,
      evidenceDescription: row.querySelector('input[name="evidenceDescription[]"]').value.trim(),
      evidenceFileName: fileName
    });
  });

  return data;
}

function validateForm(data) {
  clearFieldErrors();

function setError(id, message) {
  const el = document.getElementById(id);

  if (el) {
    if (el.type === "checkbox") {
      el.parentElement.style.color = "red";
    } else {
      el.classList.add("input-error");
    }
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.focus();
  }

  showMessage(message, false);
}

  if (!data.victimName) {
    setError("victimName", "Victim full name is required.");
    return false;
  }

  if (!/^[0-9]{10}$/.test(data.victimPhone)) {
    setError("victimPhone", "Enter valid 10-digit phone.");
    return false;
  }

  if (!data.complaintTitle) {
    setError("complaintTitle", "Complaint title required.");
    return false;
  }

  if (!data.crimeCategory) {
    setError("crimeCategory", "Select crime category.");
    return false;
  }

  if (!data.incidentDate || !data.incidentTime) {
    setError("incidentDate", "Date & time required.");
    document.getElementById("incidentDate")?.scrollIntoView({ behavior: "smooth", block: "center" });
    return false;
  }

  if (!data.incidentDescription) {
    setError("incidentDescription", "Describe the incident.");
    return false;
  }

  const hasValidTransaction = data.transactions.some(tx =>
    tx.transactionId || tx.transactionAmount || tx.senderBank
  );

  if (!hasValidTransaction) {
    showMessage("Add at least one transaction.", false);
    transactionTableBody.scrollIntoView({ behavior: "smooth" });
    return false;
  }

  if (!data.declaration) {
    setError("declaration", "Accept declaration to continue.");
    return false;
  }

  return true;
}

function renderReview() {
  const data = collectFormData();

  const txHtml = data.transactions.length
    ? `
      <ul class="review-list">
        ${data.transactions.map((tx, index) => `
          <li>
            <strong>TX ${index + 1}:</strong>
            ID: ${escapeHtml(tx.transactionId || "-")},
            Date: ${escapeHtml(tx.transactionDate || "-")},
            Time: ${escapeHtml(tx.transactionTime || "-")},
            Amount: ₹${escapeHtml(tx.transactionAmount || "0")},
            Sender Bank: ${escapeHtml(tx.senderBank || "-")},
            Sender A/C: ${escapeHtml(tx.senderAccount || "-")},
            Receiver: ${escapeHtml(tx.receiverBank || "-")},
            Mode: ${escapeHtml(tx.transactionMode || "-")}
          </li>
        `).join("")}
      </ul>
    `
    : "<p>No transaction added.</p>";

 const evHtml = data.evidences.length
  ? `
     <ul class="review-list">
       ${data.evidences.map((ev, index) => `
         <li>
           <strong>Evidence ${index + 1}:</strong>
           Type: ${escapeHtml(ev.evidenceType || "-")},
           Linked TX: ${escapeHtml(ev.evidenceTransactionRef || "-")},
           Description: ${escapeHtml(ev.evidenceDescription || "-")},
           File: ${
             ev.file
               ? `<a href="${URL.createObjectURL(ev.file)}" target="_blank">${escapeHtml(ev.file.name)}</a>`
               : escapeHtml(ev.evidenceFileName || "No file selected")
           }
         </li>
       `).join("")}
     </ul>`
  : "<p>No evidence added.</p>";

  reviewBox.innerHTML = `
    <h3>Victim Details</h3>
    <p><strong>Name:</strong> ${escapeHtml(data.victimName || "-")}</p>
    <p><strong>Phone:</strong> ${escapeHtml(data.victimPhone || "-")}</p>
    <p><strong>Alternate Phone:</strong> ${escapeHtml(data.victimAltPhone || "-")}</p>
    <p><strong>Email:</strong> ${escapeHtml(data.victimEmail || "-")}</p>
    <p><strong>Address:</strong> ${escapeHtml(data.victimAddress || "-")}</p>

    <h3>Incident Details</h3>
    <p><strong>Title:</strong> ${escapeHtml(data.complaintTitle || "-")}</p>
    <p><strong>Category:</strong> ${escapeHtml(data.crimeCategory || "-")}</p>
    <p><strong>Date:</strong> ${escapeHtml(data.incidentDate || "-")}</p>
    <p><strong>Time:</strong> ${escapeHtml(data.incidentTime || "-")}</p>
    <p><strong>Description:</strong> ${escapeHtml(data.incidentDescription || "-")}</p>
    <p><strong>Suspect Details:</strong> ${escapeHtml(data.suspectDetails || "-")}</p>

    <h3>Transactions</h3>
    ${txHtml}

    <h3>Evidence</h3>
    ${evHtml}
  `;
}

function scheduleAutoSave() {
  setSaveStatus("Saving...");
  clearTimeout(autoSaveTimer);
  autoSaveTimer = setTimeout(saveDraft, 700);
}

function saveDraft() {
  const data = collectFormData();

  try {
    const payload = {
      ...data,
      savedAt: new Date().toISOString()
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));

    setSaveStatus("Draft saved ✅");
    showMessage("Draft auto-saved.", true);

    saveDraftBtn.textContent = "Saved ✓";
    saveDraftBtn.disabled = true;

    setTimeout(() => {
      saveDraftBtn.textContent = "Save Draft";
      saveDraftBtn.disabled = false;
    }, 1500);

  } catch (err) {
    showMessage("Failed to save draft.", false);
  }
}

function restoreDraft() {
  const savedDraft = localStorage.getItem(STORAGE_KEY);
  if (!savedDraft) {
    setSaveStatus("No saved draft");
    return;
  }

  try {
    const data = JSON.parse(savedDraft);

    document.getElementById("victimName").value = data.victimName || "";
    document.getElementById("victimPhone").value = data.victimPhone || "";
    document.getElementById("victimAltPhone").value = data.victimAltPhone || "";
    document.getElementById("victimEmail").value = data.victimEmail || "";
    document.getElementById("victimAddress").value = data.victimAddress || "";
    document.getElementById("complaintTitle").value = data.complaintTitle || "";
    document.getElementById("crimeCategory").value = data.crimeCategory || "";
    document.getElementById("incidentDate").value = data.incidentDate || "";
    document.getElementById("incidentTime").value = data.incidentTime || "";
    document.getElementById("incidentDescription").value = data.incidentDescription || "";
    document.getElementById("suspectDetails").value = data.suspectDetails || "";
    document.getElementById("declaration").checked = Boolean(data.declaration);

    transactionTableBody.innerHTML = "";
    evidenceTableBody.innerHTML = "";

    if (Array.isArray(data.transactions)) {
      data.transactions.forEach(tx => addTransactionRow(tx));
    }

    if (Array.isArray(data.evidences)) {
      data.evidences.forEach(ev => addEvidenceRow(ev));
    }

    if (data.savedAt) {
      setSaveStatus("Draft restored (" + new Date(data.savedAt).toLocaleString() + ")");
    } else {
      setSaveStatus("Draft restored");
    }

  } catch (error) {
    setSaveStatus("Draft restore failed");
  }
}

function clearDraft() {
  const confirmClear = confirm("⚠️ Delete saved draft?");

  if (!confirmClear) return;

  lastDraftBackup = localStorage.getItem(STORAGE_KEY);

  localStorage.removeItem(STORAGE_KEY);

  setSaveStatus("Draft cleared ❌");
  showMessage("Draft removed. Click UNDO to restore.", true);

  showUndoButton();
}

function resetWholeForm() {
  if (confirm('Reset entire form and clear draft?')) {
    complaintForm.reset();
  transactionTableBody.innerHTML = "";
  evidenceTableBody.innerHTML = "";

  addTransactionRow();
  addEvidenceRow();

  localStorage.removeItem(STORAGE_KEY);
  updateTransactionSummary();
  updateRowNumbers();
  syncEvidenceTransactionOptions();
  renderReview();
  setSaveStatus("Form reset");
  showMessage("Form has been reset and draft cleared.", true);
  }
}

let isSubmitting = false;

function handleSubmit(event) {
  event.preventDefault();
  console.log('handleSubmit called');

  const submitBtn = document.getElementById('submitBtn');
  if (!submitBtn) {
    console.error('Submit button not found');
    return;
  }

  const data = collectFormData();
  console.log("Form validation data:", data);

  if (!validateForm(data)) {
    console.log('Validation failed');
    submitBtn.classList.remove('loading');
    return;
  }

  console.log('Validation passed, starting submit');

  // Show loading
  submitBtn.classList.add('loading');
  submitBtn.disabled = true;

  // Reset after 30s timeout in case of issues
  setTimeout(() => {
    submitBtn.classList.remove('loading');
    submitBtn.disabled = false;
    showMessage('Submit timeout - please try again', false);
  }, 30000);

  // Submit form
  setTimeout(() => {
    console.log('Submitting form');
    complaintForm.submit();
  }, 200);
}
function clearFieldErrors() {
  document.querySelectorAll(".input-error").forEach(el => {
    el.classList.remove("input-error");
  });
}
function showMessage(msg, isSuccess) {
  messageBox.textContent = msg;
  messageBox.classList.remove("hidden");

  if (isSuccess) {
    messageBox.classList.add("success");
    messageBox.classList.remove("error");
  } else {
    messageBox.classList.add("error");
    messageBox.classList.remove("success");
  }

  setTimeout(() => {
    messageBox.classList.add("hidden");
  }, 3000);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

init();