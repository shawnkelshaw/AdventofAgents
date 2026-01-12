# Vehicle Trade-In React Client

A React + TypeScript + shadcn/ui frontend for the Vehicle Trade-In Multi-Agent System.

## Overview

This client provides a modern, interactive UI for the vehicle trade-in workflow, connecting to the Orchestrator A2A server and rendering A2UI components.

## Features

- **A2UI Rendering**: Converts A2UI JSON to React/shadcn components
- **A2A Integration**: Uses `@a2a-js/sdk` for server communication
- **Interactive Forms**: Vehicle info collection, booking forms
- **Dynamic UI**: Time slot selection, estimate cards, confirmation screens
- **Responsive Design**: Works on desktop and mobile

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Open http://localhost:5176

**Note:** Ensure the Orchestrator A2A server is running at http://localhost:10010:
```bash
cd ../orchestrator_agent
uv run python server.py
```

## Project Structure

```
react-client/
├── src/
│   ├── components/
│   │   ├── a2ui/
│   │   │   └── A2UIRenderer.tsx   # A2UI JSON renderer
│   │   ├── ui/                     # shadcn/ui components
│   │   └── ChatInterface.tsx       # Main chat UI
│   ├── App.tsx                     # App entry point
│   └── main.tsx                    # React entry point
├── package.json
└── vite.config.ts
```

## A2UI Components Supported

- **Card**: Styled content container
- **Row/Column**: Flex layout components
- **Text**: Headings and body text
- **TextField**: Form input with data binding
- **Button**: Interactive buttons with action handlers

## Technology Stack

- React 18
- TypeScript
- Vite (dev server & build)
- Tailwind CSS
- shadcn/ui components
- @a2a-js/sdk (A2A protocol)

## Development

```bash
# Run development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## License

MIT
