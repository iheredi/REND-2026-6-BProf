import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import { AuthProvider } from "./context/AuthContext.tsx";

import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";
import './index.css';


createRoot(document.getElementById('root')!).render(
  <AuthProvider>
    <App />
  </AuthProvider>,
)
