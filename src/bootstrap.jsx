import React from "react";
import ReactDOM from "react-dom/client";
import "./globals.css";
import App from "./App";
import { BrowserRouter, Route, Routes } from "react-router-dom";

const rootElement = document.getElementById("root");
const root = ReactDOM.createRoot(rootElement);

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="*" element={<App />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
