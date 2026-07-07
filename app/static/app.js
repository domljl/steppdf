const input = document.querySelector("#file-input");
const addMoreButton = document.querySelector("#add-more-button");
const startPage = document.querySelector("#start-page");
const filesPage = document.querySelector("#files-page");
const selectedFiles = document.querySelector("#selected-files");
const form = document.querySelector("#conversion-form");
const fileMessage = document.querySelector("#file-message");
const mergeOrderInput = document.querySelector("#merge-order");
const convertButton = document.querySelector("#convert-button");
const progressPanel = document.querySelector("#progress-panel");
const acceptedExtensions = new Set(["pptx", "ppt", "docx", "pdf"]);
const maxFiles = Number(form.dataset.maxFiles);
const maxTotalBytes = Number(form.dataset.maxTotalBytes);
const emptyStateClass = "mt-1 text-sm text-[var(--muted-foreground)]";
const fileRowClass = "grid cursor-grab gap-3 rounded-2xl bg-[color-mix(in_srgb,var(--foreground)_6%,transparent)] p-4 text-sm shadow-[0_8px_32px_rgba(0,0,0,0.22)] ring-1 ring-[color-mix(in_srgb,var(--foreground)_10%,transparent)] active:cursor-grabbing";
const fileNameClass = "min-w-0 truncate text-center font-medium text-[var(--foreground)]";
const fileButtonClass = "rounded-full bg-transparent px-3 py-2 text-sm font-medium text-[var(--foreground)] ring-1 ring-[color-mix(in_srgb,var(--foreground)_12%,transparent)] transition hover:ring-[color-mix(in_srgb,var(--accent)_35%,transparent)] disabled:cursor-not-allowed disabled:opacity-40";
const downloadClass = "inline-flex w-fit rounded-full bg-transparent px-5 py-3 font-medium text-[var(--foreground)] no-underline shadow-[0_8px_32px_rgba(0,0,0,0.22)] ring-1 ring-[color-mix(in_srgb,var(--foreground)_12%,transparent)] transition hover:ring-[color-mix(in_srgb,var(--accent)_35%,transparent)] active:scale-[0.97]";
let chosenFiles = [];
let nextFileId = 1;

function extensionFor(file) {
  return file.name.split(".").pop().toLowerCase();
}

function showMessage(message) {
  fileMessage.textContent = message;
}

function syncMergeOrder() {
  const hasFiles = chosenFiles.length > 0;
  mergeOrderInput.value = JSON.stringify(chosenFiles.map((entry) => entry.file.name));
  convertButton.disabled = !hasFiles;
  startPage.classList.toggle("hidden", hasFiles);
  startPage.classList.toggle("grid", !hasFiles);
  startPage.hidden = hasFiles;
  filesPage.classList.toggle("hidden", !hasFiles);
  filesPage.classList.toggle("grid", hasFiles);
  filesPage.hidden = !hasFiles;
}

function showProgress(message, percent) {
  progressPanel.textContent = `${message} (${percent}%)`;
}

function showFailure(job) {
  progressPanel.replaceChildren();
  const message = document.createElement("p");
  message.className = "font-medium text-[var(--accent)]";
  message.textContent = job.message;
  progressPanel.append(message);

  if (job.error_detail) {
    const details = document.createElement("details");
    details.className = "mt-3";
    const summary = document.createElement("summary");
    summary.className = "cursor-pointer font-medium text-[var(--accent)]";
    summary.textContent = "Technical details";
    const pre = document.createElement("pre");
    pre.className = "mt-3 overflow-auto rounded-2xl bg-[color-mix(in_srgb,var(--foreground)_6%,transparent)] p-3 text-sm text-[var(--foreground)] ring-1 ring-[color-mix(in_srgb,var(--foreground)_10%,transparent)]";
    pre.textContent = job.error_detail;
    details.append(summary, pre);
    progressPanel.append(details);
  }
}

function validateFiles(files) {
  const nextFiles = [...chosenFiles, ...files];

  if (nextFiles.length > maxFiles) {
    return "You can add up to 50 files.";
  }

  const unsupportedFile = files.find((file) => !acceptedExtensions.has(extensionFor(file)));
  if (unsupportedFile) {
    return `Unsupported file type: ${unsupportedFile.name}`;
  }

  const totalBytes = nextFiles.reduce((total, entry) => total + (entry.file?.size ?? entry.size), 0);
  if (totalBytes > maxTotalBytes) {
    return "Total input must be 1 GB or less.";
  }

  return "";
}

function renderFiles() {
  selectedFiles.replaceChildren();

  if (chosenFiles.length === 0) {
    const item = document.createElement("li");
    item.className = emptyStateClass;
    item.textContent = "No files selected yet.";
    selectedFiles.append(item);
    syncMergeOrder();
    return;
  }

  for (const [index, entry] of chosenFiles.entries()) {
    const item = document.createElement("li");
    item.className = fileRowClass;
    item.draggable = true;
    item.dataset.fileId = entry.id;

    const preview = document.createElement("div");
    preview.className = "grid aspect-[3/4] place-items-center bg-[color-mix(in_srgb,var(--foreground)_8%,transparent)] text-sm font-medium uppercase text-[var(--muted-foreground)] ring-1 ring-[color-mix(in_srgb,var(--foreground)_10%,transparent)]";
    preview.textContent = extensionFor(entry.file);
    item.append(preview);

    const name = document.createElement("span");
    name.className = fileNameClass;
    name.textContent = entry.file.name;
    item.append(name);

    const actions = document.createElement("div");
    actions.className = "flex justify-center gap-2";

    const up = document.createElement("button");
    up.type = "button";
    up.className = fileButtonClass;
    up.textContent = "Up";
    up.disabled = index === 0;
    up.addEventListener("click", () => moveFile(index, index - 1));
    actions.append(up);

    const down = document.createElement("button");
    down.type = "button";
    down.className = fileButtonClass;
    down.textContent = "Down";
    down.disabled = index === chosenFiles.length - 1;
    down.addEventListener("click", () => moveFile(index, index + 1));
    actions.append(down);

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = fileButtonClass;
    remove.textContent = "Remove";
    remove.addEventListener("click", () => removeFile(entry.id));
    actions.append(remove);
    item.append(actions);

    item.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", String(index));
    });
    item.addEventListener("dragover", (event) => event.preventDefault());
    item.addEventListener("drop", (event) => {
      event.preventDefault();
      event.stopPropagation();
      moveFile(Number(event.dataTransfer.getData("text/plain")), index);
    });

    selectedFiles.append(item);
  }

  syncMergeOrder();
}

function addFiles(files) {
  const message = validateFiles(files);
  if (message) {
    showMessage(message);
    return;
  }

  chosenFiles = [
    ...chosenFiles,
    ...files.map((file) => ({
      id: nextFileId++,
      file,
    })),
  ];
  showMessage("");
  renderFiles();
}

function removeFile(fileId) {
  chosenFiles = chosenFiles.filter((entry) => entry.id !== fileId);
  renderFiles();
}

function moveFile(fromIndex, toIndex) {
  if (toIndex < 0 || toIndex >= chosenFiles.length || fromIndex === toIndex) {
    return;
  }

  const [entry] = chosenFiles.splice(fromIndex, 1);
  chosenFiles.splice(toIndex, 0, entry);
  renderFiles();
}

input.addEventListener("change", () => {
  addFiles([...input.files]);
  input.value = "";
});

addMoreButton.addEventListener("click", () => input.click());

document.body.addEventListener("dragover", (event) => {
  event.preventDefault();
});

document.body.addEventListener("drop", (event) => {
  event.preventDefault();
  addFiles([...event.dataTransfer.files]);
});

function pollJob(jobId) {
  fetch(`/jobs/${jobId}`)
    .then((response) => response.json())
    .then((job) => {
      showProgress(job.message, job.percent);
      if (job.phase === "ready") {
        progressPanel.replaceChildren();
        const link = document.createElement("a");
        link.href = `/jobs/${job.job_id}/download`;
        link.className = downloadClass;
        link.textContent = `Download ${job.output_filename}`;
        progressPanel.append(link);
      }
      if (job.phase === "failed") {
        showFailure(job);
      }
      if (!["ready", "failed", "expired"].includes(job.phase)) {
        window.setTimeout(() => pollJob(job.job_id), 500);
      }
    });
}

convertButton.addEventListener("click", () => {
  const formData = new FormData(form);
  for (const entry of chosenFiles) {
    formData.append("files", entry.file);
  }

  const xhr = new XMLHttpRequest();
  xhr.upload.addEventListener("progress", (event) => {
    if (event.lengthComputable) {
      showProgress("Uploading", Math.round((event.loaded / event.total) * 100));
    }
  });
  xhr.addEventListener("load", () => {
    const job = JSON.parse(xhr.responseText);
    showProgress(job.message, job.percent);
    pollJob(job.job_id);
  });
  xhr.open("POST", "/jobs");
  xhr.send(formData);
});
