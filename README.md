# CuppyLLM

[![Node.js](https://img.shields.io/badge/Node.js-v23-green)](https://nodejs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-v7-brightgreen)](https://www.mongodb.com/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-2DD4BF?style=flat&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

CuppyLLM is a lightweight AI chat web app powered by Ollama and Node.js, with persistent chat storage using MongoDB. It supports multiple chat sessions and formatted code block responses.

---

## Features

- Multi-chat session support (like ChatGPT)
- Persistent storage using MongoDB
- Code block formatting with newline preservation
- Works with Ollama (local models like mistral, llama2, etc.)
- Built using modern Node.js (v23+) with native `fetch` support

---

## Tech Stack

- Backend: Node.js, Express, MongoDB, Mongoose
- Frontend: Vanilla JavaScript (or use your own)
- AI Engine: Ollama (local large language model server)

---

## Setup Instructions

1. **Install dependencies:**

```
npm install
```

2. **Start an Ollama model (example):**

```
ollama run llama2
```

3. **Create a `.env` file** in the root directory with:

```
PORT=3001
OLLAMA_URL=http://localhost:11434
MONGODB_URI=mongodb://localhost:27017/ollama_chat
```

4. **Start the app:**

```
npm start
```


The backend will run at: `http://localhost:3001`

---

## API Overview

- **Create a new chat:**
- `POST /api/new-chat`

- **Send a message to chat:**
- `POST /api/chat/:chatId/message`
- Body JSON: `{ "message": "Your question here" }`

- **Get messages in a chat:**
- `GET /api/chat/:chatId`

---

## Frontend Integration Notes

- Format message content using triple backticks \`\`\` to indicate code blocks.
- Use CSS like `white-space: pre-wrap` to preserve line breaks in code.
- Add `escapeHTML()` in JavaScript to prevent XSS in code blocks.

---

## Testing Tips

- Ensure `OLLAMA_URL` points to a running model at `http://localhost:11434`
- Use Postman or curl to test endpoints
- MongoDB must be running locally or via MongoDB Atlas

---

## License

MIT License  
Copyright (c) PerrierBottle

---

## Contributing

Pull requests are welcome. If you find bugs or want new features, feel free to open an issue.
