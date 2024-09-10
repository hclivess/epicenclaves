$(document).ready(function() {
    var socket = new WebSocket((window.location.protocol === "https:" ? "wss://" : "ws://") + window.location.host + "/ws/chat");

    socket.onmessage = function(event) {
        var messageData = JSON.parse(event.data);
        var user = messageData.user;
        var text = messageData.text;
        $("#messages").append("<p><strong>" + user + ":</strong> " + text + "</p>");
        $("#messages").scrollTop($("#messages")[0].scrollHeight);
    };

    $("#send-button").click(function() {
        sendMessage();
    });

    $("#message-input").keypress(function(event) {
        if (event.which === 13) {
            sendMessage();
        }
    });

    function sendMessage() {
        var message = $("#message-input").val().trim();
        if (message !== "") {
            socket.send(JSON.stringify({text: message}));
            $("#message-input").val("");
        }
    }
});