function onClick(id) {
    var e = document.getElementById(id);
    post(e.getAttribute('id'));
}

function chCheck(id) {
    var e = document.getElementById(id);
    if (e.getAttribute('type') == "checkbox") {
        if (e.checked) {
            e.setAttribute('value', 'on');
            if (id.includes("ec")) {
                document.getElementById(id + '_p').disabled = false;
            }
        }
        else {
            e.setAttribute('value', 'off');
            if (id.includes("ec")) {
                document.getElementById(id + '_p').disabled = true;
            }
        }
    }
    post(e.getAttribute('id'), e.getAttribute('value'));
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
