import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import FileUpload from './pages/customer/FileUpload';
import UploadHistory from './pages/customer/UploadHistory';
import UploadDetail from './pages/customer/UploadDetail';
import Chat from './pages/customer/Chat';
import PendingReviews from './pages/review/PendingReviews';
import ReviewDetail from './pages/review/ReviewDetail';
import CDMExplorer from './pages/review/CDMExplorer';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          {/* Customer Portal */}
          <Route path="/" element={<FileUpload />} />
          <Route path="/history" element={<UploadHistory />} />
          <Route path="/uploads/:id" element={<UploadDetail />} />
          <Route path="/chat" element={<Chat />} />

          {/* Analyst Review Portal */}
          <Route path="/review" element={<PendingReviews />} />
          <Route path="/review/:mappingId" element={<ReviewDetail />} />
          <Route path="/review/cdm" element={<CDMExplorer />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
