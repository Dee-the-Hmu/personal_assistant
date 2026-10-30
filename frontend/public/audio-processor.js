

/*
our custom Audio Processr based on the browser's AudioWorkletProcessor

the browser Repeatedly calls 
    - process(inputs)
    as audio arrives 

    inputs = contain audio channels 

    only use input[0] for monospeech (where as Stereo = 2 channels (left and right))

    this.port.postMessage(samples) = sends those samples from the AudioWorklet to our normal frontend code

    return true = keeps this audio processor alive and continue processing

*/
class AudioProcessor extends AudioWorkletProcessor{
    process(inputs) {
        const input = inputs[0]; //inputs = array of audio inputs passed by the browser

        if (input.length > 0){
            const samples = input[0];  //only keep the first audio channel for monospeech
            this.port.postMessage(samples); 
        }
        return true;  //tell the audio process to say active 
    }
    
}

//register the processor under the name "audio-processor" so VoiceRecorder.tsx can create it later
registerProcessor("audio-processor", AudioProcessor);