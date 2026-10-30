import VoiceRecorder from "./components/VoiceRecorder";

export default function App() {

  async function testBackend() {
    const response = await fetch("http://127.0.0.1:8000/hello");
    const data = await response.json();

    console.log(data);
  }

  /*
  creates a websocket connection (new WebSocket(...))

  socket.onopen = runs when the connection is successfully opened
    socket.send() sends data to the backend
    
  sockent.onmessage = runs whenever the backend sends data back
  */
  function testWebSocket() {
    const socket = new WebSocket("ws://127.0.0.1:8000/ws");

    socket.onopen = () => { //when the connection is successfully opened, run this function (WebSocket connection establishment is asynchornous //shouldn't assume socket.send() is safe, use onopen instead)
      console.log("WebSocket connected"); 
      socket.send("Hello from React/Frontend");
    };

    socket.onmessage = (event) => { //whenever the backend sends something 
      console.log("Backend: ", event.data);
    };
  }


  return (
    <main>
      <h1>Personal Assistant</h1>
      <VoiceRecorder />

      <button onClick={testBackend}>
        Test Backend
      </button>

      <button onClick={testWebSocket}>
        Test WebSocket
      </button>
    </main>
  );
}