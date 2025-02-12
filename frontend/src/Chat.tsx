import React, { useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import "./index.css";
interface Message {
    message: string;
    isUser: boolean;
    sources?: string[];
}

const API_BASE_URL = "http://localhost:8080";

interface ChatProps {
    selectedCollection: string;
}

const Chat: React.FC<ChatProps> = ({ selectedCollection }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState("");

    const formatSource = (source: string) => source.split("/").pop() || "";

    const setPartialMessage = useCallback(
        (chunk: string, sources: string[] = []) => {
            setMessages((prevMessages) => {
                if (prevMessages.length === 0) {
                    return [{ message: chunk, isUser: false, sources }];
                }

                const lastMessage = prevMessages[prevMessages.length - 1];

                if (!lastMessage.isUser) {
                    return [
                        ...prevMessages.slice(0, -1),
                        {
                            ...lastMessage,
                            message: lastMessage.message + chunk,
                            sources: lastMessage.sources
                                ? [...lastMessage.sources, ...sources]
                                : sources,
                        },
                    ];
                }

                return [...prevMessages, { message: chunk, isUser: false, sources }];
            });
        },
        []
    );

    const handleReceiveMessage = useCallback((data: string) => {
        try {
            const parsedData = JSON.parse(data);
            if (parsedData.answer) {
                setPartialMessage(parsedData.answer.content);
            }
            if (parsedData.docs) {
                setPartialMessage(
                    "",
                    parsedData.docs.map((doc: any) => doc.metadata.source)
                );
            }
        } catch (error) {
            console.error("Error parsing response:", error);
        }
    }, []);

    const handleSendMessage = async (message: string) => {
        if (!message.trim()) return;
        console.log("sending message with collection name: ", selectedCollection)
        setInputValue("");
        setMessages((prevMessages) => [
            ...prevMessages,
            { message, isUser: true },
        ]);

        try {
            await fetchEventSource(`${API_BASE_URL}/rag/stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ input: { question: message, collection_name: selectedCollection } }),
                onmessage(event) {
                    if (event.event === "data") {
                        handleReceiveMessage(event.data);
                    }
                },
            });
        } catch (error) {
            console.error("Error sending message:", error);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(inputValue.trim());
        }
    };

    return (
        <div className="flex-grow bg-gray-700 shadow overflow-hidden sm:rounded-lg">
            <div className="border-b border-gray-600 p-4">
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={`p-3 my-3 rounded-lg text-white ml-auto ${msg.isUser ? "bg-gray-800" : "bg-gray-900"}`}
                    >
                        <ReactMarkdown components={{ p: ({ node, ...props }) => <p style={{ whiteSpace: "pre-wrap" }} {...props} /> }}>
                            {msg.message}
                        </ReactMarkdown>

                        {!msg.isUser && msg.sources && msg.sources.length > 0 && (
                            <div className="text-xs mt-3">
                                <hr className="border-b mt-5 mb-5" />
                                {msg.sources.map((source, idx) => (
                                    <div key={idx}>
                                        <a
                                            target="_blank"
                                            download
                                            href={`${API_BASE_URL}/rag/static/${encodeURIComponent(formatSource(source))}`}
                                            rel="noreferrer"
                                            className="text-blue-400 hover:underline"
                                        >
                                            {formatSource(source)}
                                        </a>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <div className="p-4 bg-gray-800">
                <textarea
                    className="form-textarea w-full p-2 border rounded text-white bg-gray-900 border-gray-600 resize-none h-auto"
                    placeholder="Enter your message here..."
                    onKeyDown={handleKeyPress}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                />
                <button
                    className="mt-2 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
                    onClick={() => handleSendMessage(inputValue)}
                >
                    Send
                </button>
            </div>
        </div>
    );
};

export default Chat;
