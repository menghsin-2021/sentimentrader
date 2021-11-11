var signUpTable = document.getElementById("singUpTable");
var signInTable = document.getElementById("signInTable");

function switchToSignIn() {
  signUpTable.className = "d-none flex-column align-items-center col-12";
  signInTable.className = "d-flex flex-column align-items-center col-12";
}

function switchToSignUp() {
  signUpTable.className = "d-flex flex-column align-items-center col-12";
  signInTable.className = "d-none flex-column align-items-center col-12";
}

 function statusChangeCallback(response) {  // Called with the results from FB.getLoginStatus().
    console.log('statusChangeCallback');
    console.log(response);                   // The current login status of the person.
    if (response.status === 'connected') {   // Logged into your webpage and Facebook.
      testAPI();
    } else {                                 // Not logged into your webpage or we are unable to tell.
      document.getElementById('status').innerHTML = 'Please log ' +
        'into this webpage.';
    }
  }