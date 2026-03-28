import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "./lib/auth";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import Login from "./pages/Login";
import Docs from "./pages/Docs";
import Dashboard from "./pages/Dashboard";
import Tickets from "./pages/Tickets";
import Moderation from "./pages/Moderation";
import Staff from "./pages/Staff";
import Config from "./pages/Config";
import NotFound from "@/pages/not-found";
import { Redirect } from "wouter";

const queryClient = new QueryClient();

function Router() {
  return (
    <Switch>
      <Route path="/" component={() => <Redirect to="/docs" />} />
      <Route path="/docs" component={Docs} />
      <Route path="/login" component={Login} />
      <Route path="/dashboard">
        <ProtectedRoute>
          <Layout>
            <Dashboard />
          </Layout>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/tickets">
        <ProtectedRoute>
          <Layout>
            <Tickets />
          </Layout>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/moderation">
        <ProtectedRoute>
          <Layout>
            <Moderation />
          </Layout>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/staff">
        <ProtectedRoute>
          <Layout>
            <Staff />
          </Layout>
        </ProtectedRoute>
      </Route>
      <Route path="/dashboard/config">
        <ProtectedRoute>
          <Layout>
            <Config />
          </Layout>
        </ProtectedRoute>
      </Route>
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
            <Router />
          </WouterRouter>
          <Toaster />
        </AuthProvider>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
