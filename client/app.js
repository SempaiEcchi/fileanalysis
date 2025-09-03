const UPLOAD_URL = "http://localhost:5001/upload";
const FILES_URL = "http://localhost:5001/files";
const STATUS_URL = "http://localhost:5001/status/";

const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const tbody = document.getElementById("fileTableBody");

// Modal elements
const resultModal = document.getElementById("resultModal");
const closeModal = document.getElementById("closeModal");
const modalFilename = document.getElementById("modalFilename");
const modalResult = document.getElementById("modalResult");

// Handle upload
uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const file = fileInput.files[0];
    if (!file) return alert("Choose a file!");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(UPLOAD_URL, { method: "POST", body: formData });
        const data = await res.json();
        alert(`File uploaded! ID: ${data.file_id}`);
        loadFiles();
    } catch (err) {
        console.error("Upload failed:", err);
        alert("Upload failed!");
    }
});

// Fetch all files
async function loadFiles() {
    try {
        const res = await fetch(FILES_URL);
        const files = await res.json();

        tbody.innerHTML = "";

        files.forEach(file => {
            const tr = document.createElement("tr");

            // Filename clickable
            const nameTd = document.createElement("td");
            nameTd.textContent = file.filename;
            nameTd.classList.add("clickable");
            nameTd.addEventListener("click", () => showFileResult(file.file_id));

            // Status badge
            const statusTd = document.createElement("td");
            const statusSpan = document.createElement("span");
            statusSpan.textContent = file.status;
            statusSpan.classList.add("status");
            if (file.status === "PENDING") statusSpan.classList.add("status-pending");
            else if (file.status === "DONE") statusSpan.classList.add("status-done");
            else statusSpan.classList.add("status-error");
            statusTd.appendChild(statusSpan);

            const createdTd = document.createElement("td");
            createdTd.textContent = file.created_at || "";

            tr.appendChild(nameTd);
            tr.appendChild(statusTd);
            tr.appendChild(createdTd);

            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed to load files:", err);
    }
}

// Show result in modal
async function showFileResult(fileId) {
    try {
        const res = await fetch(STATUS_URL + fileId);
        const file = await res.json();

        modalFilename.textContent = file.filename;
        modalResult.textContent = file.result || "No analysis result yet.";
        resultModal.style.display = "block";
    } catch (err) {
        console.error("Failed to fetch file details:", err);
    }
}

// Close modal
closeModal.addEventListener("click", () => {
    resultModal.style.display = "none";
});
window.addEventListener("click", (e) => {
    if (e.target === resultModal) {
        resultModal.style.display = "none";
    }
});

// Initial load + auto-refresh every 5s
document.addEventListener("DOMContentLoaded", () => {
    loadFiles();
    setInterval(loadFiles, 5000);
});
