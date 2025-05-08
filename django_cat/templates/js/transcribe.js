let first_chunk;
let audio_mediaRecorder;
let audio_context, audio_analyser, audio_bandpass, audio_source;
let audio_silenceTimeout;
let audio_chunkStartTime;
let audio_maxDurationInterval;
let audio_silenceInterval;
let audio_isRecording = false;

// Setup bandpass filter for voice frequencies
function setupBandpassFilter() {
    audio_context = new AudioContext();
    audio_analyser = audio_context.createAnalyser();
    audio_analyser.fftSize = 256;
    audio_bandpass = createBandpassFilter(audio_context);
}

// Silence detection via RMS
function checkSilence() {
    const data = new Uint8Array(audio_analyser.frequencyBinCount);
    audio_analyser.getByteFrequencyData(data);
    
    // Calculate RMS only for voice frequencies (80Hz-1kHz)
    const vocalRange = Array.from(data).slice(10, 100);
    const rms = Math.sqrt(vocalRange.reduce((sum, v) => sum + v * v, 0) / vocalRange.length);
    
    if (rms < SILENCE_THRESHOLD_RMS) {
        if (!audio_silenceTimeout) {
            audio_silenceTimeout = setTimeout(() => {
                if (audio_mediaRecorder?.state === 'recording') {
                    forceChunkSplit();
                    updateStatus("Pause detected: chunk sent");

                    // Restart the max duration interval
                    audio_maxDurationInterval.start();
                }
            }, SILENCE_DURATION);
        }
    } else {
        clearTimeout(audio_silenceTimeout);
        audio_silenceTimeout = null;
    }
}

function createBandpassFilter(audio_context) {
    audio_bandpass = audio_context.createBiquadFilter();
    audio_bandpass.type = "bandpass";
    audio_bandpass.frequency.value = 1000;
    audio_bandpass.Q.value = 1;
    return audio_bandpass;
}

// Start recording with filters
async function startRecording(call_when_ready = () => {}) {
    try {
        // Initialize audio context and nodes
        setupBandpassFilter();
        
        // Get user media
        audio_stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Setup audio processing chain for visualization
        audio_microphone = audio_context.createMediaStreamSource(audio_stream);
        audio_microphone.connect(audio_analyser);
        
        // Setup bandpass filter for streaming
        audio_source = audio_context.createMediaStreamSource(audio_stream);
        audio_source.connect(audio_bandpass);
        audio_bandpass.connect(audio_analyser);
        
        // Set up data array for visualization
        audio_waveformData = new Uint8Array(audio_analyser.frequencyBinCount);
        
        // Start drawing waveform
        call_when_ready();
        first_chunk = undefined;
        
        // Initialize MediaRecorder
        audio_mediaRecorder = new MediaRecorder(audio_stream, {
            mimeType: 'audio/webm;codecs=opus',
            bitsPerSecond: 128000
        });
        audio_chunkStartTime = Date.now();

        audio_mediaRecorder.ondataavailable = async (e) => {
            const chunkDuration = Date.now() - audio_chunkStartTime;

            // Set the first chunk
            if (e.data.size > 0 && first_chunk === undefined) {
                first_chunk = e.data;
                // playChunk(first_chunk);
                return;
            }

            // Skip very small chunks
            if (chunkDuration < 10 || e.data.size < 1000) return;
            
            audio_chunkStartTime = Date.now();
            
            // Restart the silence interval
            audio_silenceInterval.start();

            sendChunk(new Blob([first_chunk, e.data], { type: 'audio/webm' }));
            // playChunk(new Blob([first_chunk, e.data], { type: 'audio/webm' }));
        };

        audio_mediaRecorder.onstop = () => {
            if (audio_maxDurationInterval) audio_maxDurationInterval.stop();
            if (audio_silenceInterval) audio_silenceInterval.stop();
            audio_stream.getTracks().forEach(track => track.stop());
        };
        
        // Force split every MAX_CHUNK_DURATION
        audio_maxDurationInterval = createRestartableInterval(() => {
            if (audio_mediaRecorder?.state === 'recording') {
                forceChunkSplit();
            }
        }, MAX_CHUNK_DURATION);

        // Start recording
        audio_mediaRecorder.start();
        audio_isRecording = true;
        updateUIForRecording(true);
        audio_maxDurationInterval.start();

        // Set the first_chunk (blank)
        const firstChunkTimeout = setTimeout(() => {
            audio_mediaRecorder.requestData();
        }, 400);

        // Check silence every 500ms
        audio_silenceInterval = createRestartableTimeout(() => {
            setInterval(checkSilence, 500);
        }, MIN_CHUNK_DURATION);
        audio_silenceInterval.start();

        // Start timer
        audio_startTime = Date.now();
        updateTimer();
        
        return audio_stream;
    } catch (error) {
        console.error("Error starting recording:", error);
        updateStatus("Error: Could not access microphone");
        return null;
    }
}

function playChunk(webmBlob) {
    const audio = new Audio();
    audio.src = URL.createObjectURL(webmBlob);
    audio.controls = true;
    
    // Add to DOM (optional)
    document.body.appendChild(audio);
    
    // Play automatically
    //audio.play().catch(e => console.error("Playback failed:", e));
    
    // Clean up later
    audio.onended = () => URL.revokeObjectURL(audio.src);
}

// Stop recording and visualization
function stopRecording() {
    forceChunkSplit();

    if (audio_mediaRecorder?.state === 'recording') {
        audio_mediaRecorder.stop();
        audio_isRecording = false;
        updateUIForRecording(false);
        updateStatus("Processing complete");
    }

    audio_recorder_popup_dom.hide();
    
    // Stop visualization
    if (audio_animationId) {
        cancelAnimationFrame(audio_animationId);
    }
    
    // Disconnect microphone
    if (audio_microphone) {
        audio_microphone.disconnect();
    }
    
    // Close audio context
    if (audio_context) {
        audio_context.close();
    }
}

function forceChunkSplit() {
    if (audio_mediaRecorder?.state === 'recording') {
        audio_mediaRecorder.requestData();
    }
}

// Send audio chunk for transcription
async function sendChunk(chunk) {
    updateStatus("Processing audio...");
    
    const formData = new FormData();
    formData.append('audio', chunk, `chunk_${Date.now()}.webm`);

    try {
        // Update progress bar
        audio_progress_bar_dom.css('width', '50%');
        
        const response = await fetch("{% url 'chat:api:transcribe' %}", {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            }
        });
        
        // Update progress bar
        audio_progress_bar_dom.css('width', '100%');
        
        if (response.ok) {
            const result = await response.json();
            if (result.status == "success") {
                // Append text to input box
                const currentText = input_textarea_dom.val();
                const newText = currentText ? currentText + " " + result.text : result.text;
                input_textarea_dom.val(newText);
                
                // Trigger input event to enable send button if needed
                input_textarea_dom.trigger('input');
                
                updateStatus("Transcription added");
            } else {
                console.error("Error transcribing chunk:", result.error);
                updateStatus(`Error: ${result.error}`);
            }
        } else {
            const error = await response.json();
            updateStatus(`Error: ${error.error || response.statusText}`);
        }
        
        // Reset progress bar after a delay
        setTimeout(() => {
            audio_progress_bar_dom.css('width', '0%');
        }, 1000);
    } catch (error) {
        console.error("Error sending chunk:", error);
        updateStatus("Error: Could not connect to server");
        audio_progress_bar_dom.css('width', '0%');
    }
}
