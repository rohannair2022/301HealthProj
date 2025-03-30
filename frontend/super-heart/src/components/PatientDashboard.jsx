import React, { useState, useEffect, useCallback } from 'react';
import './Dashboard.css';
import { redirect, useNavigate } from 'react-router-dom';
import axios from 'axios';
import FileUpload from './FileUpload';
import AddFriendModal from './AddFriendModal';
import StepsChart from './StepsChart';
import HeartRateChart from './HeartRateChart';
import { Modal, Tabs, Tab } from 'react-bootstrap';
import logo from '../logo.png'; // Import the logo
import MobileMenu from './MobileMenu';
import FriendRequestsModal from './FriendRequestsModal';

const PatientDashboard = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [userData, setUserData] = useState({
    heart_score: 0,
    steps: 0,
    sleep: null,
    br: null,
    spo2: null,
    name: '',
    email: '',
    password: '',
    u_id: null,
  });
  const [isHome, setHome] = useState(true);
  const [isUpload, setUpload] = useState(false);
  const [users, setUsers] = useState([]);
  const [friends, setFriends] = useState([]);
  const [error, setError] = useState('');
  const [isAddFriendModalOpen, setIsAddFriendModalOpen] = useState(false);
  const [isProgress, setProgress] = useState(false);
  const [weeklySteps, setWeeklySteps] = useState([]);
  const [weeklyHeartRate, setWeeklyHeartRate] = useState([]);
  const [incomingRequests, setIncomingRequests] = useState([]);
  const [outgoingRequests, setOutgoingRequests] = useState([]);
  const [showRequestsModal, setShowRequestsModal] = useState(false);
  // const [weeklySpO2, setWeeklySpO2] = useState([]);

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
      // Clear ALL storage
      localStorage.clear(); // This will remove token and any other stored data
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
      // Even if the backend call fails, we should still clear storage and redirect
      localStorage.clear();
      navigate('/');
    }
  };

  const handleFitbitLogin = async () => {
    try {
      // First, perform login
      const token = localStorage.getItem('token');
      const codeCreation = await axios.get(
        'http://localhost:5001/connect_watch',
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      console.log('Code creation response:', codeCreation.data);
      const client_id = codeCreation.data.client_id;
      const code_challenge = codeCreation.data.code_challenge;
      const scope =
        'activity cardio_fitness electrocardiogram irregular_rhythm_notifications heartrate profile respiratory_rate oxygen_saturation sleep social weight';

      // Redirect to Fitbit login page
      if (codeCreation.data.status === 'SKIP') {
        alert('You are already connected to Fitbit!');
        return; // Skip the login process if already connected
      } else {
      const authUrl = `https://www.fitbit.com/oauth2/authorize?client_id=${client_id}&response_type=code&code_challenge=${code_challenge}&code_challenge_method=S256&scope=${scope}`;
      window.open(authUrl, '_blank');}
    } catch (error) {
      // Handle different error scenarios
      if (error.response) {
        switch (error.response.status) {
          case 400:
            alert('Please provide both email and password.');
            break;
          case 401:
            alert('Invalid credentials. Please try again.');
            break;
          default:
            alert('An error occurred. Please try again.');
        }
      } else if (error.request) {
        alert('No response from server. Please check your connection.');
      } else {
        alert('Error setting up the login request.');
      }
      console.error('Login error:', error);
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
          sleep: response.data.patient.sleep || null,
          br: response.data.patient.breathing_rate || null,
          spo2: response.data.patient.spo2 || null,
          name: response.data.patient.name || '?',
          email: response.data.patient.email || '?',
          password: response.data.patient.password || '?',
          u_id: response.data.patient.u_id || '?',
        });
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
      if (error.response && error.response.status === 401) {
        navigate('/login');
      }
    }
    setTimeout(fetchUserData, 6000000); // Refresh every 6000 seconds
  }, [navigate]);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5001/list_users', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setUsers(response.data.users);
    } catch (error) {
      console.error('Error fetching users:', error);
      setError('Failed to fetch users');
    }
  };

  const fetchFriends = useCallback(async () => {
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
  }, []);

  const fetchFriendRequests = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        'http://localhost:5001/list_friend_requests',
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setIncomingRequests(response.data.incoming_requests || []);
      setOutgoingRequests(response.data.outgoing_requests || []);
    } catch (error) {
      console.error('Error fetching friend requests:', error);
    }
  }, []);

  const fetchWeeklySteps = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        'http://localhost:5001/get_weekly_steps',
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setWeeklySteps(response.data.weekly_steps);
    } catch (error) {
      console.error('Error fetching weekly steps:', error);
    }
  }, []);

  const fetchHeartRateData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        'http://localhost:5001/get_weekly_heart_rate',
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setWeeklyHeartRate(response.data.weekly_heart_rate);
    } catch (error) {
      console.error('Error fetching heart rate data:', error);
    }
  }, []);

  // const fetchSpO2Data = useCallback(async () => {
  //   try {
  //     const token = localStorage.getItem("token");
  //     const response = await axios.get("http://localhost:5001/get_weekly_spo2", {
  //       headers: { Authorization: `Bearer ${token}` },
  //     });
  //     setWeeklySpO2(response.data.weekly_spo2);
  //   } catch (error) {
  //     console.error("Error fetching SpO2 data:", error);
  //   }
  // }, []);

  const handleAddFriend = async (friendId, friendType) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        'http://localhost:5001/send_friend_request',
        {
          receiver_id: friendId,
          receiver_type: friendType,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );
      // After sending a request, also fetch the friend requests to update the outgoing list
      await fetchFriendRequests();
      // Add success feedback
      alert('Friend request sent successfully!');
    } catch (error) {
      console.error('Error sending friend request:', error);
      // Provide more detailed error feedback
      if (error.response && error.response.data) {
        setError(
          error.response.data.error ||
            error.response.data.message ||
            'Failed to send friend request'
        );
      } else {
        setError('Failed to send friend request. Please try again.');
      }
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
          friend_type: friendType,
        },
      });
      // Refresh friends list after removing
      fetchFriends();
    } catch (error) {
      console.error('Error removing friend:', error);
      setError(error.response?.data?.error || 'Failed to remove friend');
    }
  };

  const handleAcceptRequest = async (requestId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `http://localhost:5001/accept_friend_request/${requestId}`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      // Refresh both requests and friends lists
      fetchFriendRequests();
      fetchFriends();
    } catch (error) {
      console.error('Error accepting friend request:', error);
      setError('Failed to accept friend request');
    }
  };

  const handleRejectRequest = async (requestId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `http://localhost:5001/reject_friend_request/${requestId}`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      fetchFriendRequests();
    } catch (error) {
      console.error('Error rejecting friend request:', error);
      setError('Failed to reject friend request');
    }
  };

  // Global refresh function
  const refreshAllData = async () => {
    console.log('Performing complete data refresh');
    try {
      // Refresh everything in sequence to ensure it's all up to date
      await fetchUserData();
      await fetchFriendRequests();
      await fetchFriends();
      console.log('All data refreshed successfully');
    } catch (err) {
      console.error('Error during global refresh:', err);
    }
  };

  // Add a function to refresh friend requests - update the existing one
  const refreshFriendRequests = async () => {
    await fetchFriendRequests();
  };

  // Add this useEffect to handle the friend requests state
  useEffect(() => {
    // This will run whenever the add friend modal closes
    if (!isAddFriendModalOpen) {
      console.log('Modal closed - refreshing friend requests');
      // Fetch the latest friend requests
      const updateRequestsAfterModalClose = async () => {
        try {
          await fetchFriendRequests();
          console.log('Refreshed friend requests after modal close');
        } catch (err) {
          console.error('Error updating requests after modal close:', err);
        }
      };

      updateRequestsAfterModalClose();
    }
  }, [isAddFriendModalOpen, fetchFriendRequests]);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    setIsDarkMode(savedTheme === 'dark');
    document.body.className = savedTheme === 'dark' ? 'dark-mode' : '';
    fetchUserData();
    fetchFriends();
    fetchFriendRequests();
    fetchWeeklySteps();
    fetchHeartRateData();
    // fetchSpO2Data();
  }, [
    fetchUserData,
    fetchFriends,
    fetchFriendRequests,
    fetchWeeklySteps,
    fetchHeartRateData,
  ]);

  // Theme toggle function
  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.body.className = !isDarkMode ? 'dark-mode' : '';
    localStorage.setItem('theme', !isDarkMode ? 'dark' : 'light');
  };

  // Profile page navigation
  const goToProfile = () => {
    navigate('/patient-profile', { state: { userData, isDarkMode } });
  };

  // Add a useEffect to mark body as dashboard page for specific styling
  useEffect(() => {
    document.body.classList.add('dashboard-active');

    return () => {
      document.body.classList.remove('dashboard-active');
    };
  }, []);

  return (
    <div className='app-container'>
      <MobileMenu />

      {/* Side Navigation */}
      <nav className='side-nav'>
        <div className='logo'>
          <img
            src={logo}
            alt='SuperHeart Logo'
            style={{ maxWidth: '100%', maxHeight: '40px', marginRight: '10px' }}
          />
          SuperHeart
        </div>
        <ul className='nav-links'>
          <li
            onClick={() => {
              setUpload(false);
              setHome(true);
              setProgress(false);
            }}
          >
            <i className='fas fa-home'></i>
            Dashboard
          </li>
          {/* <li
            onClick={() => {
              setUpload(false);
              setHome(false);
              setProgress(false);
            }}
          >
            <i className="fas fa-user-friends"></i>
            Friends
          </li> */}
          <li
            onClick={() => {
              setUpload(false);
              setHome(false);
              setProgress(true);
            }}
          >
            <i className='fas fa-chart-line'></i>
            Progress
          </li>
          <li
            onClick={() => {
              setUpload(true);
              setHome(false);
              setProgress(false);
            }}
          >
            <i className='fas fa-upload'></i>
            Upload Data
          </li>
          <li
            onClick={() => {
              handleFitbitLogin();
            }}
          >
            <i className='fas fa-heart'></i>
            Connect Fitbit
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
      <main
        className='main-content'
        style={{ position: 'relative', paddingTop: '30px' }}
      >
        <div
          style={{
            position: 'absolute',
            top: '40px', // Increased from 20px to 40px
            right: '40px', // Increased from 20px to 40px
            zIndex: 100,
          }}
        >
          <div
            onClick={goToProfile}
            style={{
              cursor: 'pointer',
              width: '50px',
              height: '50px',
              borderRadius: '50%',
              backgroundColor: 'var(--highlight-color)',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              boxShadow: '0 3px 8px rgba(0,0,0,0.2)',
            }}
          >
            <i
              className='fas fa-user-circle'
              style={{ fontSize: '1.8rem', color: 'white' }}
            ></i>
          </div>
        </div>

        {isUpload ? (
          <div>
            <FileUpload />
          </div>
        ) : isHome ? (
          <>
            {/* Dashboard Content */}
            <div className='dashboard-content'>
              <div className='dashboard-header'>
                <h2>Health Overview</h2>
              </div>

              <div className='dashboard-grid'>
                <div className='dashboard-card'>
                  <h3>Heart Health Score</h3>
                  <div className='score'>{userData?.heart_score || 'N/A'}</div>
                  <p>Out of 100</p>
                </div>

                <div className='dashboard-card'>
                  <h3>Daily Steps</h3>
                  <div className='score'>{userData?.steps || 0}</div>
                  <div className='steps-progress'>
                    <div className='progress-bar'>
                      <div
                        className='progress-fill'
                        style={{
                          width: `${((userData?.steps || 0) / 10000) * 100}%`,
                        }}
                      ></div>
                    </div>
                    <p>Target: 10,000 steps</p>
                  </div>
                </div>

                <div className='dashboard-card'>
                  <h3>Sleep</h3>
                  <div className='measurement'>{userData?.sleep || 'N/A'}</div>
                  <p>Minutes Asleep</p>
                </div>

                <div className='dashboard-card'>
                  <h3>Breathing Rate</h3>
                  <div className='measurement'>{userData?.br || 'N/A'}</div>
                  <p>Number of breaths per minute while sleeping</p>
                </div>

                <div className='dashboard-card'>
                  <h3>SpO2</h3>
                  <div className='measurement'>{userData?.spo2 || 'N/A'}</div>
                  <p>Pulse Oxygen Level (in %)</p>
                </div>
              </div>

              {/* Friends Section */}
              <div className='friends-section'>
                <div className='section-header'>
                  <h3>Friends</h3>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                      className='view-requests-btn'
                      onClick={() => setShowRequestsModal(true)}
                    >
                      <i className='fas fa-user-friends'></i> View Requests
                    </button>
                    <button
                      className='add-friend-btn'
                      onClick={() => setIsAddFriendModalOpen(true)}
                    >
                      <i className='fas fa-plus'></i> Add Friend
                    </button>
                  </div>
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
                {error && <div className='error-message'>{error}</div>}
                <div className='friends-list'>
                  {friends.length > 0 ? (
                    friends
                      .filter((friend) =>
                        friend.name
                          .toLowerCase()
                          .includes(searchTerm.toLowerCase())
                      )
                      .map((friend) => (
                        <div key={friend.u_id} className='friend-item'>
                          <div className='friend-info'>
                            <i className='fas fa-user-circle'></i>
                            <span className='friend-name'>{friend.name}</span>
                            <span className={`friend-type ${friend.type}`}>
                              {friend.type.toUpperCase()}
                            </span>
                          </div>
                          <div className='friend-actions'>
                            <span className='friend-score'>
                              {friend.type === 'patient'
                                ? `Score: ${friend.heart_score}`
                                : friend.specialty}
                            </span>
                            <button
                              className='remove-friend-btn'
                              onClick={() =>
                                handleRemoveFriend(friend.u_id, friend.type)
                              }
                              title='Remove friend'
                            >
                              <i className='fas fa-times'></i>
                            </button>
                          </div>
                        </div>
                      ))
                  ) : (
                    <p>No friends added yet.</p>
                  )}
                </div>
              </div>
            </div>

            <AddFriendModal
              show={isAddFriendModalOpen}
              onHide={() => {
                setIsAddFriendModalOpen(false);
                refreshAllData(); // Refresh everything when modal closes
              }}
              onRequestSent={() => {
                console.log('Friend request sent from modal');
                refreshAllData().then(() => {
                  setShowRequestsModal(true); // Show requests after refresh
                });
              }}
              handleAddFriend={async (...args) => {
                await handleAddFriend(...args);
                await refreshAllData();
              }}
            />
          </>
        ) : isProgress ? ( // Progress Section
          <div className='dashboard-content'>
            {/* Horizontal Layout for Steps and Heart Rate Charts */}
            <div className='horizontal-charts-container'>
              {/* Steps Chart */}
              <div className='horizontal-chart'>
                <StepsChart data={weeklySteps} />
              </div>

              {/* Heart Rate Chart */}
              <div className='horizontal-chart'>
                <HeartRateChart data={weeklyHeartRate} />
              </div>
            </div>

            {/* Weekly Summary Below */}
            <div className='stats-summary'>
              <h3>Weekly Summary</h3>
              <div className='stats-grid'>
                {/* Steps Statistics */}
                <div className='stat-item'>
                  <span>Total Steps</span>
                  <strong>
                    {weeklySteps.reduce(
                      (sum, day) => sum + (day.steps || 0),
                      0
                    )}
                  </strong>
                </div>
                <div className='stat-item'>
                  <span>Avg Daily Steps</span>
                  <strong>
                    {Math.round(
                      weeklySteps.reduce(
                        (sum, day) => sum + (day.steps || 0),
                        0
                      ) / 7
                    )}
                  </strong>
                </div>

                {/* Heart Rate Statistics */}
                <div className='stat-item'>
                  <span>Avg Heart Rate</span>
                  <strong>
                    {weeklyHeartRate.length > 0
                      ? Math.round(
                          weeklyHeartRate.reduce(
                            (sum, day) => sum + (day.heart_rate || 0),
                            0
                          ) / 7
                        )
                      : 'N/A'}
                  </strong>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </main>

      {/* Friend Requests Modal */}
      <FriendRequestsModal
        show={showRequestsModal}
        onHide={() => setShowRequestsModal(false)}
        incomingRequests={incomingRequests}
        outgoingRequests={outgoingRequests}
        handleAcceptRequest={handleAcceptRequest}
        handleRejectRequest={handleRejectRequest}
        onRequestUpdated={refreshAllData}
        onForceRefresh={refreshAllData}
        refreshButton={true} // Add a refresh button to the modal
      />
    </div>
  );
};

export default PatientDashboard;
