export default function VoiceRecorder() {
    async function startRecording() {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio : true,
        });
        
        console.log(stream); //for us, Devs 
    }

    return (
        <button onClick={startRecording}> 
            Start microphone
        </button>
    );
}