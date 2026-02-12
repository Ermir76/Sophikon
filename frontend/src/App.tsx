import { Route, Routes } from "react-router";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { GuestRoute } from "./components/GuestRoute";

import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";

// Pages (We will build these next)
function HomePage() {
  return <h1>Home Page (Protected)</h1>;
}

function App() {
  return (
    <Routes>
      {/* 
        GUEST ROUTES 
        Only accessible if you are NOT logged in.
        If you are logged in, these redirect to "/" 
      */}
      <Route element={<GuestRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* 
        PROTECTED ROUTES 
        Only accessible if you ARE logged in.
        If you are not logged in, these redirect to "/login" 
      */}
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<HomePage />} />
      </Route>
    </Routes>
  );
}

export default App;
