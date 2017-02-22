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
                document.getElementById('ec_' +  id.split('_')[1] + '_p').disabled = false;
            }
            if (id.includes("ds")) {
                document.getElementById('dk:11').disabled = false;
                document.getElementById('dk:12').disabled = false;
                document.getElementById('dk:13').disabled = false;
                document.getElementById('dk:14').disabled = false;
                document.getElementById('dk:15').disabled = false;
            }
        }
        else {
            e.setAttribute('value', 'off');
            if (id.includes("es")) {
                document.getElementById('ec_' + id.split('_')[1] + '_p').disabled = true;
            }
            if (id.includes("ds")) {
                document.getElementById('dk:11').disabled = true;
                document.getElementById('dk:12').disabled = true;
                document.getElementById('dk:13').disabled = true;
                document.getElementById('dk:14').disabled = true;
                document.getElementById('dk:15').disabled = true;
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
