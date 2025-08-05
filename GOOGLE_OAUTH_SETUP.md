
# Google OAuth Setup Instructions

To enable Google OAuth authentication for patient registration and login, follow these steps:

## 1. Create Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API and Google OAuth2 API
4. Go to "Credentials" in the left sidebar
5. Click "Create Credentials" > "OAuth 2.0 Client IDs"
6. Configure the OAuth consent screen:
   - Application name: "Dr. Richa's Eye Clinic"
   - User support email: your email
   - Application homepage: your Replit app URL
   - Authorized domains: add your Replit domain
7. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Name: "Dr. Richa's Eye Clinic Web Client"
   - Authorized JavaScript origins: `https://your-repl-name.replit.app`
   - Authorized redirect URIs: `https://your-repl-name.replit.app/patient/google-callback`

## 2. Configure Environment Variables

In your Replit project:

1. Go to the "Secrets" tab (lock icon in sidebar)
2. Add these environment variables:
   - `GOOGLE_CLIENT_ID`: Your Google OAuth Client ID
   - `GOOGLE_CLIENT_SECRET`: Your Google OAuth Client Secret

## 3. Update Code

Replace the placeholder values in `routes.py`:
- Replace `"your-google-client-id"` with `app.config['GOOGLE_CLIENT_ID']`
- Replace `"your-google-client-secret"` with `app.config['GOOGLE_CLIENT_SECRET']`

## 4. Test the Integration

1. Visit `/patient/register`
2. Click "Register with Google Account"
3. You should be redirected to Google's OAuth consent screen
4. After granting permissions, you'll be redirected back to the patient dashboard

## Notes

- For development, you can test with localhost URLs
- For production, make sure to use HTTPS URLs
- The OAuth consent screen may show a warning for unverified apps during development
