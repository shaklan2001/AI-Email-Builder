The AI currently gets stuck asking for missing fields repeatedly.

This creates a poor user experience.

## Required Behavior

Users must be allowed to skip questions.

Examples:

- skip
- none
- nothing
- don't know
- not sure
- no preference
- doesn't matter

When detected:

Do not ask the same question again.

Mark the field as skipped.

## Optional Fields

These fields are optional:

- Business Goal
- Tone
- Audience
- CTA
- Landing Page
- Images
- Attachments
- Competitors

If skipped:

Use intelligent defaults.

Examples:

Business Goal:
→ Product Promotion

Tone:
→ Professional

Audience:
→ General Customers

CTA:
→ Learn More

## Required Fields

Only these fields are required:

- Product / Service

If product is known:

The AI should always be able to continue.

## Fallback Behavior

If user provides very little information:

User:
"Chocolate business"

AI:

✓ Product: Chocolate

Assumptions:
- Goal: Product Promotion
- Tone: Professional
- CTA: Learn More

Would you like me to customize any of these before generating the campaign?

## Check When Done

- Users can skip questions
- AI does not repeat the same question endlessly
- Intelligent defaults are applied
- Campaign generation can proceed with minimal information