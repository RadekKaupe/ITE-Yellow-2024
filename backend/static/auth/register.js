const registerFormEl = document.querySelector("#regisetrForm");

const errorMessageEl = document.querySelector("#error-message");
const usernameInputEl = document.querySelector("#username")
const passwordInputEl = document.querySelector("#password")
const confirmPasswordInputEl = document.querySelector("#confirmPassword")
document
    .getElementById("registerForm")
    .addEventListener("submit", async (e) => {
        e.preventDefault();

        const username = usernameInputEl.value;
        const password = passwordInputEl.value;
        const confirmPassword = confirmPasswordInputEl.value;

        if (username.length < 4) {
            errorMessageEl.style.color = "red";
            errorMessageEl.textContent =
                "Please make the username at least 5 characters long.";
            errorMessageEl.style.display = "block";
            return;
        }
        if (password.length < 7 || confirmPassword.length < 7) {
            errorMessageEl.style.color = "red";
            errorMessageEl.textContent =
                "Please make the password at least 8 characters long.";
            errorMessageEl.style.display = "block";
            return;
        }
        if (password !== confirmPassword) {
            errorMessageEl.style.color = "red";
            errorMessageEl.textContent = "Passwords do not match";
            errorMessageEl.style.display = "block";
            return;
        }

        try {
            const response = await fetch("/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: new URLSearchParams({
                    username: username,
                    password: password,
                }),
            });

            if (response.redirected) {
                window.location.href = response.url;
            } else {
                const data = await response.json();
                if (data.error) {
                    errorMessageEl.textContent = data.error;
                    errorMessageEl.style.display = "block";
                    errorMessageEl.style.color = "red";
                }
                if (data.success) {
                    errorMessageEl.textContent = data.success;
                    errorMessageEl.style.display = "block";
                    errorMessageEl.style.color = "green";
                }
            }
        } catch (error) {
            errorMessageEl.textContent = "An error occurred. Please try again.";
            errorMessageEl.style.display = "block";
        }
    });
