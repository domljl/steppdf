const input = document.querySelector("#file-input");
const dropzone = document.querySelector("#dropzone");
const selectedFiles = document.querySelector("#selected-files");

function renderFiles(files) {
  selectedFiles.replaceChildren();

  if (files.length === 0) {
    const item = document.createElement("li");
    item.className = "empty-list";
    item.textContent = "No files selected yet.";
    selectedFiles.append(item);
    return;
  }

  for (const file of files) {
    const item = document.createElement("li");
    item.textContent = file.name;
    selectedFiles.append(item);
  }
}

input.addEventListener("change", () => {
  renderFiles([...input.files]);
});

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  input.files = event.dataTransfer.files;
  renderFiles([...input.files]);
});
