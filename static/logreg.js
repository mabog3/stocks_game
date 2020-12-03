document.addEventListener('DOMContentLoaded', function() {
    if (document.URL.includes('register'))
    {
        pw = document.getElementById("pw")
        pw.addEventListener('change', function() {
            if (pw.value.length < 8) {
                document.getElementById("pwtext").innerHTML = "Password must be at least 8 chracters long"
                document.getElementById("sub").disabled = true;
                pw.classList.add('is-invalid')
            }
            else {
                document.getElementById("pwtext").innerHTML = ""
                document.getElementById("sub").disabled = false;
                pw.classList.remove('is-invalid')
            }
        })

        cf = document.getElementById("cf")
        cf.addEventListener('input', function() {
            if (cf.value != pw.value) {
                document.getElementById("cftext").innerHTML = "Passwords do not match"
                document.getElementById("sub").disabled = true;
                cf.classList.add('is-invalid')
            }
            else {
                document.getElementById("cftext").innerHTML = ""
                document.getElementById("sub").disabled = false;
                cf.classList.remove('is-invalid')
            }
        })
    }

    document.querySelectorAll('input').forEach(item => { //no spaces in any input
        item.addEventListener('input', function() {
            if (item.value.indexOf(' ') >= 0) {
                item.value = item.value.replace(/\s+/g, '');
            }
        })
    })
})