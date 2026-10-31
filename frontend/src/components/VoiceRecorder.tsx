import { useRef, useState } from "react";

/*
returns React Component that records microphone audio
- stores the recorded chunks
- allow playback
*/
export default function VoiceRecorder() {
    const [isRecording, setIsRecording] = useState(false); 

    const streamRef = useRef<MediaStream | null>(null);
    const webSocketRef = useRef<WebSocket | null>(null); 

    const audioContextRef = useRef<AudioContext | null>(null);
    const workletRef = useRef<AudioWorkletNode | null>(null);

    // Stores PCM samples until we have enough to send one useful chunk.
    const pcmBufferRef = useRef<Int16Array[]>([]); // Int16Array = typed array containing signed 16-bit integers

    // Converts browser Float32 audio samples into signed 16-bit PCM.
    function float32ToPCM16(samples: Float32Array) : Int16Array {
        const pcm = new Int16Array(samples.length);

        for (let i = 0; i < samples.length; i++){
            // Clamp the value so it cannot exceed the valid -1 to +1 range.
            const sample = Math.max(-1, Math.min(1, samples[i]));
            // We use different multipliers because signed Int16 ranges from
            // -32768 to +32767.
            pcm[i] = sample < 0
                ? sample * 32768
                : sample * 32767;
        }
        return pcm;
    }

    async function startRecording() {
    try { 
        const socket = new WebSocket("ws://127.0.0.1:8000/ws"); 
        webSocketRef.current = socket;

        // onopen runs after the WebSocket connection is successfully established.
        socket.onopen = async () => {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
            });

            streamRef.current = stream;
            
            // AudioContext = owns/manages the Web Audio system.
            const audioContext = new AudioContext({
                sampleRate: 16000,
            }); 

           console.log("Actual sample rate:", audioContext.sampleRate);

            // Load our custom AudioProcessor.
            // Files inside Vite's public/ directory are served from the website root "/".
            // So public/audioProcessor.js is available as /audioProcessor.js.
            // addModule() returns a Promise, so we await it.
            await audioContext.audioWorklet.addModule("/audioProcessor.js");

            // Turn the microphone MediaStream into a Web Audio source node.
            // This allows microphone audio to enter the Web Audio graph.
            // microphone → MediaStream → source
            const source = audioContext.createMediaStreamSource(stream);

            // Create the main-thread interface to our custom AudioWorklet processor.
            // "audio-processor" must match the name registered in audioProcessor.js.
            const worklet = new AudioWorkletNode(
                audioContext,
                "audio-processor"
            );

            // Connect microphone → worklet.
            // Audio now flows:
            // microphone → MediaStream → source → AudioWorklet
            source.connect(worklet);

            // 0.08 seconds = 80 ms.
            // Deepgram recommends ~80 ms chunks for Flux.
            const samplesPerChunk = Math.floor(
                audioContext.sampleRate * 0.5
            );

            // onmessage runs EVERY TIME audioProcessor.js sends us
            // another Float32Array of microphone samples.
            worklet.port.onmessage = (event) => {
                // `as Float32Array` is a TypeScript type assertion:
                // we are telling TypeScript what type event.data contains.
                const floatSamples = event.data as Float32Array;

                // Convert Float32 microphone samples → signed PCM16 samples.
                const pcmSamples = float32ToPCM16(floatSamples);

                // Add this small block to our buffer.
                pcmBufferRef.current.push(pcmSamples);

                // Determine how many samples are currently buffered.
                //
                // reduce() combines all elements into one result:
                // total = running total
                // chunk = current Int16Array
                const bufferedSamples = pcmBufferRef.current.reduce(
                    (total, chunk) => total + chunk.length,
                    0
                );

                // Once we have approximately 100 ms of audio, combine and send it.
                if (bufferedSamples >= samplesPerChunk) {

                    // Create one Int16Array large enough to hold
                    // all currently buffered blocks.
                    const combined = new Int16Array(bufferedSamples);

                    let offset = 0;

                    // forEach runs this function once for every buffered chunk.
                    pcmBufferRef.current.forEach((chunk) => {
                        // .set() copies chunk into combined starting at offset.
                        combined.set(chunk, offset);

                        offset += chunk.length;
                    });

                    // readyState tells us the WebSocket's current state.
                    // Only send if the connection is OPEN.
                    if (socket.readyState === WebSocket.OPEN) {
                        // .buffer gives us the underlying binary ArrayBuffer.
                        // WebSocket sends it as binary data.
                        socket.send(combined.buffer); //send the raw PCM audio bytes through the WebSocket.
                    }

                    // These samples were sent, so reset the buffer.
                    pcmBufferRef.current = []; 
                }
            };

            socket.onmessage = (event) => {
                const message = JSON.parse(event.data); //JSON string -> javascript 

                if (message.type === "assistant_chunk"){
                    console.log("Assistant chunk: ", message.text);
                }

                if(message.type === "assistant_done"){
                    console.log("Assistant response complete");
                }
                

            };

            // Save these so stopRecording() can access and clean them up.
            audioContextRef.current = audioContext;
            workletRef.current = worklet;

            setIsRecording(true);
        };
            
    } catch (error) {
        console.error("could not access microphone: ", error);
    }
}



    // start Microhpone Access
    // records audio in chunks 
    // combine those audio chunks into a playable audio Blob when stopped
 
    function stopRecording() {

        workletRef.current?.disconnect();

        //get the media (audio) track belonging to the stream
        streamRef.current?.getTracks().forEach((track) => { 
            track.stop();
        });

        webSocketRef.current?.close(); //tells both frontend and backend to stop the WebSocket Connection

        streamRef.current = null; 
        webSocketRef.current = null; 
        audioContextRef.current = null;
        workletRef.current = null; 

        setIsRecording(false);
    }

    return (
        <div>
            <p>{isRecording ? "Recording..." : "Not recording"}</p>
            <button onClick={startRecording} disabled={isRecording}> 
                Start 
            </button>

            <button onClick={stopRecording} disabled={!isRecording}>
                Stop
            </button>

            
        </div>
    );  
}