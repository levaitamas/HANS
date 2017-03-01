function onClick(id) {
    var e = document.getElementById(id);
    post(e.getAttribute('id'));
}

function chCheck(id) {
    var e = document.getElementById(id);
    if (e.getAttribute('type') == "checkbox") {
        if (e.checked) {
            e.setAttribute('value', 'on');
            if (id.includes("es")) {
                document.getElementById('ec.' +  id.split('.')[1] + '-param').disabled = false;
            }
            if (id.includes("ds")) {
                document.getElementById('DK11').disabled = false;
                document.getElementById('DK12').disabled = false;
                document.getElementById('DK13').disabled = false;
                document.getElementById('DK14').disabled = false;
                document.getElementById('DK15').disabled = false;
            }
        }
        else {
            e.setAttribute('value', 'off');
            if (id.includes("es")) {
                document.getElementById('ec.' + id.split('.')[1] + '-param').disabled = true;
            }
            if (id.includes("ds")) {
                document.getElementById('DK11').disabled = true;
                document.getElementById('DK12').disabled = true;
                document.getElementById('DK13').disabled = true;
                document.getElementById('DK14').disabled = true;
                document.getElementById('DK15').disabled = true;
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
