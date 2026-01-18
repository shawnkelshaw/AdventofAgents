import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import { createClient, AnamEvent, type AnamClient } from '@anam-ai/js-sdk';

interface AnamAvatarProps {
    onStatusChange?: (status: string) => void;
    onMessageReceived?: (role: 'user' | 'agent', text: string) => void;
    onError?: (error: Error) => void;
}

export interface AnamAvatarHandle {
    stop: () => void;
}

const AnamAvatar = forwardRef<AnamAvatarHandle, AnamAvatarProps>(({ onStatusChange, onMessageReceived, onError }, ref) => {
    const clientRef = useRef<AnamClient | null>(null);
    const [isInitializing, setIsInitializing] = useState(false);
    const videoId = "anam-video-element";

    useImperativeHandle(ref, () => ({
        stop: () => {
            if (clientRef.current) {
                clientRef.current.interruptPersona();
            }
        }
    }));

    useEffect(() => {
        let active = true;

        const initAnam = async () => {
            if (isInitializing) return;
            setIsInitializing(true);

            try {
                // Fetch session token from backend
                const response = await fetch('http://localhost:10010/anam/session');
                if (!response.ok) throw new Error('Failed to fetch Anam session token');
                const { sessionToken } = await response.json();

                if (!active) return;

                // Initialize SDK using the helper
                const client = createClient(sessionToken);

                // Event: Connection State
                client.addListener(AnamEvent.SESSION_READY, (sessionId) => {
                    onStatusChange?.('READY');
                    console.info('[Anam] Session ready:', sessionId);
                });

                client.addListener(AnamEvent.CONNECTION_CLOSED, () => {
                    onStatusChange?.('CLOSED');
                });

                // Event: Message History Synchronization
                client.addListener(AnamEvent.MESSAGE_HISTORY_UPDATED, (messages) => {
                    if (messages.length > 0) {
                        const lastMessage = messages[messages.length - 1];
                        // Only notify for the most recent message to avoid duplicates in the UI
                        onMessageReceived?.(
                            lastMessage.role === 'user' ? 'user' : 'agent',
                            lastMessage.content
                        );
                    }
                });

                // Start streaming (this also requests microphone access)
                await client.streamToVideoElement(videoId);

                if (active) {
                    clientRef.current = client;
                } else {
                    client.stopStreaming();
                }
            } catch (err) {
                console.error('Anam initialization error:', err);
                onError?.(err instanceof Error ? err : new Error(String(err)));
            } finally {
                if (active) {
                    setIsInitializing(false);
                }
            }
        };

        initAnam();

        return () => {
            active = false;
            if (clientRef.current) {
                clientRef.current.stopStreaming();
            }
        };
    }, []);

    return (
        <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden shadow-2xl">
            <video
                id={videoId}
                autoPlay
                playsInline
                className="w-full h-full object-cover"
            />
            {isInitializing && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 text-white z-10">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mr-3" />
                    Initializing Avatar...
                </div>
            )}
            <div className="absolute bottom-4 left-4 right-4 flex justify-between items-center pointer-events-none">
                <div className="bg-black/60 px-3 py-1 rounded-full text-white text-xs backdrop-blur-sm">
                    Microphone Active
                </div>
            </div>
        </div>
    );
});

AnamAvatar.displayName = 'AnamAvatar';

export default AnamAvatar;
