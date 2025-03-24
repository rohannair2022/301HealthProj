import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AddFriendModal = ({ show, onHide }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [allUsers, setAllUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [pendingRequestIds, setPendingRequestIds] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // Prevent body scrolling when modal is open
  useEffect(() => {
    if (show) {
      document.body.style.overflow = 'hidden';
      // Load data when modal opens
      fetchPendingRequests();
    } else {
      document.body.style.overflow = 'auto';
    }

    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [show]);

  // Fetch pending requests to exclude those users
  const fetchPendingRequests = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/list_friend_requests', {
        headers: { Authorization: `Bearer ${token}` },
      });

      // Extract user IDs from outgoing requests
      const outgoingRequestIds = response.data.outgoing_requests.map(
        (req) => req.u_id
      );
      setPendingRequestIds(outgoingRequestIds);

      // Now fetch available users
      fetchAllUsers(outgoingRequestIds);
    } catch (err) {
      console.error('Error fetching pending requests:', err);
      // Continue with fetching users anyway
      fetchAllUsers([]);
    }
  };

  // Fetch all users when the modal opens
  const fetchAllUsers = async (outgoingRequestIds = []) => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/list_users', {
        headers: { Authorization: `Bearer ${token}` },
      });

      // Filter out users who already have pending requests
      const filteredUsersList = response.data.users.filter(
        (user) => !outgoingRequestIds.includes(user.u_id)
      );

      setAllUsers(filteredUsersList);
      setFilteredUsers(filteredUsersList);

      if (filteredUsersList.length === 0) {
        setError('No users available to add as friends.');
      }
    } catch (err) {
      setError('Error loading users. Please try again.');
      console.error('Load users error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle search input changes
  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchTerm(value);

    // Filter users based on search term
    if (value.trim() === '') {
      setFilteredUsers(allUsers);
    } else {
      const filtered = allUsers.filter(
        (user) =>
          user.name.toLowerCase().includes(value.toLowerCase()) ||
          user.email.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredUsers(filtered);

      if (filtered.length === 0) {
        setError('No users found matching your search');
      } else {
        setError(null);
      }
    }
  };

  const handleAddFriend = async (userId, userType) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        '/send_friend_request',
        {
          receiver_id: userId,
          receiver_type: userType,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      // Remove the user from the list after sending a request
      const updatedUsers = allUsers.filter((user) => user.u_id !== userId);
      setAllUsers(updatedUsers);
      setFilteredUsers(filteredUsers.filter((user) => user.u_id !== userId));

      // If no users left after filtering, show appropriate message
      if (filteredUsers.length <= 1) {
        if (searchTerm) {
          setError('No more users found matching your search');
        } else if (updatedUsers.length === 0) {
          setError('No more users available to add as friends');
        }
      }
    } catch (err) {
      setError('Failed to send friend request. Please try again.');
      console.error('Add friend error:', err);
    }
  };

  if (!show) return null;

  return (
    <div
      className='custom-modal-overlay'
      onClick={(e) => {
        if (e.target.className === 'custom-modal-overlay') onHide();
      }}
    >
      <div className='custom-modal add-friend-modal'>
        <div className='custom-modal-header'>
          <h5 className='custom-modal-title'>Add Friend</h5>
          <button className='custom-close-button' onClick={onHide}>
            ×
          </button>
        </div>
        <div className='custom-modal-body'>
          <div className='search-container'>
            <div className='search-form'>
              <span className='search-icon'>
                <i className='fas fa-search'></i>
              </span>
              <input
                type='text'
                placeholder='Search by name or email...'
                value={searchTerm}
                onChange={handleSearchChange}
                className='search-input'
              />
            </div>
          </div>

          {loading && (
            <div className='loading-indicator'>
              <i className='fas fa-spinner fa-spin'></i>
              <span>Loading users...</span>
            </div>
          )}

          {error && !loading && filteredUsers.length === 0 && (
            <div className='no-results-message'>
              <i className='fas fa-search'></i>
              <p>{error}</p>
              {searchTerm && (
                <button
                  className='clear-search-btn'
                  onClick={() => {
                    setSearchTerm('');
                    setFilteredUsers(allUsers);
                    setError(null);
                  }}
                >
                  <i className='fas fa-times-circle'></i> Clear Search
                </button>
              )}
            </div>
          )}

          <div className='search-results'>
            {filteredUsers.map((user) => (
              <div key={user.u_id} className='user-item'>
                <div className='user-info'>
                  <i className='fas fa-user-circle'></i>
                  <div className='user-details'>
                    <div className='user-primary-info'>
                      <span className='user-name'>{user.name}</span>
                      <span className={`user-type ${user.type.toLowerCase()}`}>
                        {user.type.toUpperCase()}
                      </span>
                    </div>
                    <span className='user-email'>{user.email}</span>
                    {user.type === 'doctor' && user.specialty && (
                      <span className='specialty'>
                        <i className='fas fa-stethoscope'></i> {user.specialty}
                      </span>
                    )}
                    {user.type === 'patient' &&
                      user.heart_score !== undefined && (
                        <span className='heart-score'>
                          <i className='fas fa-heartbeat'></i> Heart Score:{' '}
                          {user.heart_score}
                        </span>
                      )}
                  </div>
                </div>
                <button
                  className='add-friend-btn'
                  onClick={() => handleAddFriend(user.u_id, user.type)}
                >
                  <i className='fas fa-user-plus'></i> Add Friend
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddFriendModal;
