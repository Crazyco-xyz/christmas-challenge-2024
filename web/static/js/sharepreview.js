const sidebar = document.getElementById("sidebar"),
  home = document.getElementById("home"),
  path = location.href.split("/"),
  fileId = path[path.length - 1];

function getShareDetails(shareId, password, callback) {
  const data = { share_id: shareId };
  if (password) data.password = password;

  fetch(`/a/v1/sharedetails`, {
    method: "POST",
    body: JSON.stringify(data),
    headers: { "Content-Type": "application/json" },
  })
    .then(async function (response) {
      return { status: response.ok, json: await response.json() };
    })
    .then(({ status, json }) => {
      if (!status) {
        alert(json.message);
        return;
      }

      callback(json.name, json.password);
    });
}

function downloadShare(fileId, password) {
  const shareUrl = `/a/v1/${fileId}/download`;

  if (!password) {
    open(shareUrl, "_blank");
    return;
  }

  fetch(shareUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password: password }),
  })
    .then((response) => response.blob())
    .then((blob) => {
      window.open(URL.createObjectURL(blob));
    });
}

function onLoad(name, password) {
  const nameParts = name.split("."),
    ext = nameParts[nameParts.length - 1],
    onIcons = (icons) => {
      for (const ico of icons) {
        if (ico.ext.includes(ext)) {
          document.getElementById("fileico").classList.add(ico.icon);
          return;
        }
      }
      document.getElementById("fileico").classList.add("fa-file");
    };
  document.getElementById("filename").innerText = name;

  fetch("/s/filetypes.json")
    .then((response) => response.json())
    .then(onIcons);

  if (password) askPassword();
  else passwordSubmitted(null);
}

function askPassword() {
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
  createIco.classList.add("fa-solid", "fa-key", "icon");
  createName.classList.add("name");

  description.innerHTML = "You need to enter a password to view this share!";
  title.innerText = "Shared file";
  createName.innerText = "View File";

  closeico.addEventListener("click", () => (location.href = "/~"));

  create.addEventListener("click", () => {
    const passwordStr = passwd.value;

    fetch(`/a/v1/${fileId}`, {
      method: "POST",
      body: JSON.stringify({ password: passwordStr }),
      headers: {
        "Content-Type": "application/json",
      },
    }).then((response) => {
      if (!response.ok) {
        location.reload();
        return;
      }

      document.body.removeChild(overlay);
      passwordSubmitted(passwordStr);
    });
  });

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

function passwordSubmitted(password) {
  document
    .getElementById("download")
    .addEventListener("click", () => downloadShare(fileId, password));
}

document
  .getElementById("close")
  .addEventListener("click", () => (location.href = `/~`));

home.addEventListener("click", () => (location.href = "/~"));

getShareDetails(fileId, null, onLoad);
