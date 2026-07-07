const input = document.querySelector("#file-input");
const dropzone = document.querySelector("#dropzone");
const selectedFiles = document.querySelector("#selected-files");
const form = document.querySelector("#conversion-form");
const fileMessage = document.querySelector("#file-message");
const mergeOrderInput = document.querySelector("#merge-order");
const convertButton = document.querySelector("#convert-button");
const acceptedExtensions = new Set(["pptx", "ppt", "docx", "pdf"]);
const maxFiles = Number(form.dataset.maxFiles);
const maxTotalBytes = Number(form.dataset.maxTotalBytes);
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
    item.className = "empty-list";
    item.textContent = "No files selected yet.";
    selectedFiles.append(item);
    syncMergeOrder();
    return;
  }

  for (const [index, entry] of chosenFiles.entries()) {
    const item = document.createElement("li");
    item.draggable = true;
    item.dataset.fileId = entry.id;

    const name = document.createElement("span");
    name.textContent = entry.file.name;
    item.append(name);

    const up = document.createElement("button");
    up.type = "button";
    up.textContent = "Up";
    up.disabled = index === 0;
    up.addEventListener("click", () => moveFile(index, index - 1));
    item.append(up);

    const down = document.createElement("button");
    down.type = "button";
    down.textContent = "Down";
    down.disabled = index === chosenFiles.length - 1;
    down.addEventListener("click", () => moveFile(index, index + 1));
    item.append(down);

    const remove = document.createElement("button");
    remove.type = "button";
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
