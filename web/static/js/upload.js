import { api, refreshFiles } from "./filepicker.js";

const upload = document.getElementById("upload"),
  uploadInput = document.getElementById("file");

function onUpload(files) {
  const uploadText = upload.getElementsByClassName("name")[0],
    uploadDescription = upload.getElementsByClassName("description")[0],
    onFinish = () => {
      uploadText.innerHTML = "Upload";
    },
    onSuccess = (name, body) => {
      api.currentDir()[body.file_id] = name;
      refreshFiles();
    },
    onFailure = (name, body) => {
      uploadDescription.innerText = body.message;
    };

  // Change text of upload box
  uploadText.innerHTML = "Uploading...";

  api.uploadFiles(files, onSuccess, onFailure, onFinish);
}

function openFileInput() {
  // Open the file input dialogue box
  uploadInput.click();
}

function initUpload() {
  // Open file input on click
  upload.onclick = openFileInput;
  uploadInput.onchange = (e) => onUpload(e.target.files);

  // Prevent default dropping behaviour
  ["dragenter", "dragover", "dragleave", "drop"].forEach((event) =>
    upload.addEventListener(event, (e) => {
      e.preventDefault();
      e.stopPropagation();
    })
  );

  // Show border on hover while dragging a file
  upload.addEventListener("dragover", () => {
    upload.style.border = "1px solid var(--color-border)";
  });

  // Hide border when drag leaves or file gets dropped
  ["dragleave", "drop"].forEach((event) =>
    upload.addEventListener(
      event,
      () => (upload.style.border = "1px solid transparent")
    )
  );

  // When a file gets dropped
  upload.addEventListener("drop", (e) => {
    e.stopPropagation();
    onUpload(e.dataTransfer.files);
  });
}

export { initUpload };
