import React from 'react';
import {BrowserRouter, Route, Routes} from "react-router-dom";
import {Empty} from "antd";

import './App.css';

import InteractiveKnowledgeGraph from "./components/InteractiveKnowledgeGraph/InteractiveKnowledgeGraph";
import MetaModel from "./components/MetaModel/MetaModel";

function App() {
  return (
      <BrowserRouter>
          <Routes>
              <Route path={"/"} element={<InteractiveKnowledgeGraph />} />
              <Route path={"/model"} element={<MetaModel />} />
          </Routes>
      </BrowserRouter>
  );
}

export default App;
