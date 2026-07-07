const input = document.querySelector("#file-input");
const dropzone = document.querySelector("#dropzone");
const selectedFiles = document.querySelector("#selected-files");
const form = document.querySelector("#conversion-form");
const fileMessage = document.querySelector("#file-message");
const mergeOrderInput = document.querySelector("#merge-order");
const convertButton = document.querySelector("#convert-button");
const progressPanel = document.querySelector("#progress-panel");
const acceptedExtensions = new Set(["pptx", "ppt", "docx", "pdf"]);
const maxFiles = Number(form.dataset.maxFiles);
const maxTotalBytes = Number(form.dataset.maxTotalBytes);
const emptyStateClass = "mt-1 text-sm text-zinc-500";
const fileRowClass = "grid grid-cols-[minmax(0,1fr)_auto_auto_auto] items-center gap-2 rounded-2xl border border-white/10 bg-zinc-950/80 p-3 text-sm sm:text-base";
const fileNameClass = "min-w-0 truncate font-medium text-zinc-100";
const fileButtonClass = "rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm font-medium text-zinc-300 transition hover:border-emerald-300/50 hover:text-emerald-100 disabled:cursor-not-allowed disabled:opacity-40";
const downloadClass = "inline-flex w-fit rounded-xl bg-emerald-300 px-5 py-3 font-semibold text-zinc-950 no-underline transition hover:bg-emerald-200 active:translate-y-px";
let chosenFiles = [];
let nextFileId = 1;

function extensionFor(file) {
  return file.name.split(".").pop().toLowerCase();
}

function showMessage(message) {
  fileMessage.textContent = message;
}

function syncFileInput() {
  const transfer = new DataTransfer();
  for (const entry of chosenFiles) {
    transfer.items.add(entry.file);
  }
  input.files = transfer.files;
}

function syncMergeOrder() {
  mergeOrderInput.value = JSON.stringify(chosenFiles.map((entry) => entry.file.name));
  convertButton.disabled = chosenFiles.length === 0;
}

function showProgress(message, percent) {
  progressPanel.textContent = `${message} (${percent}%)`;
}

function showFailure(job) {
  progressPanel.replaceChildren();
  const message = document.createElement("p");
  message.className = "font-semibold text-red-300";
  message.textContent = job.message;
  progressPanel.append(message);

  if (job.error_detail) {
    const details = document.createElement("details");
    details.className = "mt-3";
    const summary = document.createElement("summary");
    summary.className = "cursor-pointer font-semibold text-emerald-200";
    summary.textContent = "Technical details";
    const pre = document.createElement("pre");
    pre.className = "mt-3 overflow-auto rounded-xl border border-white/10 bg-zinc-950 p-3 text-sm text-zinc-300";
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

    const name = document.createElement("span");
    name.className = fileNameClass;
    name.textContent = entry.file.name;
    item.append(name);

    const up = document.createElement("button");
    up.type = "button";
    up.className = fileButtonClass;
    up.textContent = "Up";
    up.disabled = index === 0;
    up.addEventListener("click", () => moveFile(index, index - 1));
    item.append(up);

    const down = document.createElement("button");
    down.type = "button";
    down.className = fileButtonClass;
    down.textContent = "Down";
    down.disabled = index === chosenFiles.length - 1;
    down.addEventListener("click", () => moveFile(index, index + 1));
    item.append(down);

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = fileButtonClass;
    remove.textContent = "Remove";
    remove.addEventListener("click", () => removeFile(entry.id));
    item.append(remove);

    item.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", String(index));
    });
    item.addEventListener("dragover", (event) => event.preventDefault());
    item.addEventListener("drop", (event) => {
      event.preventDefault();
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
    ...files.map((file) => ({ id: nextFileId++, file })),
  ];
  showMessage("");
  syncFileInput();
  renderFiles();
}

function removeFile(fileId) {
  chosenFiles = chosenFiles.filter((entry) => entry.id !== fileId);
  syncFileInput();
  renderFiles();
}

function moveFile(fromIndex, toIndex) {
  if (toIndex < 0 || toIndex >= chosenFiles.length || fromIndex === toIndex) {
    return;
  }

  const [entry] = chosenFiles.splice(fromIndex, 1);
  chosenFiles.splice(toIndex, 0, entry);
  syncFileInput();
  renderFiles();
}

input.addEventListener("change", () => {
  addFiles([...input.files]);
});

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
});

dropzone.addEventListener("drop", (event) => {
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
