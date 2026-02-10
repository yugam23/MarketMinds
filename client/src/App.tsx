import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import { AnimatePresence } from "framer-motion";
import { PageTransition } from "./components/layout/PageTransition";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Loader2 } from "lucide-react";
import "./App.css";

// Lazy load pages
const Dashboard = lazy(() => import("./pages/Dashboard").then(module => ({ default: module.Dashboard })));

const LoadingFallback = () => (
  <div className="min-h-screen flex items-center justify-center bg-slate-900 text-slate-400">
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="animate-spin text-[#135bec]" size={40} />
      <span className="text-sm font-medium animate-pulse">Loading MarketMinds...</span>
    </div>
  </div>
);

function AppContent() {
  const location = useLocation();

  return (
    <>
      <Toaster position="top-right" richColors theme="dark" />
      <AnimatePresence mode="wait">
        <Suspense fallback={<LoadingFallback />}>
          <Routes location={location} key={location.pathname}>
            <Route
              path="/"
              element={
                <PageTransition>
                  <Dashboard />
                </PageTransition>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </AnimatePresence>
    </>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
