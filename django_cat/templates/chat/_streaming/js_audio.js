<script>
        // Audio Recording Logic
        let mediaRecorder;
        let audioChunks = [];
        const dialog = $("#audio-dialog");
        const recordButton = $("#record-button");
        const recordingStatus = $("#recording-status");
        const responseAudio = $("#response-audio")[0]; // Ottieni l'elemento audio nativo
        let isRecording = false;
        let isWaitingResponse = false;
        let isErrorResponseGenerated = false;
        let isPlayingResponse = false;
        let shouldContinue = true; // Nuova variabile per controllare il flusso

        // Verifica supporto registrazione audio
        function checkMediaRecorderSupport() {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                console.log("getUserMedia not supported");
                recordingStatus.text("Audio recording not supported in this browser");
                recordButton.prop('disabled', true);
                return false;
            }
            return true;
        }

        // Gestione apertura/chiusura modal
        $("#input-mic-button").on("click", () => {
            if (!checkMediaRecorderSupport()) {
                alert("Il tuo browser non supporta la registrazione audio. Usa Chrome, Firefox o Safari aggiornati.");
                return;
            }
            dialog.removeClass("hidden");
        });

        // Chiudi il modal quando si clicca sulla X o fuori dal dialog
        $(document).on("mousedown", (e) => {
            if (dialog.is(":visible") && 
                !$(e.target).closest(".modal-box").length && 
                !$(e.target).closest("#input-mic-button").length &&
                !isRecording) { // Aggiungi controllo per isRecording
                closeModal();
            }
        });

        // Modifica anche il comportamento del pulsante X
        $("#close-modal").on("click", (e) => {
            if (!isRecording) {
                closeModal();
            }
        });

        function closeModal() {
            dialog.addClass("hidden");
            shouldContinue = false; // Imposta il flag a false quando si chiude il modal

            if (isRecording && mediaRecorder) {
                mediaRecorder.stop();
                isRecording = false;
            }

            // Stop audio playback if it's playing
            if (isPlayingResponse && !responseAudio.paused) {
                responseAudio.pause();
                responseAudio.currentTime = 0;
                isPlayingResponse = false;
            }

            recordingStatus.text("Click to start recording");
            recordButton.removeClass("btn-error");
            recordButton.show();
        }

        async function reproduceAudioResponse() {
            try {
                recordingStatus.text("Attendo la risposta dell'assistente...");

                while (isWaitingResponse) {
                    await new Promise(resolve => setTimeout(resolve, 500));
                    if (!shouldContinue) return;
                }

                if (isErrorResponseGenerated || !shouldContinue) {
                    recordingStatus.text("Si è verificato un errore nella generazione della risposta");
                    setTimeout(() => closeModal(), 2000);
                    return;
                }

                recordingStatus.text("Attendo risposta audio...");

                // Controllo se il dialogo è stato chiuso mentre si aspetta la risposta audio
                if (!shouldContinue) return;

                const response = await fetch("{% url 'chat:speak-last-api' chat_id=chat_id %}");
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }

                // Controllo nuovamente prima di iniziare la riproduzione
                if (!shouldContinue) return;

                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);

                recordingStatus.text("Riproduco risposta...");
                isPlayingResponse = true;
                
                responseAudio.src = audioUrl;
                
                // Controlliamo se il dialogo è stato chiuso prima di iniziare la riproduzione
                if (!shouldContinue) {
                    isPlayingResponse = false;
                    return;
                }

                await responseAudio.play();

                // Aspetta che l'audio finisca, con possibilità di interruzione
                await new Promise((resolve, reject) => {
                    responseAudio.onended = () => {
                        isPlayingResponse = false;
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
                        reject(new Error('Audio playback error'));
                    };
                });

                if (shouldContinue) {
                    closeModal();
                }

            } catch (error) {
                console.error('Error playing response:', error);
                isPlayingResponse = false;
                if (shouldContinue) {
                    recordingStatus.text("Errore nella riproduzione della risposta");
                    setTimeout(() => closeModal(), 2000);
                }
            }
        }

        recordButton.on("click", async () => {
            if (!isRecording) {
                try {
                    const constraints = {
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        }
                    };
                    
                    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];

                    mediaRecorder.ondataavailable = (event) => {
                        if (event.data.size > 0) {
                            audioChunks.push(event.data);
                        }
                    };

                    mediaRecorder.onstop = async () => {
                        const tracks = stream.getTracks();
                        tracks.forEach(track => track.stop());
                        
                        shouldContinue = true; // Reset del flag all'inizio del processo

                        // Se il dialogo è stato chiuso, non procedere
                        if (!dialog.is(":visible")) {
                            return;
                        }

                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const formData = new FormData();
                        formData.append('audio', audioBlob);

                        try {
                            recordButton.hide();
                            recordingStatus.text("Sto trascrivendo...");

                            const response = await fetch('{% url "chat:audio-api" %}', {
                                method: 'POST',
                                body: formData,
                                headers: {
                                    'X-CSRFToken': document.querySelector('[name="csrfmiddlewaretoken"]').value
                                }
                            });

                            if (response.ok) {
                                const data = await response.json();
                                
                                if (data.status == "success" && data.text != "") {
                                    console.log(data);

                                    $("#message-input").val(data.text);
                                    
                                    $("#chatForm").submit();
                                    await reproduceAudioResponse();
                                } else {
                                    closeModal();
                                }
                            }
                        } catch (error) {
                            console.error('Error uploading audio:', error);
                            recordingStatus.text("Error uploading audio");
                            recordButton.show();
                        }
                    };

                    mediaRecorder.start();
                    isRecording = true;
                    recordingStatus.text("Recording... Click to stop");
                    recordButton.addClass("btn-error");
                } catch (err) {
                    console.error('Error accessing microphone:', err);
                    recordingStatus.text("Error accessing microphone. Make sure you've granted permission.");
                    recordButton.prop('disabled', true);
                }
            } else {
                mediaRecorder.stop();
                isRecording = false;
                recordingStatus.text("Click to start recording");
                recordButton.removeClass("btn-error");
            }
        });

        // Previeni la propagazione del click sul modal box
        $(".modal-box").on("click", (e) => {
            e.stopPropagation();
        });
    </script>