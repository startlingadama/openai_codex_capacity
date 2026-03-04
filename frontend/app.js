const { useState } = React;

const API_BASE = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [token, setToken] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState('login');
  const [conversationId, setConversationId] = useState(null);

  async function authSubmit(event) {
    event.preventDefault();
    const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register';
    const payload = mode === 'login'
      ? { username, password }
      : { username, password, role: 'user' };

    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      alert('Authentification échouée');
      return;
    }

    const data = await response.json();
    setToken(data.token);
    setMessages([
      {
        role: 'assistant',
        content: `Bienvenue ${data.username} 👋. Je suis prêt pour vos demandes support CDG.`,
        sources: [],
      },
    ]);
  }

  async function sendMessage(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading || !token) return;

    setMessages((prev) => [...prev, { role: 'user', content: text, sources: [] }]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: text, conversation_id: conversationId }),
      });

      if (!response.ok) throw new Error(`Erreur API: ${response.status}`);

      const data = await response.json();
      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `[${data.category}] ${data.reply}`,
          sources: data.sources || [],
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: "Erreur backend. Vérifiez l'API FastAPI sur le port 8000.",
          sources: [],
        },
      ]);
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <button className="chat-fab" onClick={() => setIsOpen((prev) => !prev)} aria-label="Ouvrir le chat CDG">
        {isOpen ? '✕' : '💬'}
      </button>

      {isOpen && (
        <aside className={`chat-panel ${isExpanded ? 'expanded' : ''}`}>
          <header className="chat-header">
            <div>
              <h1>Assistant CDG</h1>
              <p>Support conversationnel</p>
            </div>
            <div className="chat-actions">
              <button type="button" className="secondary" onClick={() => setIsExpanded((prev) => !prev)}>
                {isExpanded ? 'Réduire' : 'Étendre 1/2 écran'}
              </button>
            </div>
          </header>

          {!token ? (
            <form onSubmit={authSubmit} className="auth-form">
              <h2>{mode === 'login' ? 'Connexion' : 'Créer un compte'}</h2>
              <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Nom utilisateur" required />
              <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mot de passe" type="password" required />
              <button type="submit">{mode === 'login' ? 'Se connecter' : "S'inscrire"}</button>
              <button type="button" className="secondary" onClick={() => setMode((m) => (m === 'login' ? 'register' : 'login'))}>
                {mode === 'login' ? "Créer un compte" : 'Déjà un compte ?'}
              </button>
            </form>
          ) : (
            <>
              <section className="chatbox" aria-live="polite">
                {messages.map((message, index) => (
                  <article key={index} className={`message ${message.role}`}>
                    <strong>{message.role === 'assistant' ? 'Agent CDG' : 'Vous'} :</strong>{' '}
                    <span>{message.content}</span>
                    {message.sources?.length > 0 && (
                      <ul className="sources">
                        {message.sources.map((source, i) => (
                          <li key={i}>
                            <a href={source.url} target="_blank" rel="noreferrer">{source.title || source.url}</a>
                          </li>
                        ))}
                      </ul>
                    )}
                  </article>
                ))}
              </section>
              <form onSubmit={sendMessage} className="composer">
                <input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="Décrivez votre problème"
                  disabled={loading}
                />
                <button type="submit" disabled={loading || !input.trim()}>{loading ? 'Envoi...' : 'Envoyer'}</button>
              </form>
            </>
          )}
        </aside>
      )}
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
