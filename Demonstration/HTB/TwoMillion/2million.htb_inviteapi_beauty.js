HTTP / 1.1 200 OK
Server: nginx
Date: Sat, 11 Apr 2026 06: 35: 23 GMT
Content - Type: application / javascript;
charset = utf - 8
Content - Length: 637
Last - Modified: Fri, 02 Jun 2023 16: 15: 28 GMT
Connection: keep - alive
ETag: "647a15a0-27d"
Accept - Ranges: bytes

function verifyInviteCode(code) {
    var formData = {
        "code": code
    };
    $.ajax({
        type: "POST",
        dataType: "json",
        data: formData,
        url: '/api/v1/invite/verify',
        success: function(response) {
            console.log(response)
        },
        error: function(response) {
            console.log(response)
        }
    })
}

function makeInviteCode() {
    $.ajax({
        type: "POST",
        dataType: "json",
        url: '/api/v1/invite/how/to/generate',
        success: function(response) {
            console.log(response)
        },
        error: function(response) {
            console.log(response)
        }
    })
}