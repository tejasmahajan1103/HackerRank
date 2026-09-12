import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { Chat } from './pages/Chat';
import { Analyze } from './pages/Analyze';
import { Forecast } from './pages/Forecast';
import { Transactions } from './pages/Transactions';
import { Plans } from './pages/Plans';
import { Profile } from './pages/Profile';
import { Layout } from './components/Layout';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/forecast" element={<Forecast />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/plans" element={<Plans />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;