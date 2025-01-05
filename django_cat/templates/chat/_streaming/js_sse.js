// Carica la libreria SSE come modulo
import { SSE } from 'https://cdn.jsdelivr.net/npm/sse.js@2.4.1/lib/sse.min.js';

$(document).on("submit", "#chatForm", handleSubmit);

function startLoadingState() {
    const submitButton = document.getElementById('input-send-message');
    submitButton.disabled = true;
    $("#message-input").val("");
    $("#chat-form-help-text").text("loading...");

    isErrorResponseGenerated = false;
}

function endLoadingState() {
    const submitButton = document.getElementById('input-send-message');
    submitButton.disabled = false;
    $('#message-input').val("");
    $('#message-input').focus();
    $("#chat-form-help-text").text("");

    isWaitingResponse = false;
}

function handleSubmit(e) {
    e.preventDefault();
    
    isWaitingResponse = true;
    isErrorResponseGenerated = false;

    const formData = new FormData(e.target);
    const data = {
        message: formData.get('message'),
        chat_id: formData.get('chat_id')
    };
    const formAction = e.target.action;
    startLoadingState();

    let responses = $("#responses");

    // Create user message
    let userMsg = $("#msg-user-proto").clone(true);
    userMsg.removeAttr("id");
    userMsg.find("div.message").text(`${data.message}`);
    userMsg.show();
    responses.append(userMsg);

    // Create assistant message container
    let assMsg = $("#msg-assistant-proto").clone(true);
    assMsg.removeAttr("id");
    assMsg.show();
    assMsg.find("div.message").text("");
    assMsg.message = "";
    responses.append(assMsg);

    // Effettua una singola chiamata POST con SSE
    // const eventSource = new EventSource(`${formAction}`, {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json',
    //         'X-CSRFToken': document.querySelector('[name="csrfmiddlewaretoken"]').value
    //     },
    //     body: JSON.stringify({
    //         message: data.get('message')
    //     })
    // });

    const eventSource = new SSE(e.target.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name="csrfmiddlewaretoken"]').value,
            'Content-Type': 'application/json',
        },
        payload: JSON.stringify(data)
    });
    
    eventSource.addEventListener("message",  function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.data) {
                // console.log(data.data.length);
                assMsg.message += data.data;

                assMsg.find("div.message").html(convertToHTML(assMsg.message));
            }
        } catch (e) {
            console.error("Error parsing SSE data:", e);
        }
    });

    eventSource.addEventListener('done', function(event) {
        eventSource.close();
        endLoadingState();
        isWaitingResponse = false;
        // Scroll to bottom
        let container = $("#app-container");
        container.animate({ scrollTop: container.find("#app").get(0).scrollHeight }, 500);
    });

    eventSource.addEventListener("error", function(err) {
        console.error("EventSource failed:", err);
        eventSource.close();
        endLoadingState();
        isWaitingResponse = false;
        isErrorResponseGenerated = true;
    });

    eventSource.stream();
}
