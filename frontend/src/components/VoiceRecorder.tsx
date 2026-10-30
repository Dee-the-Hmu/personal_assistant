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

    // start Microhpone Access
    // records audio in chunks 
    // combine those audio chunks into a playable audio Blob when stopped
    async function startRecording() {
        try{ 
            const socket = new WebSocket("ws://127.0.0.1:8000/ws"); 

            webSocketRef.current = socket;

            socket.onopen = async () => {
                const stream = await navigator.mediaDevices.getUserMedia({
                    audio : true,
                })
                streamRef.current = stream;
                
                // AudioContext = owns/manages the audio system
                const audioContext = new AudioContext(); 

                console.log("Sample rate: ", audioContext.sampleRate);

                //load our custom AudioProcessor
                // Files inside Vite's `public/` directory are served from the website root `/`.
                // So public/audioProcessor.js is available as /audioProcessor.js.
                await audioContext.audioWorklet.addModule("/audioProcessor.js"); //addModule() returns a promise

                // Turn the microphone MediaStream into a Web Audio source node.
                // creates a node that allows your microphone audio to enter the Web Audio graph.
                //puts your microphone into that Audio system 
                const source = audioContext.createMediaStreamSource(stream); // microphone → MediaStream → source

                // connects to your custom processor
                const worklet = new AudioWorkletNode(
                    audioContext,
                    "audio-processor"
                );

                // Connect nodes in our Web Audio processing graph: Connect microphone → worklet
                source.connect(worklet);

                worklet.port.onmessage = (event) => {
                    console.log(event.data);
                };

                audioContextRef.current = audioContext;
                workletRef.current = worklet;
                setIsRecording(true);
            };
        } catch (error) {
            console.error("could not access microphone: ", error);
        }
    }

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