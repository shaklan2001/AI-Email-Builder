import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import {
  conversationMessageLabels,
  type ConversationThreadMessage,
} from "../../types/conversation-thread";

interface ConversationThreadProps {
  messages: ConversationThreadMessage[];
}

function ThreadMessage({ message }: { message: ConversationThreadMessage }) {
  const isProspect = message.type === "prospect_reply";

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isProspect ? "flex-end" : "flex-start",
      }}
    >
      <Paper
        variant="outlined"
        elevation={0}
        sx={{
          maxWidth: "100%",
          px: 1.5,
          py: 1,
          borderRadius: 1.5,
          bgcolor: isProspect ? "action.hover" : "background.paper",
          textAlign: "left",
        }}
      >
        <Typography
          variant="caption"
          color="text.secondary"
          fontWeight={600}
          display="block"
          sx={{ mb: 0.5 }}
        >
          {conversationMessageLabels[message.type]}
        </Typography>
        <Typography variant="caption" component="p" sx={{ m: 0, whiteSpace: "pre-wrap" }}>
          {message.content}
        </Typography>
      </Paper>
    </Box>
  );
}

export function ConversationThread({ messages }: ConversationThreadProps) {
  return (
    <Box sx={{ width: "100%", textAlign: "left" }}>
      <Typography variant="caption" color="text.secondary" fontWeight={600} display="block" sx={{ mb: 1 }}>
        Thread View
      </Typography>
      <Stack spacing={1}>
        {messages.map((message) => (
          <ThreadMessage key={message.id} message={message} />
        ))}
      </Stack>
    </Box>
  );
}
