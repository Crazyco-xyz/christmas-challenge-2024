import { API } from "./api.js";
import { initContext } from "./ctxmenu.js";
import { initUpload } from "./upload.js";
import Abortable from "./abort.js";

const api = new API(refreshFiles, refreshFiles),
  main = document.getElementsByTagName("main")[0],
  topbar = document.getElementById("topbar"),
  breadcrumbs = topbar.getElementsByClassName("breadcrumbs")[0],
  sidebar = document.getElementById("sidebar"),
  ctxdownload = document.getElementById("ctxdownload"),
  moveUp = document.getElementById("moveup"),
  moveBack = document.getElementById("moveback"),
  moveFwd = document.getElementById("movefwd");

function refreshFiles() {
  let currentDir = api.currentDir();
  if (typeof currentDir !== "object") return;

  const clearFiles = () => {
    while (main.firstChild) {
      main.removeChild(main.firstChild);
    }
  };

  const addFile = (id) => {
    if (id[0] === "_") return;

    const fileName = currentDir[id],
      isdir = typeof fileName === "object",
      obj = document.createElement("div"),
      ico = document.createElement("i"),
      name = document.createElement("span");

    obj.classList.add("object");
    ico.classList.add("fa-regular", "fa-3x");
    name.classList.add("name");

    if (isdir) {
      ico.classList.add("fa-folder");
      name.innerText = api.nameById(id);
    } else {
      ico.classList.add(api.iconByName(fileName));
      name.innerText = fileName;
    }

    obj.id = id;

    obj.addEventListener("contextmenu", (e) => {
      e.preventDefault();
      Abortable.abort();

      if (isdir) {
        ctxdownload.style.display = "none";
      } else {
        ctxdownload.style.display = "block";
      }

      let bounds = obj.getBoundingClientRect();
      ctxmenu.style.left = `${bounds.x}px`;
      ctxmenu.style.top = `${bounds.y + bounds.height}px`;
      ctxmenu.style.display = "flex";

      ctxmenu.dataset["hover_id"] = id;

      Abortable.add(() => {
        ctxmenu.style.display = "none";
      });
    });
    obj.addEventListener("dblclick", () => {
      if (!isdir) {
        location.href = `/preview/${id}`;
      }
      api.moveInto(id);
      refreshFiles();
    });
    obj.addEventListener("click", (e) => {
      Abortable.abort(e);

      obj.classList.add("selected");
      Abortable.add(() => {
        obj.classList.remove("selected");
      });
    });

    obj.appendChild(ico);
    obj.appendChild(name);
    main.appendChild(obj);
  };

  const addAddFolder = () => {
    const folder = document.createElement("div"),
      icon = document.createElement("i"),
      name = document.createElement("span");

    folder.classList.add("object", "add");
    icon.classList.add("fa-solid", "fa-folder-plus", "fa-3x");
    name.classList.add("name");
    name.innerHTML = "Create folder";

    folder.addEventListener("click", (e) => {
      Abortable.abort(e);

      const nameInput = document.createElement("input");
      nameInput.type = "text";

      nameInput.addEventListener("keypress", (event) => {
        if (event.key == "Enter") {
          event.preventDefault();
          api.createFolder(nameInput.value, refreshFiles);
        }
      });

      name.style.display = "none";
      folder.appendChild(nameInput);
      nameInput.focus();

      Abortable.add(() => {
        folder.removeChild(nameInput);
        name.style.display = "block";
      });
    });

    folder.appendChild(icon);
    folder.appendChild(name);
    main.appendChild(folder);
  };

  clearFiles();

  for (const id of Object.keys(currentDir)) {
    addFile(id);
  }
  addAddFolder();

  showBreadcrumbs();
  showRootDirs();
}

function showBreadcrumbs() {
  const clearBreadcrumbs = () => {
      while (breadcrumbs.firstChild) {
        breadcrumbs.removeChild(breadcrumbs.firstChild);
      }
    },
    makeSpacer = () => {
      const spacer = document.createElement("div");
      spacer.classList.add("spacer");
      spacer.innerText = "/";

      return spacer;
    },
    makeCrumb = (nameStr, idPath) => {
      const crumb = document.createElement("div"),
        ico = document.createElement("i"),
        name = document.createElement("span");

      crumb.classList.add("hover");
      ico.classList.add("fa-regular", "fa-folder", "icon");
      name.classList.add("name");

      name.innerText = nameStr;

      crumb.addEventListener("click", () => {
        api.moveStatic(idPath);
      });

      crumb.appendChild(ico);
      crumb.appendChild(name);

      return crumb;
    },
    makeEllipses = () => {
      const ellipses = document.createElement("div"),
        name = document.createElement("span");

      name.classList.add("name");
      name.innerText = "...";

      ellipses.appendChild(name);

      return ellipses;
    },
    dirParts = api.currentDirPath(),
    idPath = [];

  clearBreadcrumbs();

  if (dirParts.length == 0) {
    breadcrumbs.appendChild(makeSpacer());

    return;
  } else if (dirParts.length <= 3) {
    for (const part of dirParts) {
      idPath.push(part.id);
      breadcrumbs.appendChild(makeSpacer());
      breadcrumbs.appendChild(makeCrumb(part.name, idPath.slice()));
    }

    return;
  }

  breadcrumbs.appendChild(makeSpacer());
  breadcrumbs.append(makeCrumb(dirParts[0].name, [dirParts[0].id]));
  breadcrumbs.appendChild(makeSpacer());
  breadcrumbs.appendChild(makeEllipses());

  for (let i = dirParts.length - 2; i < dirParts.length; i++) {
    idPath.push(dirParts[i].id);
    breadcrumbs.appendChild(makeSpacer());
    breadcrumbs.appendChild(makeCrumb(dirParts[i].name, idPath.slice()));
  }
}

function showRootDirs() {
  const clearRoot = () => {
      for (const rdir of sidebar.getElementsByClassName("root")) {
        sidebar.removeChild(rdir);
      }
    },
    makeFolder = (nameStr, id) => {
      const folder = document.createElement("div"),
        ico = document.createElement("i"),
        name = document.createElement("span");

      folder.classList.add("bar", "clickable", "root");
      ico.classList.add("fa-regular", "fa-folder-closed", "icon");
      name.classList.add("name");

      name.innerText = nameStr;

      folder.addEventListener("click", () => {
        api.moveStatic([id]);
        refreshFiles();
      });

      folder.appendChild(ico);
      folder.appendChild(name);

      return folder;
    };

  clearRoot();

  for (const f of Object.keys(api.dirsIn(api.root()))) {
    sidebar.appendChild(makeFolder(api.root()[f]._name, f));
  }
}

document.addEventListener("click", () => {
  Abortable.abort();
});

moveUp.addEventListener("click", () => {
  api.moveUp();
  refreshFiles();
});

moveBack.addEventListener("click", () => {
  api.moveBack();
  refreshFiles();
});

moveFwd.addEventListener("click", () => {
  api.moveForward();
  refreshFiles();
});

document.getElementById("home").addEventListener("click", () => {
  api.moveStatic([]);
  refreshFiles();
});

api.userId((name) => {
  document.getElementById("user").innerText = `${name}'s Files`;
});

initUpload();
initContext();

export { api, refreshFiles };
