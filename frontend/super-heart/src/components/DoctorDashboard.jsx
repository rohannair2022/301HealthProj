import React, { useState, useEffect, useCallback } from 'react';
import './Dashboard.css';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import AddFriendModal from './AddFriendModal';
import { Modal, Button, Form, Tabs, Tab } from 'react-bootstrap';
import logo from '../logo.png'; // Import the logo
import MobileMenu from './MobileMenu';
import FriendRequestsModal from './FriendRequestsModal';

const DoctorDashboard = () => {
  const navigate = useNavigate();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [doctorData, setDoctorData] = useState({
    name: '',
    specialty: '',
    email: '',
    password: '',
    u_id: null,
  });
  const [isAddFriendModalOpen, setIsAddFriendModalOpen] = useState(false);
  const [friends, setFriends] = useState([]);
  const [patientFiles, setPatientFiles] = useState({}); // Map patient id -> files array
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  // New state variables for friend requests
  const [incomingRequests, setIncomingRequests] = useState([]);
  const [outgoingRequests, setOutgoingRequests] = useState([]);
  const [showRequestsModal, setShowRequestsModal] = useState(false);

  // States for updating health score
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [newHealthScore, setNewHealthScore] = useState('');

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        'http://localhost:5001/logout',
        {},
        { headers: { Authorization: `Bearer ${token}` } }
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
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.data) setDoctorData(response.data.doctor);
    } catch (error) {
      console.error('Error fetching doctor data:', error);
      if (error.response?.status === 401) navigate('/login');
    }
  };

  // Fetch friends (patients) and then their files
  const fetchFriends = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5001/list_friends', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const friendsData = response.data.friends || [];
      setFriends(friendsData);
      updatePatientFiles(friendsData);
    } catch (error) {
      console.error('Error fetching friends:', error);
      setError('Failed to fetch friends');
    }
  }, []);

  // New function to fetch friend requests
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

  // New functions for handling friend requests
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

  // Fetch files for a single patient
  const fetchPatientFiles = async (patientId) => {
    try {
      const token = localStorage.getItem('token');
      // Assumes a new endpoint for doctor to view patient's files exists:
      const response = await axios.get(
        `http://localhost:5001/doctor/files/${patientId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data.files || [];
    } catch (error) {
      console.error('Error fetching files for patient', patientId, error);
      return [];
    }
  };

  // Update the patientFiles mapping for each patient
  const updatePatientFiles = async (friendsList) => {
    const newPatientFiles = {};
    await Promise.all(
      friendsList.map(async (friend) => {
        if (friend.type === 'patient') {
          const files = await fetchPatientFiles(friend.u_id);
          newPatientFiles[friend.u_id] = files;
        }
      })
    );
    setPatientFiles(newPatientFiles);
  };

  const handleFitbitLogin = async () => {
    try {
      const token = localStorage.getItem('token');
      const codeCreation = await axios.get(
        'http://localhost:5001/connect_watch',
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const { client_id, code_challenge } = codeCreation.data;
      const scope =
        'activity cardio_fitness electrocardiogram irregular_rhythm_notifications heartrate profile respiratory_rate oxygen_saturation sleep social weight';
      const authUrl = `https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=${client_id}&scope=${scope}&code_challenge_method=S256&code_challenge=${code_challenge}`;
      window.open(authUrl, '_blank');
    } catch (error) {
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

  // Updated function to use send_friend_request endpoint
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
      // Add success message
      alert('Friend request sent successfully!');
      // Refresh friend requests to see the new outgoing request
      await fetchFriendRequests();
      // If requests modal is open, the updated list should now show
    } catch (error) {
      console.error('Error sending friend request:', error);
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
          'Content-Type': 'application/json',
        },
        data: {
          friend_id: friendId,
          friend_type: friendType,
        },
      });
      // Add success message
      alert('Friend removed successfully!');
      // Clear any errors
      setError('');
      // Refresh friends list
      fetchFriends();
    } catch (error) {
      console.error('Error removing friend:', error);
      if (error.response && error.response.data) {
        setError(error.response.data.error || 'Failed to remove friend');
      } else {
        setError('Failed to remove friend. Please try again.');
      }
    }
  };

  // Health score update functions
  const handleOpenUpdateModal = (patient) => {
    setSelectedPatient(patient);
    setNewHealthScore(patient.heart_score);
    setShowUpdateModal(true);
  };

  const handleCloseUpdateModal = () => {
    setShowUpdateModal(false);
    setSelectedPatient(null);
  };

  const handleUpdateHealthScore = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        'http://localhost:5001/doctor/update_health_score',
        { health_score: newHealthScore, patient_id: selectedPatient.u_id },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('Health score updated successfully!');
      setShowUpdateModal(false);
      fetchFriends();
    } catch (error) {
      console.error('Error updating health score:', error);
      alert('Failed to update health score');
    }
  };

  const refreshFriendRequests = async () => {
    await fetchFriendRequests();
  };

  // Global refresh function
  const refreshAllData = async () => {
    console.log('Performing complete data refresh');
    try {
      // Refresh everything in sequence to ensure it's all up to date
      await fetchDoctorData();
      await fetchFriendRequests();
      await fetchFriends();
      console.log('All data refreshed successfully');
    } catch (err) {
      console.error('Error during global refresh:', err);
    }
  };

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    setIsDarkMode(savedTheme === 'dark');
    document.body.className = savedTheme === 'dark' ? 'dark-mode' : '';
    fetchDoctorData();
    fetchFriends();
    fetchFriendRequests();
  }, [fetchFriends, fetchFriendRequests]);

  // Add a useEffect to mark body as dashboard page for specific styling
  useEffect(() => {
    document.body.classList.add('dashboard-active');

    return () => {
      document.body.classList.remove('dashboard-active');
    };
  }, []);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.body.className = !isDarkMode ? 'dark-mode' : '';
    localStorage.setItem('theme', !isDarkMode ? 'dark' : 'light');
  };

  const goToProfile = () => {
    navigate('/doctor-profile', { state: { doctorData } });
  };

  useEffect(() => {
    console.log('isAddFriendModalOpen:', isAddFriendModalOpen);
  }, [isAddFriendModalOpen]);

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

  return (
    <div className='app-container'>
      <MobileMenu />

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
          <li>
            <i className='fas fa-home'></i> Dashboard
          </li>
          <li>
            <i className='fas fa-user-friends'></i> My Patients
          </li>
          <li onClick={toggleTheme} className='theme-toggle'>
            <i className={`fas ${isDarkMode ? 'fa-sun' : 'fa-moon'}`}></i>
            {isDarkMode ? 'Light Mode' : 'Dark Mode'}
          </li>
          <li onClick={handleFitbitLogin}>
            <i className='fas fa-heart'></i> Connect Fitbit
          </li>
          <li onClick={handleLogout} className='logout-btn'>
            <i className='fas fa-sign-out-alt'></i> Logout
          </li>
        </ul>
      </nav>

      <main
        className='main-content'
        style={{ position: 'relative', paddingTop: '30px' }}
      >
        <div className='profile-circle' onClick={goToProfile}>
          <i className='fas fa-user-circle'></i>
        </div>

        {/* Remove the inline styles div for profile button 
            and replace with our standardized component */}

        <div className='dashboard-content'>
          <div className='dashboard-header'>
            <h2>Welcome, Dr. {doctorData.name}</h2>
            <p>Specialty: {doctorData.specialty}</p>
          </div>

          <div className='friends-section'>
            <div className='section-header'>
              <h3>My Patients</h3>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  className='view-requests-btn'
                  onClick={() => setShowRequestsModal(true)}
                >
                  <i className='fas fa-user-friends'></i> View Requests
                </button>
                <button
                  className='add-friend-btn'
                  onClick={() => {
                    console.log('Add Patient button clicked');
                    setIsAddFriendModalOpen(true);
                  }}
                >
                  <i className='fas fa-plus'></i> Add Patient
                </button>
              </div>
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
                          className='update-score-btn'
                          onClick={() => handleOpenUpdateModal(friend)}
                          title='Update Health Score'
                        >
                          <i className='fas fa-edit'></i>
                        </button>
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
                      {/* Display patient's uploaded files */}
                      {patientFiles[friend.u_id] &&
                        patientFiles[friend.u_id].length > 0 && (
                          <div className='patient-files'>
                            <strong>Files:</strong>
                            <ul>
                              {patientFiles[friend.u_id].map((file, idx) => (
                                <li key={idx}>
                                  <a
                                    href={`http://localhost:5001/doctor/files/${friend.u_id}/${file}`}
                                    target='_blank'
                                    rel='noopener noreferrer'
                                  >
                                    {file}
                                  </a>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                    </div>
                  ))
              ) : (
                <p>No patients added yet.</p>
              )}
            </div>
          </div>
        </div>

        {isAddFriendModalOpen && (
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
            isDoctor={true}
            handleAddFriend={async (...args) => {
              await handleAddFriend(...args);
              await refreshAllData();
            }}
          />
        )}

        {/* Modal for updating health score */}
        <Modal show={showUpdateModal} onHide={handleCloseUpdateModal}>
          <Modal.Header closeButton>
            <Modal.Title>Update Health Score</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group>
              <Form.Label>New Health Score</Form.Label>
              <Form.Control
                type='number'
                value={newHealthScore}
                onChange={(e) => setNewHealthScore(e.target.value)}
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant='secondary' onClick={handleCloseUpdateModal}>
              Close
            </Button>
            <Button variant='primary' onClick={handleUpdateHealthScore}>
              Save Changes
            </Button>
          </Modal.Footer>
        </Modal>

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
          isDoctor={true}
          refreshButton={true} // Add a refresh button to the modal
        />
      </main>
    </div>
  );
};

export default DoctorDashboard;
