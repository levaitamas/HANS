function thanks() {
    var msg = "";
    var reply = document.getElementById("reply");
    switch(reply.innerHTML){
        case "Please press the button above!": msg = "Wait for the MAGIC!"; break;
        case "Wait for the MAGIC!": msg = "Be patient, please."; break;
        case "Be patient, please.": msg = "Don't force me to go HARDCORE!"; break;
        case "Don't force me to go HARDCORE!": msg = "WOW! VERYHARDCORE! MUCH HANS!"; break;
        default: msg = "Wait for the MAGIC!";
    }
    reply.innerHTML = msg;
}

function onClick(id) {
    var e = document.getElementById(id);
    post(e.getAttribute('id'));
    thanks();
}

function chValue(id, nvalue) {
    var e = document.getElementById(id);
    post(e.getAttribute('id'), nvalue);
}

function post(id) {
    var formData = new FormData();
    formData.append('id', id);
    var request = new XMLHttpRequest();
    request.open("POST", "/");
    request.send(formData);
}

function post(id, value) {
    var formData = new FormData();
    formData.append('id', id);
    formData.append('value', value);
    var request = new XMLHttpRequest();
    request.open("POST", "/");
    request.send(formData);
}