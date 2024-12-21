import Abortable from "./abort.js";
import { api, refreshFiles } from "./filepicker.js";

const ctxmenu = document.getElementById("ctxmenu"),
  ctxrename = document.getElementById("ctxrename"),
  ctxdelete = document.getElementById("ctxdelete"),
  ctxdownload = document.getElementById("ctxdownload");

function onRenameClick(e) {
  Abortable.abort(e);
  ctxmenu.style.display = "none";

  const hoverid = ctxmenu.dataset["hover_id"],
    clicked = document.getElementById(hoverid),
    name = clicked.getElementsByClassName("name")[0],
    nameInput = document.createElement("input");

  name.style.display = "none";

  nameInput.type = "text";
  nameInput.value = api.nameById(hoverid);
  nameInput.addEventListener("keypress", (event) => {
    if (event.key == "Enter") {
      event.preventDefault();

      api.rename(hoverid, nameInput.value);
      refreshFiles();
    }
  });

  clicked.appendChild(nameInput);
  nameInput.focus();
}

function onDeleteClick(e) {
  Abortable.abort(e);
  ctxmenu.style.display = "none";

  const hoverid = ctxmenu.dataset["hover_id"];
  api.delete(hoverid);
  refreshFiles();
}

function onDownloadClick(e) {
  Abortable.abort(e);
  ctxmenu.style.display = "none";

  const hoverid = ctxmenu.dataset["hover_id"];
  window.open(`/a/v1/${hoverid}/download`, "_blank");
}

function initContext() {
  document.addEventListener("contextmenu", (e) => e.preventDefault());

  ctxrename.addEventListener("click", onRenameClick);
  ctxdelete.addEventListener("click", onDeleteClick);
  ctxdownload.addEventListener("click", onDownloadClick);
}

export { initContext };
