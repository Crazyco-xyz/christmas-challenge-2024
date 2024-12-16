const topbar = document.getElementById("topbar"),
  breadcrumbs = topbar.getElementsByClassName("breadcrumbs")[0];

function clearBreadcrumbs() {
  while (breadcrumbs.firstChild) {
    breadcrumbs.removeChild(breadcrumbs.firstChild);
  }
}

function makeSpacer() {
  const spacer = document.createElement("div");
  spacer.classList.add("spacer");
  spacer.innerText = "/";

  return spacer;
}

function makeCrumb(nameStr, idPath, clickCallback) {
  const crumb = document.createElement("div"),
    ico = document.createElement("i"),
    name = document.createElement("span");

  crumb.classList.add("hover");
  ico.classList.add("fa-regular", "fa-folder", "icon");
  name.classList.add("name");

  name.innerText = nameStr;

  crumb.addEventListener("click", () => {
    clickCallback(idPath);
  });

  crumb.appendChild(ico);
  crumb.appendChild(name);

  return crumb;
}

function makeEllipses() {
  const ellipses = document.createElement("div"),
    name = document.createElement("span");

  name.classList.add("name");
  name.innerText = "...";

  ellipses.appendChild(name);

  return ellipses;
}

function showBreadcrumbs(api, clickCallback) {
  const dirParts = api.currentDirPath(),
    idPath = [];

  clearBreadcrumbs();

  if (dirParts.length == 0) {
    breadcrumbs.appendChild(makeSpacer());

    return;
  } else if (dirParts.length <= 3) {
    for (const part of dirParts) {
      idPath.push(part.id);
      breadcrumbs.appendChild(makeSpacer());
      breadcrumbs.appendChild(
        makeCrumb(part.name, idPath.slice(), clickCallback)
      );
    }

    return;
  }

  breadcrumbs.appendChild(makeSpacer());
  breadcrumbs.append(
    makeCrumb(dirParts[0].name, [dirParts[0].id], clickCallback)
  );
  breadcrumbs.appendChild(makeSpacer());
  breadcrumbs.appendChild(makeEllipses());

  for (let i = dirParts.length - 2; i < dirParts.length; i++) {
    idPath.push(dirParts[i].id);
    breadcrumbs.appendChild(makeSpacer());
    breadcrumbs.appendChild(
      makeCrumb(dirParts[i].name, idPath.slice(), clickCallback)
    );
  }
}

export { showBreadcrumbs };
