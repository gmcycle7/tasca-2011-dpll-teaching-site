import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

// BASE_URL is "/" in dev and "/<repo-name>/" when built with VITE_BASE set
// (see web/vite.config.ts). Stripping the trailing slash gives the form
// BrowserRouter expects, including the empty-string default.
const basename = import.meta.env.BASE_URL.replace(/\/$/, "");

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter basename={basename}>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
