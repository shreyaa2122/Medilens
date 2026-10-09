import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { Upload } from "./pages/Upload";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="upload" element={<Upload />} />
        <Route
          path="documents/:documentId/processing"
          element={
            <PlaceholderPage
              title="Processing document"
              description="Live status while the document is read, structured and validated."
            />
          }
        />
        <Route
          path="documents/:documentId"
          element={
            <PlaceholderPage
              title="Document results"
              description="Extracted lab values, reference-range status, confidence and source evidence."
            />
          }
        />
        <Route
          path="documents/:documentId/labs/:resultId"
          element={
            <PlaceholderPage
              title="Lab result details"
              description="One test in detail, with a plain-language explanation and the source text."
            />
          }
        />
        <Route
          path="documents/:documentId/prescriptions"
          element={
            <PlaceholderPage
              title="Prescription details"
              description="Extracted medication details with confidence and verification prompts."
            />
          }
        />
        <Route
          path="trends"
          element={
            <PlaceholderPage
              title="Trends"
              description="Track the same lab test across multiple reports."
            />
          }
        />
        <Route
          path="privacy"
          element={
            <PlaceholderPage
              title="Privacy & data"
              description="See how many documents are stored and delete one or all of them."
            />
          }
        />
      </Route>
    </Routes>
  );
}
