import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ROUTES } from "./routes";
import Protected from "./components/Protected";
import Home from "./pages/Home";
import Ping from "./pages/Ping";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import Books from "./pages/Books";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path={ROUTES.home} element={<Home />} />
        <Route path={ROUTES.ping} element={<Ping />} />
        <Route path={ROUTES.login} element={<Login />} />
        <Route path={ROUTES.profile} element={
          <Protected>
            <Profile />            
          </Protected>
        } />
        <Route path={ROUTES.books} element={
          <Protected>
            <Books />            
          </Protected>
        } />
      </Routes>
    </BrowserRouter>
  );
}
export default App
