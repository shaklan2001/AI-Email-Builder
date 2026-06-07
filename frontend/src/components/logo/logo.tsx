import { forwardRef, useId } from 'react';
// @mui
import Link from '@mui/material/Link';
import Box, { BoxProps } from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
// routes
import { RouterLink } from 'src/routes/components';

// ----------------------------------------------------------------------

export interface LogoProps extends BoxProps {
  disabledLink?: boolean;
}

const Logo = forwardRef<HTMLDivElement, LogoProps>(
  ({ disabledLink = false, sx, ...other }, ref) => {
    const theme = useTheme();
    const gradientId = useId();
    const { primary, grey } = theme.palette;

    const logo = (
      <Box
        ref={ref}
        sx={{
          width: 64,
          height: 64,
          flexShrink: 0,
          cursor: 'pointer',
          ...sx,
        }}
        {...other}
      >
        <svg viewBox="0 0 64 64" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={primary.lighter} />
              <stop offset="100%" stopColor={primary.light} />
            </linearGradient>
          </defs>

          <circle cx="44" cy="20" r="16" fill={primary.main} />

          <rect x="4" y="16" width="44" height="44" rx="12" fill={`url(#${gradientId})`} />

          <text
            x="26"
            y="46"
            textAnchor="middle"
            fontFamily="Public Sans, sans-serif"
            fontSize="18"
            fontWeight="700"
            fill={grey[800]}
          >
            AI
          </text>
        </svg>
      </Box>
    );

    if (disabledLink) {
      return logo;
    }

    return (
      <Link component={RouterLink} href="/dashboard" sx={{ display: 'contents' }}>
        {logo}
      </Link>
    );
  }
);

export default Logo;
