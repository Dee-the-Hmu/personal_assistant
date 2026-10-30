import VoiceRecorder from "./components/VoiceRecorder";

export default function App() {

  async function testBackend() {
    const response = await fetch("http://127.0.0.1:8000/hello")
    const data = await response.json();

    console.log(data);
  }


  return (
    <main>
      <h1>Personal Assistant</h1>
      <VoiceRecorder />

      <button onClick={testBackend}>
        Test Backend
      </button>
    </main>
  );
}