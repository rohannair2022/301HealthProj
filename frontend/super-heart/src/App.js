import logo from './logo.png';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Login from './components/Login.js';
import Landing from './components/Landing';
import Test from './components/Test';
import PatientDashboard from './components/PatientDashboard';
import DoctorDashboard from './components/DoctorDashboard';
import Register from './components/Register';
import PatientProfilePage from './components/PatientProfilePage.jsx';
import DoctorProfilePage from './components/DoctorProfilePage.jsx';
import ForgotPassword from "./components/ForgotPassword";

function App() {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<Landing />} />
        <Route path='/login' element={<Login />} />
        <Route path='/register' element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path='/test' element={<Test />} />
        <Route path='/patient-dashboard' element={<PatientDashboard />} />
        <Route path='/doctor-dashboard' element={<DoctorDashboard />} />
        <Route path='/patient-profile' element={<PatientProfilePage />} />
        <Route path='/doctor-profile' element={<DoctorProfilePage />} />
      </Routes>
    </Router>
  );
  // The logo is now displayed in the Landing component
}

export default App;