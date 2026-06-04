import Box from "@mui/material/Box";
import { useEffect, useRef } from "react";
import { AssistantMessage } from "./assistant-message";
import type { ChatMessage } from "./types";
import { UserMessage } from "./user-message";

interface MessageListProps {
  messages: ChatMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <Box
      sx={{
        flex: 1,
        minHeight: 0,
        overflowY: "auto",
        py: 1,
      }}
    >
      {messages.map((message) =>
        message.role === "user" ? (
          <UserMessage key={message.id} content={message.content} />
        ) : (
          <AssistantMessage
            key={message.id}
            content={message.content}
            isLoading={message.isLoading}
          />
        ),
      )}
      <div ref={bottomRef} />
    </Box>
  );
}
