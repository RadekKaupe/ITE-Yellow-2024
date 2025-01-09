const errorMessageEl = document.querySelector("#error-message");
const successMessageEl = document.querySelector("#success-message");
if(!errorMessageEl){
    console.log("No rrror message element found.")
}
if(!successMessageEl){
    console.log("No success message element found.")
}
export function writeSuccessMessage(message) {
    errorMessageEl.style.display = "none";
    successMessageEl.textContent = message;
    successMessageEl.style.display = "block";
    successMessageEl.classList.remove("fade-in"); // Trigger reflow to restart the animation void 
    void successMessageEl.offsetWidth; // Re-add the fade-in class 
    successMessageEl.classList.add("fade-in");
}
export function writeErrorMessage(message) {
    successMessageEl.style.display = "none";
    errorMessageEl.textContent = message;
    errorMessageEl.style.display = "block";
    errorMessageEl.classList.remove("fade-in"); // Trigger reflow to restart the animation void 
    void errorMessageEl.offsetWidth; // Re-add the fade-in class 
    errorMessageEl.classList.add("fade-in");
}
