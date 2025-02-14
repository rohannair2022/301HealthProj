import React, { useState, useEffect, useCallback } from 'react';
import './Dashboard.css';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import FileUpload from './FileUpload';

const Dashboard = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [userData, setUserData] = useState({
    heart_score: 0,
    steps: 0,
  });
  const [isHome, setHome] = useState(true)
  const [isUpload, setUpload] = useState(false)


  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post('http://localhost:5001/logout', {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      localStorage.removeItem('token'); // Clear the token
      navigate('/'); // Navigate to landing page
    } catch (error) {
      console.error('Logout error:', error);
      // Even if the backend call fails, we should still clear local storage and redirect
      localStorage.removeItem('token');
      navigate('/');
    }
  };

  const fetchUserData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');

      const response = await axios.get('http://localhost:5001/get_patient', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.data) {
        setUserData({
          heart_score: response.data.patient.heart_score || 0,
          steps: response.data.patient.steps || 0,
        });
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
      if (error.response && error.response.status === 401) {
        navigate('/login');
      }
    }
  }, [navigate]);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    setIsDarkMode(savedTheme === 'dark');
    document.body.className = savedTheme === 'dark' ? 'dark-mode' : '';
    fetchUserData();
  }, [fetchUserData]);

  // Theme toggle function
  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.body.className = !isDarkMode ? 'dark-mode' : '';
    localStorage.setItem('theme', !isDarkMode ? 'dark' : 'light');
  };

  const friends = [
    { id: 1, name: 'John Doe', heartScore: 8.5 },
    { id: 2, name: 'Jane Smith', heartScore: 7.2 },
    { id: 3, name: 'Mike Johnson', heartScore: 9.0 },
  ];

  const filteredFriends = friends.filter((friend) =>
    friend.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className='app-container'>
      {/* Side Navigation */}
      <nav className='side-nav'>
        <div className='logo'>SuperHeart</div>
        <ul className='nav-links'>
          <li onClick={() => {
            setUpload(false);
            setHome(true);
          }}>
            <i className='fas fa-home'></i>
            Dashboard
          </li>
          <li>
            <i className='fas fa-user-friends'></i>
            Friends
          </li>
          <li>
            <i className='fas fa-chart-line'></i>
            Progress
          </li>
          <li onClick={() => {
            setUpload(true);
            setHome(false);
          }}>
            <i className='fas fa-upload'></i>
            Upload Data
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
      
      {/* Main Content */}
      <main className='main-content'>
        {isUpload ? (
          <div>
           <FileUpload/>
          </div>
        ) : isHome ? (
          <>
            <header className='top-header'>
              <div className='header-search'>
                <i className='fas fa-search'></i>
                <input type='text' placeholder='Search...' />
              </div>
              <div className='header-right'>
                <i className='fas fa-bell'></i>
                <i className='fas fa-user-circle'></i>
              </div>
            </header>

            {/* Dashboard Content */}
            <div className='dashboard-content'>
              <div className='dashboard-header'>
                <h2>Health Overview</h2>
              </div>

              <div className='dashboard-grid'>
                <div className='dashboard-card'>
                  <h3>Heart Health Score</h3>
                  <div className='score'>{userData?.heart_score || 'N/A'}</div>
                  <p>Out of 10</p>
                </div>

                <div className='dashboard-card'>
                  <h3>Daily Steps</h3>
                  <div className='score'>{userData?.steps || 0}</div>
                  <div className='steps-progress'>
                    <div className='progress-bar'>
                      <div
                        className='progress-fill'
                        style={{ width: `${((userData?.steps || 0) / 10000) * 100}%` }}
                      ></div>
                    </div>
                    <p>Target: 10,000 steps</p>
                  </div>
                </div>

                <div className='dashboard-card'>
                  <h3>Height</h3>
                  <div className='measurement'>{userData?.height || 'N/A'}</div>
                  <p>Current Height</p>
                </div>

                <div className='dashboard-card'>
                  <h3>Weight</h3>
                  <div className='measurement'>{userData?.weight || 'N/A'}</div>
                  <p>Current Weight</p>
                </div>
              </div>

              <div className='friends-section'>
                <div className='section-header'>
                  <h3>Friends</h3>
                  <button className='add-friend-btn'>
                    <i className='fas fa-plus'></i> Add Friend
                  </button>
                </div>
                <div className='search-bar'>
                  <i className='fas fa-search'></i>
                  <input
                    type='text'
                    placeholder='Search friends...'
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <div className='friends-list'>
                  {filteredFriends.map((friend) => (
                    <div key={friend.id} className='friend-item'>
                      <div className='friend-info'>
                        <i className='fas fa-user-circle'></i>
                        <span className='friend-name'>{friend.name}</span>
                      </div>
                      <span className='friend-score'>
                        Score: {friend.heartScore}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : null}
      </main>

    </div>
  );
};

export default Dashboard;
