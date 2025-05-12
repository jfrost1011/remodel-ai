"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { Auth0Provider, useAuth0 } from "@auth0/auth0-react"

// Auth context to share authentication state
type AuthContextType = {
  isAuthenticated: boolean
  isLoading: boolean
  user: any
  login: () => void
  logout: () => void
  getAccessToken: () => Promise<string | null>
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  user: null,
  login: () => {},
  logout: () => {},
  getAccessToken: async () => null,
})

export const useAuth = () => useContext(AuthContext)

// Auth provider wrapper
export function AuthProviderWrapper({ children }: { children: ReactNode }) {
  // In a real app, these would come from environment variables
  const domain = "dev-example.us.auth0.com"
  const clientId = "your-auth0-client-id"
  const audience = "https://api.remodelaiesimator.com"

  return (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: typeof window !== "undefined" ? window.location.origin : "",
        audience: audience,
        scope: "read:estimates write:estimates",
      }}
    >
      <AuthProvider>{children}</AuthProvider>
    </Auth0Provider>
  )
}

// Internal provider that uses Auth0 hooks
function AuthProvider({ children }: { children: ReactNode }) {
  const {
    isAuthenticated,
    isLoading,
    user,
    loginWithRedirect,
    logout: auth0Logout,
    getAccessTokenSilently,
  } = useAuth0()
  const [accessToken, setAccessToken] = useState<string | null>(null)

  // Get access token when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      getAccessTokenSilently()
        .then((token) => {
          setAccessToken(token)
        })
        .catch((err) => {
          console.error("Error getting access token:", err)
        })
    }
  }, [isAuthenticated, getAccessTokenSilently])

  const login = () => {
    loginWithRedirect()
  }

  const logoutUser = () => {
    auth0Logout({
      logoutParams: {
        returnTo: typeof window !== "undefined" ? window.location.origin : "",
      },
    })
  }

  const getAccessToken = async (): Promise<string | null> => {
    if (!isAuthenticated) return null

    try {
      const token = await getAccessTokenSilently()
      setAccessToken(token)
      return token
    } catch (error) {
      console.error("Error getting access token:", error)
      return null
    }
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        login,
        logout: logoutUser,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
