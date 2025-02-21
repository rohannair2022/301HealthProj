import logo from './logo.svg';
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

function App() {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<Landing />} />
        <Route path='/login' element={<Login />} />
        <Route path='/register' element={<Register />} />
        <Route path='/test' element={<Test />} />
        <Route path='/patient-dashboard' element={<PatientDashboard />} />
        <Route path='/doctor-dashboard' element={<DoctorDashboard />} />
        <Route path='/patient-profile' element={<PatientProfilePage />} />
        <Route path='/doctor-profile' element={<DoctorProfilePage />} />
      </Routes>
    </Router>
  );
  //   <div className="App">
  //     <header className="App-header">
  //       <img src={logo} className="App-logo" alt="logo" />
  //       <p>
  //         Edit <code>src/App.js</code> and save to reload.
  //       </p>
  //       <a
  //         className="App-link"
  //         href="https://reactjs.org"
  //         target="_blank"
  //         rel="noopener noreferrer"
  //       >
  //         Learn React
  //       </a>
  //     </header>
  //   </div>
  // );
}

export default App;