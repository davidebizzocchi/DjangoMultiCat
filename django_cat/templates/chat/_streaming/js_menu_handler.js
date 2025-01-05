let currentAudioUrl = null;  // Aggiungi questa variabile all'inizio del file

$(document).on("click", "div.tooltip.tooltip-bottom", async function(e) {
    let target = $(e.currentTarget);
    let type = target.data("tip").toLowerCase();
    let messageElement = target.closest('.chat-footer').prev('.chat-bubble').find('.message.markdown');
    let text_message = messageElement.text().trim();

    if (type === "copy") {
        try {
            await navigator.clipboard.writeText(text_message);
            
            // Feedback opzionale all'utente
            alert("Testo copiato negli appunti!");
        } catch (error) {
            console.error('Errore durante la copia:', error);
            alert("Impossibile copiare il testo");
        }
    }
        
    if (type === "volume") {
        try {
            console.log("Pressed volume button");
            
            dialog.removeClass("hidden");
            recordButton.hide();
            shouldContinue = true;

            recordingStatus.text("Attendo la risposta dell'assistente...");

            const response = await fetch(`{% url 'chat:speak-api' %}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    text: text_message
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const audioBlob = await response.blob();
            
            // Revoca l'URL precedente se esiste
            if (currentAudioUrl) {
                URL.revokeObjectURL(currentAudioUrl);
            }
            currentAudioUrl = URL.createObjectURL(audioBlob);

            recordingStatus.text("Riproduco risposta...");
            isPlayingResponse = true;
            
            responseAudio.src = currentAudioUrl;
            
            // Controlliamo se il dialogo è stato chiuso prima di iniziare la riproduzione
            if (!shouldContinue) {
                isPlayingResponse = false;
                return;
            }

            await responseAudio.play();

            // Aspetta che l'audio finisca, con possibilità di interruzione
            await new Promise((resolve, reject) => {
                responseAudio.onended = () => {
                    clearInterval(checkInterval);
                    isPlayingResponse = false;
                    // Revoca l'URL quando l'audio termina
                    if (currentAudioUrl) {
                        URL.revokeObjectURL(currentAudioUrl);
                        currentAudioUrl = null;
                    }
                    resolve();
                };
                
                // Controlliamo periodicamente se dobbiamo interrompere
                const checkInterval = setInterval(() => {
                    if (!shouldContinue) {
                        clearInterval(checkInterval);
                        isPlayingResponse = false;
                        reject(new Error('Playback interrupted'));
                    }
                }, 100);

                // Puliamo l'intervallo quando l'audio finisce
                responseAudio.onended = () => {
                    clearInterval(checkInterval);
                    isPlayingResponse = false;
                    resolve();
                };

                responseAudio.onerror = () => {
                    clearInterval(checkInterval);
                    // Revoca l'URL anche in caso di errore
                    if (currentAudioUrl) {
                        URL.revokeObjectURL(currentAudioUrl);
                        currentAudioUrl = null;
                    }
                    reject(new Error('Audio playback error'));
                };
            });

            if (shouldContinue) {
                closeModal();
            }

        } catch (error) {
            // Revoca l'URL in caso di errore nel try-catch
            if (currentAudioUrl) {
                URL.revokeObjectURL(currentAudioUrl);
                currentAudioUrl = null;
            }
            console.error('Error in tooltip click handler:', error);
            // Qui puoi aggiungere una notifica all'utente se necessario
        }
    }
});