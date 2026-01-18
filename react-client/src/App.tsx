import { useState, useRef, useEffect } from 'react'
import { A2AClient, type A2AMessage } from './lib/a2a-client'
import { A2UIRenderer, processDataModelUpdates } from './components/a2ui/A2UIRenderer'
import { Button } from './components/ui/button'
import { Input } from './components/ui/input'
import { Card, CardContent } from './components/ui/card'
import AnamAvatar from './components/anam/AnamAvatar'
import type { AnamAvatarHandle } from './components/anam/AnamAvatar'
import { MessageSquare, Video } from 'lucide-react'

function App() {
  const [messages, setMessages] = useState<A2AMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [dataModel, setDataModel] = useState<Record<string, any>>({})
  const [uiMode, setUiMode] = useState<'form' | 'avatar'>('form')
  const clientRef = useRef<A2AClient>(new A2AClient('http://localhost:10010'))
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const avatarRef = useRef<AnamAvatarHandle>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: A2AMessage = {
      role: 'user',
      content: input,
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await clientRef.current.sendMessage(input)
      setMessages(prev => [...prev, response])

      // Process dataModelUpdate messages to initialize form values
      if (response.a2uiJson) {
        setDataModel(prev => processDataModelUpdates(response.a2uiJson!, prev))
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      setMessages(prev => [...prev, {
        role: 'agent',
        content: 'Sorry, I encountered an error. Please make sure the orchestrator server is running at http://localhost:10010',
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleAction = async (actionName: string, context: Record<string, any>) => {
    setIsLoading(true)

    try {
      const response = await clientRef.current.sendAction({ name: actionName, context })
      setMessages(prev => [...prev, response])

      // Process dataModelUpdate messages
      if (response.a2uiJson) {
        setDataModel(prev => processDataModelUpdates(response.a2uiJson!, prev))
      }
    } catch (error) {
      console.error('Failed to send action:', error)
      setMessages(prev => [...prev, {
        role: 'agent',
        content: 'Sorry, I encountered an error processing your action.',
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleDataChange = (path: string, value: any) => {
    setDataModel(prev => {
      const newModel = { ...prev }
      const parts = path.split('/').filter(p => p)

      let current: any = newModel
      for (let i = 0; i < parts.length - 1; i++) {
        if (!current[parts[i]]) {
          current[parts[i]] = {}
        }
        current = current[parts[i]]
      }

      current[parts[parts.length - 1]] = value
      return newModel
    })
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="border-b p-4 flex justify-between items-center bg-card">
        <div>
          <h1 className="text-2xl font-bold">Vehicle Trade-In Assistant</h1>
          <p className="text-sm text-muted-foreground">Powered by React + shadcn/ui</p>
        </div>
        <div className="flex bg-muted p-1 rounded-lg">
          <Button
            variant={uiMode === 'form' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setUiMode('form')}
            className="gap-2"
          >
            <MessageSquare className="h-4 w-4" />
            Form
          </Button>
          <Button
            variant={uiMode === 'avatar' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setUiMode('avatar')}
            className="gap-2"
          >
            <Video className="h-4 w-4" />
            Avatar
          </Button>
        </div>
      </div>

      {/* Avatar Display Section */}
      {uiMode === 'avatar' && (
        <div className="p-4 bg-muted/30 border-b flex justify-center">
          <div className="w-full max-w-3xl">
            <AnamAvatar
              ref={avatarRef}
              onMessageReceived={(role, content) => {
                setMessages(prev => [...prev, { role, content }]);
              }}
            />
          </div>
        </div>
      )}

      {/* Messages */}
      <div className={`flex-1 overflow-y-auto p-4 space-y-4 ${uiMode === 'avatar' ? 'max-h-[30vh]' : ''}`}>
        {messages.length === 0 && (
          <Card>
            <CardContent className="pt-6">
              <p className="text-center text-muted-foreground">
                Welcome! Tell me about your vehicle trade-in.
              </p>
            </CardContent>
          </Card>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`
              ${message.role === 'user' ? 'max-w-[80%] bg-primary text-primary-foreground' : 'max-w-[70%] bg-muted'} 
              rounded-lg p-4
            `}>
              {message.role === 'user' ? (
                <p>{message.content}</p>
              ) : (
                <div className="flex flex-col gap-4">
                  <p>{clientRef.current.getTextContent(message.content)}</p>
                  {message.a2uiJson && (
                    <div className="w-full">
                      <A2UIRenderer
                        a2uiJson={message.a2uiJson}
                        onAction={handleAction}
                        dataModel={dataModel}
                        onDataChange={handleDataChange}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg p-4">
              <p className="text-muted-foreground">Thinking...</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <Button onClick={handleSend} disabled={isLoading || !input.trim()}>
            Send
          </Button>
        </div>
      </div>
    </div>
  )
}

export default App
