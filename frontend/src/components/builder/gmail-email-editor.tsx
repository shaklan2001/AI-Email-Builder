import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import InputBase from "@mui/material/InputBase";
import Typography from "@mui/material/Typography";

const GMAIL_COLORS = {
  text: "#202124",
  secondary: "#5f6368",
  border: "#e8eaed",
};

const GMAIL_FONT = '"Roboto", "Helvetica", "Arial", sans-serif';

interface GmailEmailEditorProps {
  subject: string;
  body: string;
  onSubjectChange?: (value: string) => void;
  onBodyChange?: (value: string) => void;
  readOnly?: boolean;
  senderName?: string;
  senderEmail?: string;
}

function getSenderInitial(senderName: string, senderEmail: string): string {
  const source = senderName.trim() || senderEmail.trim();
  return source.charAt(0).toUpperCase() || "C";
}

export function GmailEmailEditor({
  subject,
  body,
  onSubjectChange,
  onBodyChange,
  readOnly = false,
  senderName = "Campaign",
  senderEmail = "onboarding@resend.dev",
}: GmailEmailEditorProps) {
  const displaySender = senderEmail.includes("@")
    ? senderEmail
    : `${senderName} <${senderEmail}>`;

  return (
    <Box
      sx={{
        bgcolor: "#fff",
        border: `1px solid ${GMAIL_COLORS.border}`,
        borderRadius: "12px",
        overflow: "hidden",
        fontFamily: GMAIL_FONT,
      }}
    >
      <Box sx={{ px: 2.5, pt: 2.25, pb: 1.25 }}>
        {readOnly ? (
          <Typography
            sx={{
              fontSize: "1.125rem",
              fontWeight: 500,
              lineHeight: 1.35,
              color: GMAIL_COLORS.text,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {subject || "No subject"}
          </Typography>
        ) : (
          <InputBase
            value={subject}
            onChange={(e) => onSubjectChange?.(e.target.value)}
            placeholder="Subject"
            fullWidth
            multiline
            sx={{
              fontSize: "1.125rem",
              fontWeight: 500,
              lineHeight: 1.35,
              color: GMAIL_COLORS.text,
              "& .MuiInputBase-input": {
                p: 0,
                "&::placeholder": {
                  color: GMAIL_COLORS.secondary,
                  opacity: 1,
                },
              },
            }}
          />
        )}
      </Box>

      <Box
        sx={{
          display: "flex",
          alignItems: "flex-start",
          gap: 1.5,
          px: 2.5,
          pb: 2,
        }}
      >
        <Avatar
          sx={{
            width: 40,
            height: 40,
            bgcolor: "#1a73e8",
            fontSize: "1rem",
            fontWeight: 500,
          }}
        >
          {getSenderInitial(senderName, senderEmail)}
        </Avatar>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "baseline",
              justifyContent: "space-between",
              gap: 2,
            }}
          >
            <Box sx={{ minWidth: 0 }}>
              <Typography
                component="div"
                sx={{
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: GMAIL_COLORS.text,
                  lineHeight: 1.4,
                }}
              >
                {displaySender}
              </Typography>
              <Typography
                component="div"
                sx={{
                  fontSize: "0.75rem",
                  color: GMAIL_COLORS.secondary,
                  lineHeight: 1.4,
                }}
              >
                to me
              </Typography>
            </Box>
            <Typography
              sx={{
                fontSize: "0.75rem",
                color: GMAIL_COLORS.secondary,
                whiteSpace: "nowrap",
                flexShrink: 0,
              }}
            >
              now
            </Typography>
          </Box>
        </Box>
      </Box>

      <Box sx={{ borderTop: `1px solid ${GMAIL_COLORS.border}` }} />

      <Box sx={{ px: 2.5, py: 2.25 }}>
        {readOnly ? (
          <Typography
            sx={{
              fontSize: "0.875rem",
              lineHeight: 1.7,
              color: GMAIL_COLORS.text,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {body || "No message"}
          </Typography>
        ) : (
          <InputBase
            value={body}
            onChange={(e) => onBodyChange?.(e.target.value)}
            placeholder="Write your email message…"
            fullWidth
            multiline
            minRows={10}
            sx={{
              width: "100%",
              fontSize: "0.875rem",
              lineHeight: 1.7,
              color: GMAIL_COLORS.text,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              "& .MuiInputBase-input": {
                p: 0,
                "&::placeholder": {
                  color: GMAIL_COLORS.secondary,
                  opacity: 1,
                },
              },
            }}
          />
        )}
      </Box>
    </Box>
  );
}
