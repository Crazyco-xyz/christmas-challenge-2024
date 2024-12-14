const loginForm = document.getElementById("loginform"),
  registerForm = document.getElementById("registerform"),
  message = document.getElementById("msg"),
  messageStr = message.getElementsByClassName("message")[0];

function performAPI(endpoint, data) {
  fetch(`/a/v1/${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: data,
  })
    .then(async (response) => {
      const data = await response.json();

      return { ok: response.ok, data };
    })
    .then(({ ok, data }) => {
      if (ok) {
        location.href = data.location;
        return;
      }

      showMessage(data.message);
    });
}

function showMessage(msg) {
  messageStr.innerHTML = msg;
  message.animate({ opacity: 1 }, { duration: 200, fill: "forwards" });
}

function onLogin(event) {
  event.preventDefault();

  let formData = new FormData(loginForm);
  performAPI("login", JSON.stringify(Object.fromEntries(formData)));
}

function onRegister(event) {
  event.preventDefault();

  let formData = new FormData(registerForm);
  performAPI("register", JSON.stringify(Object.fromEntries(formData)));
}

if (loginForm) loginForm.onsubmit = onLogin;
if (registerForm) registerForm.onsubmit = onRegister;
