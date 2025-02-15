import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const DoctorDashboard = () => {
  const navigate = useNavigate();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [doctorData, setDoctorData] = useState({
    name: '',
    specialty: '',
    email: '',
  });

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        'http://localhost:5001/logout',
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      localStorage.removeItem('token');
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
      localStorage.removeItem('token');
      navigate('/');
    }
  };

  const fetchDoctorData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5001/get_doctor', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.data) {
        setDoctorData(response.data.doctor);
      }
    } catch (error) {
      console.error('Error fetching doctor data:', error);
      if (error.response && error.response.status === 401) {
        navigate('/login');
      }
    }
  };

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    setIsDarkMode(savedTheme === 'dark');
    document.body.className = savedTheme === 'dark' ? 'dark-mode' : '';
    fetchDoctorData();
  }, []);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.body.className = !isDarkMode ? 'dark-mode' : '';
    localStorage.setItem('theme', !isDarkMode ? 'dark' : 'light');
  };

  return (
    <div className='app-container'>
      <nav className='side-nav'>
        <div className='logo'>SuperHeart</div>
        <ul className='nav-links'>
          <li>
            <i className='fas fa-home'></i>
            Dashboard
          </li>
          <li>
            <i className='fas fa-user-friends'></i>
            My Patients
          </li>
          <li onClick={toggleTheme} className='theme-toggle'>
            <i className={`fas ${isDarkMode ? 'fa-sun' : 'fa-moon'}`}></i>
            {isDarkMode ? 'Light Mode' : 'Dark Mode'}
          </li>
          <li onClick={handleLogout} className='logout-btn'>
            <i className='fas fa-sign-out-alt'></i>
            Logout
          </li>
        </ul>
      </nav>

      <main className='main-content'>
        <header className='top-header'>
          <div className='header-right'>
            <i className='fas fa-bell'></i>
            <i className='fas fa-user-circle'></i>
          </div>
        </header>

        <div className='dashboard-content'>
          <div className='dashboard-header'>
            <h2>Welcome, Dr. {doctorData.name}</h2>
            <p>Specialty: {doctorData.specialty}</p>
          </div>

          <div className='friends-section'>
            <div className='section-header'>
              <h3>My Patients</h3>
              <button className='add-friend-btn'>
                <i className='fas fa-plus'></i> Add Patient
              </button>
            </div>
            <div className='friends-list'>
              <p>No patients added yet.</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DoctorDashboard;