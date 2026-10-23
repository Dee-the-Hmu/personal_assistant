import { useRef, useState } from "react";

export default function VoiceRecorder() {
    const [isRecording, setIsRecording] = useState(false); 

    const recorderRef = useRef<MediaRecorder | null>(null);
    const streamRef = useRef<MediaStream | null>(null);

    async function startRecording() {

        try{ 
            const stream = await navigator.mediaDevices.getUserMedia({
                audio : true,
            });

            streamRef.current = stream;
            
            const recorder = new MediaRecorder(stream); //recorder now knows which stream it should record

            //recorder produces an event whenever an audio chunk becomes available
            //event.data = a Blob (browser obj representing binary data)
            //don't send empty chunks
            recorder.ondataavailable = (event) => {
                if (event.data.size > 0){ //Blob size in bytes
                    console.log(event.data); 
                }
            };

            recorder.start(250); //starts recording, give me recorded audio data in chunks about every 250 millisecond

            recorderRef.current = recorder;
            setIsRecording(true);
        } catch (error) {
            console.error("could not access microphone: ", error);
        }
    }

    function stopRecording() {
        recorderRef.current?.stop(); 

        //get the media (audio) track belonging to the stream
        streamRef.current?.getTracks().forEach((track) => { 
            track.stop();
        });

        recorderRef.current = null; 
        streamRef.current = null; 

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