import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import './index.css'
import App from './App.tsx'

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
if (!publishableKey) {
  console.warn(
    '[Clerk] VITE_CLERK_PUBLISHABLE_KEY is not set. Auth will not work until you add it from the Clerk dashboard.'
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ClerkProvider publishableKey={publishableKey || ''}>
      <App />
    </ClerkProvider>
  </StrictMode>,
)
