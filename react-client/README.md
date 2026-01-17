# Vehicle Trade-In React Client

A React + TypeScript + shadcn/ui frontend for the Vehicle Trade-In Multi-Agent System.

## Overview

This client provides a modern, interactive UI for the vehicle trade-in workflow, connecting to the Orchestrator A2A server and rendering A2UI components.

## Features

- **A2UI Rendering**: Converts A2UI JSON to React/shadcn components (12 component types)
- **A2A Integration**: Uses `@a2a-js/sdk` for server communication
- **Schema Validation**: Validates A2UI JSON before rendering
- **Error Handling**: Error boundary with retry option
- **Input Sanitization**: XSS prevention (strips HTML, blocks dangerous URLs)
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

Open http://localhost:5173

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
│   │   │   └── A2UIRenderer.tsx   # A2UI JSON renderer (900+ lines)
│   │   ├── ui/                     # shadcn/ui components
│   │   └── ChatInterface.tsx       # Main chat UI
│   ├── index.css                   # Tailwind v4 theme config
│   ├── App.tsx                     # App entry point
│   └── main.tsx                    # React entry point
├── package.json
└── vite.config.ts
```

## A2UI Components Supported (12)

| Component | Description |
|-----------|-------------|
| Card | Styled content container |
| Button | Primary/outline/secondary/ghost/destructive variants |
| TextField | Form input with data binding |
| Text | Headings (h1-h5), body, caption |
| Row | Horizontal flex container |
| Column | Vertical flex container |
| List | Horizontal/vertical list |
| Divider | Visual separator |
| Icon | Emoji-based icons |
| Image | URL-bound images |
| CheckBox | Data-bound checkbox |
| DateTimeInput | Date/time picker |

## Technology Stack

- React 18
- TypeScript
- Vite (dev server & build)
- **Tailwind CSS v4** with `@theme` configuration
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
