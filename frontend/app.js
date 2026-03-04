const { useState } = React;

const API_URL = 'http://localhost:8000/api/chat';

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Bonjour 👋 Je suis l'agent CDG. Dites-moi votre besoin support (accès, incident, ticket).",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  async function sendMessage(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) throw new Error(`Erreur API: ${response.status}`);

      const data = await response.json();
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            "Je n'arrive pas à joindre le backend. Vérifiez que l'API FastAPI tourne sur le port 8000.",
        },
      ]);
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="layout">
      <h1>Support conversationnel CDG</h1>
      <section className="chatbox" aria-live="polite">
        {messages.map((message, index) => (
          <article key={index} className={`message ${message.role}`}>
            <strong>{message.role === 'assistant' ? 'Agent CDG' : 'Vous'} :</strong>{' '}
            <span>{message.content}</span>
          </article>
        ))}
      </section>

      <form onSubmit={sendMessage} className="composer">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ex: Je n'arrive pas à me connecter"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? 'Envoi...' : 'Envoyer'}
        </button>
      </form>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
