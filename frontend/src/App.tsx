import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ROUTES } from "./routes";
import Protected from "./components/Protected";
import Home from "./pages/Home";
import Ping from "./pages/Ping";
import Login from "./pages/Login";
import Vedett from "./pages/Vedett_oldal";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path={ROUTES.home} element={<Home />} />
        <Route path={ROUTES.ping} element={<Ping />} />
        <Route path={ROUTES.login} element={<Login />} />
        <Route path={ROUTES.vedett} element={
          <Protected>
            <Vedett />
          </Protected>
        } />
      </Routes>
    </BrowserRouter>
  );
}
export default App
