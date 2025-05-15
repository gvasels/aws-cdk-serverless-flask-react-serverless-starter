import reactLogo from './assets/react.svg'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'
import { configureAmplify } from './amplify-ui-config';
import viteLogo from '/vite.svg'
import './App.css'
import { withAuthenticator, WithAuthenticatorProps } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

// Set up a Router instance
const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
  scrollRestoration: true,
});

// Register things for typesafety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

configureAmplify();

export function App({ signOut, user }: WithAuthenticatorProps) {


  return (
    <>
        <div>
          <a href="https://vite.dev" target="_blank">
            <img src={viteLogo} className="logo" alt="Vite logo" />
          </a>
          <a href="https://react.dev" target="_blank">
            <img src={reactLogo} className="logo react" alt="React logo" />
          </a>
        </div>
        <h1>Vite + React + TanStack Router</h1>
        <h1>Hello {user?.username}</h1>
        <button onClick={signOut}>Sign out</button>
        <RouterProvider router={router} />
    </>
  );
};

// Give the wrapped component a display name for React Fast Refresh
const AppWithAuth = withAuthenticator(App);
export default AppWithAuth;
