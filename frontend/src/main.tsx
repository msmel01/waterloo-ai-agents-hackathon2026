import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import { Toaster } from 'sonner'
import './index.css'
import App from './App.tsx'

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
if (!publishableKey) {
  throw new Error('Missing VITE_CLERK_PUBLISHABLE_KEY. Add it to .env (copy from CLERK_PUBLISHABLE_KEY).')
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ClerkProvider publishableKey={publishableKey}>
      <App />
      <Toaster position="top-center" richColors />
    </ClerkProvider>
  </StrictMode>,
)
