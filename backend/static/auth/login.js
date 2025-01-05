const loginFormEl = document.querySelector("#loginForm");
const usernameInputEl = document.querySelector("#username");
const passwordInputEl = document.querySelector("#password");

import {writeErrorMessage, writeSuccessMessage} from "./messageDisplay.js";
window.onload = function () {
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get("error");
    if (error) {
        writeErrorMessage(error)
    }
    const success = urlParams.get("success");
    if (success) {
        writeSuccessMessage(success)
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
            writeErrorMessage(data.error)
        }
        if (data.redirect) {
            window.location.href = data.redirect;
        }
        if (data.success) {
            writeSuccessMessage(data.success)
        }
    } catch (error) {
        const message = "An error occurred. Please try again."
        writeErrorMessage(message)
    }
});
