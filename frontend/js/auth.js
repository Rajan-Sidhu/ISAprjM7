const loginForm = document.querySelector("#login-form");
const registerForm = document.querySelector("#register-form");
const errorBox = document.querySelector("#form-error");

function showForm(which) {
  const login = which === "login";
  loginForm.hidden = !login;
  registerForm.hidden = login;
  document.querySelector("#show-login").setAttribute("aria-selected", String(login));
  document.querySelector("#show-register").setAttribute("aria-selected", String(!login));
  errorBox.textContent = "";
}

document.querySelector("#show-login").addEventListener("click", () => showForm("login"));
document.querySelector("#show-register").addEventListener("click", () => showForm("register"));

function go(user) {
  window.location.href = user.role === "admin" ? "admin.html" : "user.html";
}

async function submit(path, form) {
  errorBox.textContent = "";
  const data = Object.fromEntries(new FormData(form));
  const button = form.querySelector("button");
  button.disabled = true;
  try {
    const result = await api(path, {
      method: "POST",
      body: JSON.stringify(data),
    });
    go(result.user);
  } catch (error) {
    errorBox.textContent = error.message;
    button.disabled = false;
  }
}

loginForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submit("/api/auth/login", loginForm);
});

registerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submit("/api/auth/register", registerForm);
});

api("/api/auth/me")
  .then((result) => go(result.user))
  .catch(() => {});
