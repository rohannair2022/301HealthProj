import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import AddFriendModal from './AddFriendModal';

const DoctorDashboard = () => {
  const navigate = useNavigate();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [doctorData, setDoctorData] = useState({
    name: '',
    specialty: '',
    email: '',
  });
  const [isAddFriendModalOpen, setIsAddFriendModalOpen] = useState(false);
  const [friends, setFriends] = useState([]);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

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

  const fetchFriends = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5001/list_friends', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setFriends(response.data.friends || []);
    } catch (error) {
      console.error('Error fetching friends:', error);
      setError('Failed to fetch friends');
    }
  };

  const handleAddFriend = async (friendId, friendType) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        'http://localhost:5001/add_friend',
        {
          friend_id: friendId,
          friend_type: friendType,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      fetchFriends(); // Refresh the friends list after adding
    } catch (error) {
      console.error('Error adding friend:', error);
      setError(error.response?.data?.error || 'Failed to add friend');
    }
  };

  const handleRemoveFriend = async (friendId, friendType) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete('http://localhost:5001/remove_friend', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        data: {
          friend_id: friendId,
          friend_type: 'patient', // Always 'patient' for doctors
        },
      });
      // Refresh friends list after removing
      fetchFriends();
    } catch (error) {
      console.error('Error removing friend:', error);
      setError(error.response?.data?.error || 'Failed to remove friend');
    }
  };

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    setIsDarkMode(savedTheme === 'dark');
    document.body.className = savedTheme === 'dark' ? 'dark-mode' : '';
    fetchDoctorData();
    fetchFriends();
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
              <button
                className='add-friend-btn'
                onClick={() => setIsAddFriendModalOpen(true)}
              >
                <i className='fas fa-plus'></i> Add Patient
              </button>
            </div>
            <div className='search-bar'>
              <i className='fas fa-search'></i>
              <input
                type='text'
                placeholder='Search patients...'
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            {error && <div className='error-message'>{error}</div>}
            <div className='friends-list'>
              {friends.length > 0 ? (
                friends
                  .filter((friend) =>
                    friend.name.toLowerCase().includes(searchTerm.toLowerCase())
                  )
                  .map((friend) => (
                    <div key={friend.u_id} className='friend-item'>
                      <div className='friend-info'>
                        <i className='fas fa-user-circle'></i>
                        <span className='friend-name'>{friend.name}</span>
                        <span className='friend-type patient'>PATIENT</span>
                      </div>
                      <div className='friend-actions'>
                        <span className='friend-score'>
                          Score: {friend.heart_score}
                        </span>
                        <button
                          className='remove-friend-btn'
                          onClick={() =>
                            handleRemoveFriend(friend.u_id, 'patient')
                          }
                          title='Remove patient'
                        >
                          <i className='fas fa-times'></i>
                        </button>
                      </div>
                    </div>
                  ))
              ) : (
                <p>No patients added yet.</p>
              )}
            </div>
          </div>
        </div>

        <AddFriendModal
          isOpen={isAddFriendModalOpen}
          onClose={() => setIsAddFriendModalOpen(false)}
          onAddFriend={handleAddFriend}
        />
      </main>
    </div>
  );
};

export default DoctorDashboard;
