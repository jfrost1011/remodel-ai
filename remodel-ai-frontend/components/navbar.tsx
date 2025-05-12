"use client"

import { useState } from "react"
import Link from "next/link"
import { Home, Menu, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { AuthButton } from "@/components/auth-button"

interface NavbarProps {
  onAboutClick: () => void
  onNewEstimate?: () => void
}

export function Navbar({ onAboutClick, onNewEstimate }: NavbarProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-xl font-semibold">
          <Home className="h-5 w-5 text-emerald-500" />
          <span>RemodelAI Estimator</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-6">
          {onNewEstimate && (
            <Button variant="outline" onClick={onNewEstimate} className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              New Estimate
            </Button>
          )}
          <Button variant="ghost" onClick={onAboutClick}>
            About
          </Button>
          <AuthButton />
        </nav>

        {/* Mobile Navigation */}
        <Sheet open={isMenuOpen} onOpenChange={setIsMenuOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon">
              <Menu className="h-6 w-6" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right">
            <div className="flex flex-col gap-4 mt-8">
              <AuthButton />
              {onNewEstimate && (
                <Button
                  variant="outline"
                  onClick={() => {
                    onNewEstimate()
                    setIsMenuOpen(false)
                  }}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  New Estimate
                </Button>
              )}
              <Button
                variant="ghost"
                onClick={() => {
                  onAboutClick()
                  setIsMenuOpen(false)
                }}
              >
                About
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </header>
  )
}
