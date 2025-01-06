import { writeErrorMessage, writeSuccessMessage } from "./messageDisplay.js";
const registerFormEl = document.querySelector("#regisetrForm");

const usernameInputEl = document.querySelector("#username");
const passwordInputEl = document.querySelector("#password");
const confirmPasswordInputEl = document.querySelector("#confirmPassword");

document

    .getElementById("registerForm")
    .addEventListener("submit", async (e) => {
        e.preventDefault();

        const username = usernameInputEl.value;
        const password = passwordInputEl.value;
        const confirmPassword = confirmPasswordInputEl.value;

        if (username.length < 4) {
            const message =
                "Please make the username at least 5 characters long.";
            writeErrorMessage(message);
            return;
        }
        if (password.length < 7 || confirmPassword.length < 7) {
            const message =
                "Please make the password at least 8 characters long.";
            writeErrorMessage(message);
            return;
        }
        if (password !== confirmPassword) {
            const message = "Passwords do not match.";
            writeErrorMessage(message);
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
                    writeErrorMessage(data.error);
                }
                if (data.success) {
                    writeSuccessMessage(data.success);
                }
            }
        } catch (error) {
            const message = "An error occurred. Please try again.";
            writeErrorMessage(message);
        }
    });
