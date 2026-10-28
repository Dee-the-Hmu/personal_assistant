import { useRef, useState } from "react";

/*
returns React Component that records microphone audio
- stores the recorded chunks
- allow playback
*/
export default function VoiceRecorder() {
    const [isRecording, setIsRecording] = useState(false); 

    const recorderRef = useRef<MediaRecorder | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    const [audioURL, setAudioURL] = useState<string | null>(null); 

    // start Microhpone Access
    // records audio in chunks 
    // combine those audio chunks into a playable audio Blob when stopped
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
                    audioChunksRef.current.push(event.data);

                    //TODO:  send each audio chunk to backend here
                }
            };

            //combine chunks into final Blob
            recorder.onstop = () => {
                const audioBlob = new Blob(audioChunksRef.current, {
                    type : recorder.mimeType
                });

                const url = URL.createObjectURL(audioBlob);
                setAudioURL(url); 
                audioChunksRef.current = []; 
            };

            recorder.start(250); //starts recording, give me recorded audio data in chunks about every 250 millisecond

            recorderRef.current = recorder;
            setIsRecording(true);
        } catch (error) {
            console.error("could not access microphone: ", error);
        }
    }

    function stopRecording() {
        recorderRef.current?.stop();  //this triggers recorder.onstop

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

            {audioURL && (<audio src={audioURL} controls /> )}
        </div>
    );
}