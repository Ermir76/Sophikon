# Sophikon Landing Page

Static HTML landing page — deployed independently to S3 + CloudFront.

## Structure

```
landing/
  index.html     ← the landing page
  assets/
    favicon.ico  ← TODO: add favicon
    og-image.png ← TODO: add OG image (1200x630px)
```

## Deploy

```bash
aws s3 sync . s3://sophikon-landing --exclude "README.md"
```

## Assets needed before go-live

- `assets/favicon.ico` — browser tab icon
- `assets/og-image.png` — 1200×630px image shown when sharing the link on social media / Slack / iMessage
