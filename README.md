﻿# RemodelAI - AI-Powered Renovation Intelligence

> Transform renovation planning from weeks of uncertainty to 60 seconds of clarity.

[![Demo Day 2025](https://img.shields.io/badge/Demo%20Day-2025-blue)](https://github.com/jfrost1011/remodel-ai)
[![Next.js](https://img.shields.io/badge/Next.js-15.0-black)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org/)

## 🎯 The Problem We Solve

Every year, 3 million homeowners face renovation paralysis:
- 70% of renovations go over budget
- Average overrun: $16,000
- Total market inefficiency: $4.2B annually

## 🚀 Our Solution

RemodelAI delivers instant, accurate renovation estimates using:
- **📸 Image Analysis**: Upload photos of your current kitchen and inspiration
- **🎤 Voice Input**: Describe your vision naturally with speech-to-text
- **🤖 AI Intelligence**: Multi-agent system analyzing local market data
- **📊 Instant Estimates**: Detailed cost breakdowns in 60 seconds

## ✨ Key Features

### For Homeowners
- **No More Guessing**: Get accurate estimates before calling contractors
- **Voice-First Interface**: Simply speak your renovation dreams
- **Visual Intelligence**: Our AI understands your space from photos
- **Local Accuracy**: California-specific pricing (San Diego & Los Angeles)
- **PDF Reports**: Professional estimates to share with contractors

### Technical Highlights
- **Multi-Modal AI**: OpenAI Vision + Anthropic Claude integration
- **Real-Time Processing**: Voice transcription with Web Speech API
- **Smart Caching**: 1-hour client-side cache for instant responses
- **Responsive Design**: Works seamlessly on mobile and desktop

## 🏗️ Architecture Overview

```
Frontend (Next.js 15 + React 19)
          ↓
    API Gateway (FastAPI)
          ↓
   Multi-Agent AI System
    ├── Vision Analysis (OpenAI)
    ├── Cost Estimation (RAG + Pinecone)
    └── Conversation (Anthropic Claude)
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and Python 3.11+
- OpenAI API Key
- Anthropic Claude API Key

### Frontend Setup
```bash
cd remodel-ai-frontend
npm install
npm run dev
```

### Backend Setup
```bash
cd remodel-ai-backend
pip install -r requirements.txt
python main.py
```

## 🎮 Live Demo Features

### 1. **Voice-First Experience**
- Click microphone → speak naturally
- Real-time speech-to-text transcription
- "I want to remodel my kitchen with modern appliances"

### 2. **Visual Intelligence**
- Upload current space photos
- AI analyzes room type, condition, square footage
- Upload inspiration images for style matching

### 3. **Instant Estimates**
- Detailed cost breakdowns (labor, materials, permits)
- Timeline projections
- Confidence scoring
- PDF export for contractors


## 🔒 Enterprise Features
- Multi-market expansion framework
- Contractor network integration
- Real-time material pricing APIs
- Advanced analytics dashboard

---

*Built with ❤️ for homeowners who deserve better renovation planning*
