import { API } from "./api.js";
import { showBreadcrumbs } from "./breadcrumbs.js";

const api = new API(onLoad),
  sidebar = document.getElementById("sidebar"),
  home = document.getElementById("home"),
  path = location.href.split("/"),
  fileId = path[path.length - 1];

function showRootDirs() {
  const rootDirs = api.dirsIn(api.root()),
    makeRootDir = (id, nameStr) => {
      const obj = document.createElement("div"),
        ico = document.createElement("i"),
        name = document.createElement("span");

      obj.classList.add("bar", "clickable");
      ico.classList.add("fa-regular", "fa-folder-closed", "icon");
      name.classList.add("name");

      name.innerText = nameStr;

      obj.addEventListener("click", () => (location.href = `/~/${id}`));

      obj.appendChild(ico);
      obj.appendChild(name);

      sidebar.append(obj);
    };

  for (const dirId of Object.keys(rootDirs)) {
    makeRootDir(dirId, rootDirs[dirId]);
  }
}

function showShare() {
  const overlay = document.createElement("div"),
    share = document.createElement("div"),
    closeico = document.createElement("i"),
    title = document.createElement("span"),
    description = document.createElement("p"),
    passwd = document.createElement("input"),
    create = document.createElement("button"),
    createIco = document.createElement("i"),
    createName = document.createElement("span");

  overlay.id = "overlay";
  share.classList.add("share");
  closeico.classList.add("fa-solid", "fa-xmark", "closeico");
  title.classList.add("title");
  description.classList.add("description");
  passwd.type = "password";
  passwd.name = "sharepwd";
  createIco.classList.add("fa-solid", "fa-link", "icon");
  createName.classList.add("name");

  description.innerHTML =
    "You can generate a link to share this file here.<br />To secure this link using a password, use the box below!";
  title.innerText = "Share file";
  createName.innerText = "Create Link";

  closeico.addEventListener("click", () => document.body.removeChild(overlay));

  create.addEventListener("click", () =>
    api.makeShare(fileId, passwd.value, (shareId) => {
      share.removeChild(passwd);
      share.removeChild(create);

      description.innerHTML =
        "You can now share this file using the link below.";

      const linkStr = `${location.href.split("/preview/")[0]}/share/${shareId}`,
        link = document.createElement("span");
      link.id = "linkout";
      link.innerText = linkStr;

      share.appendChild(link);
    })
  );

  create.appendChild(createIco);
  create.appendChild(createName);
  share.appendChild(closeico);
  share.appendChild(title);
  share.appendChild(description);
  share.appendChild(passwd);
  share.appendChild(create);
  overlay.appendChild(share);
  document.body.appendChild(overlay);
}

function onLoad() {
  api.moveStatic(api.pathOf(fileId));

  showRootDirs();
  showBreadcrumbs(api, (id) => (location.href = `/~/${id[id.length - 1]}`));

  document.getElementById("filename").innerText = api.nameById(fileId);

  document
    .getElementById("fileico")
    .classList.add(api.iconByName(api.nameById(fileId)));

  document.getElementById("close").addEventListener("click", () => {
    const path = api.dir[api.dir.length - 1] || "";
    location.href = `/~/${path}`;
  });
}

document
  .getElementById("download")
  .addEventListener("click", () => open(`/a/v1/${fileId}/download`, "_blank"));

document.getElementById("share").addEventListener("click", showShare);

document.getElementById("preview").src = `/a/v1/preview/${fileId}`;

home.addEventListener("click", () => (location.href = "/~/"));
