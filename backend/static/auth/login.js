const loginFormEl = document.querySelector("#loginForm")
const errorMessageEl = document.querySelector("#error-message");
const usernameInputEl = document.querySelector("#username")
const passwordInputEl = document.querySelector("#password")
window.onload = function () {
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get("error");
    if (error) {
        errorMessageEl.textContent = error;
        errorMessageEl.style.display = "block";
    }
};
loginFormEl.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = usernameInputEl.value;
    const password = passwordInputEl.value;

    try {
        const response = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams({
                username: username,
                password: password,
            }),
        });
        console.log(response);
        const data = await response.json();
        console.log(data);
        if (data.error) {
            errorMessageEl.textContent = data.error;
            errorMessageEl.style.display = "block";
        }
        if (data.redirect) {
            window.location.href = data.redirect;
        }
    } catch (error) {
        errorMessageEl.textContent = "An error occurred. Please try again.";
        errorMessageEl.style.display = "block";
    }
});
