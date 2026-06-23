import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard";

export default function App() {
  const [dark, setDark] = useState(() => localStorage.getItem("theme") !== "light");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  return <Dashboard dark={dark} setDark={setDark} />;
}
