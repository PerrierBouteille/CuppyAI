// server.js
import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import dotenv from 'dotenv';
import { v4 as uuidv4 } from 'uuid';
import mongoose from 'mongoose';

dotenv.config();

const app = express();
app.use(cors());
app.use(bodyParser.json());

const { MONGODB_URI, PORT = 3001, OLLAMA_URL } = process.env;

// --- Mongoose models ---
mongoose.connect(MONGODB_URI, { useNewUrlParser: true, useUnifiedTopology: true });
const ChatSchema = new mongoose.Schema({
  _id: { type: String, default: uuidv4 },
  messages: [{ role: String, content: String }],
  createdAt: { type: Date, default: Date.now }
});
const Chat = mongoose.model('Chat', ChatSchema);

// --- Routes ---

// New chat
app.post('/api/new-chat', async (_, res) => {
  const chat = new Chat();
  await chat.save();
  res.json({ chatId: chat._id });
});

// Get chat
app.get('/api/chat/:chatId', async (req, res) => {
  const chat = await Chat.findById(req.params.chatId);
  if (!chat) return res.status(404).send('Chat not found');
  res.json(chat.messages);
});

// Send message
app.post('/api/chat/:chatId/message', async (req, res) => {
    const { message } = req.body;
    const chat = await Chat.findById(req.params.chatId);
    if (!chat) return res.status(404).send('Chat not found');

    chat.messages.push({ role: 'user', content: message });

  // Call Ollama
    const ollamaRes = await fetch(`${OLLAMA_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            model: 'llama2',
            messages: chat.messages,
            stream: false
        })
    });
    const ollamaData = await ollamaRes.json();

    if (!ollamaRes.ok || !ollamaData?.message?.content) {
    console.error('Ollama error:', ollamaData);
    return res.status(500).json({ error: 'Failed to get response from Ollama' });
    }

    chat.messages.push({ role: 'assistant', content: ollamaData.message.content });

    await chat.save();
    res.json({ response: ollamaData.message.content });
});

// Delete chat
app.post('/api/chat/:chatId/delete', async (req, res) => {
  try {
    const chat = await Chat.findByIdAndDelete(req.params.chatId);
    if (!chat) return res.status(404).send('Chat not found');
    chat.deleteOne();
    res.sendStatus(204);
  } catch (error) {
    console.error('Error deleting chat:', error);
    res.status(500).json({ error: 'Failed to delete chat' });
  }
});


app.listen(PORT, () => console.log(`Server on ${PORT}`));
