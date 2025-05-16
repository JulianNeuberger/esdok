import React from 'react';
import {BrowserRouter, Route, Routes} from "react-router-dom";

import './App.css';
import MetaModel from "./components/MetaModel/MetaModel";
import KnowledgeGraphView from "./views/KnowledgeGraphView";

function App() {
  return (
      <BrowserRouter basename={process.env.PUBLIC_URL}>
          <Routes>
              <Route path={"/"} element={<KnowledgeGraphView />} />
              <Route path={"/model"} element={<MetaModel />} />
          </Routes>
      </BrowserRouter>
  );
}

export default App;
