import { writeErrorMessage, writeSuccessMessage } from "./messageDisplay.js";
const loginFormEl = document.querySelector("#loginForm");
const usernameInputEl = document.querySelector("#username");
const passwordInputEl = document.querySelector("#password");

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
}
const logoutMessage = decodeURIComponent(getCookie("logout_message"));
console.log(logoutMessage);
try {
    const data = JSON.parse(logoutMessage);
    if (data.success) {
        writeSuccessMessage(data.success); // Clear the cookie after handling the message
        document.cookie =
            "logout_message=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    }

    if (data.error) {
        writeErrorMessage(data.error); // Clear the cookie after handling the message
        document.cookie =
            "logout_message=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    }
} catch (e) {
    console.error("Error:", e);
}
window.onload = function () {
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get("error");
    if (error) {
        writeErrorMessage(error);
    }
    const success = urlParams.get("success");
    if (success) {
        writeSuccessMessage(success);
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
            writeErrorMessage(data.error);
        }
        if (data.redirect) {
            console.log("I should redirect?");
            console.log(response.redirect);
            window.location.href = data.redirect;
        }
        if (data.success) {
            writeSuccessMessage(data.success);
        }
    } catch (error) {
        const message = "An error occurred. Please try again.";
        writeErrorMessage(message);
    }
});
