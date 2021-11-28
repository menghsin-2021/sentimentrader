const signUpTable = document.getElementById("singUpTable");
const signInTable = document.getElementById("signInTable");

const inputs = document.querySelectorAll('input')

function switchToSignIn() {
  signUpTable.className = "d-none flex-column align-items-center col-12";
  signInTable.className = "d-flex flex-column align-items-center col-12";
}

function switchToSignUp() {
  signUpTable.className = "d-flex flex-column align-items-center col-12";
  signInTable.className = "d-none flex-column align-items-center col-12";
}

inputs.forEach( input => {
input.addEventListener('input', function() {
    if (input.checkValidity()) {
        input.classList.add('is-valid')
        input.classList.remove('is-invalid')
    } else {
        input.classList.remove('is-valid')
        input.classList.add('is-invalid')
        }
    })
})