import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Dashboard.css';

const AddFriendModal = ({ isOpen, onClose, onAddFriend }) => {
  const [users, setUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetchUsers();
    }
  }, [isOpen]);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5001/list_users', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setUsers(response.data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      setError('Failed to fetch users');
    }
  };

  const filteredUsers = users.filter((user) =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleAddFriend = (userId, userType) => {
    try {
      onAddFriend(userId, userType);
      onClose();
    } catch (error) {
      setError('Failed to send friend request');
    }
  };

  if (!isOpen) return null;

  return (
    <div className='modal-overlay'>
      <div className='modal-content'>
        <div className='modal-header'>
          <h3>Add Friend</h3>
          <button className='close-button' onClick={onClose}>
            <i className='fas fa-times'></i>
          </button>
        </div>

        <div className='search-bar'>
          <i className='fas fa-search'></i>
          <input
            type='text'
            placeholder='Search users...'
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            autoFocus
          />
        </div>

        {error && <div className='error-message'>{error}</div>}

        <div className='users-list'>
          {filteredUsers.length > 0 ? (
            filteredUsers.map((user) => (
              <div key={user.u_id} className='user-item'>
                <div className='user-info'>
                  <i className='fas fa-user-circle'></i>
                  <div className='user-details'>
                    <div className='user-primary-info'>
                      <span className='user-name'>{user.name}</span>
                      <span className='user-type'>
                        {user.type.toUpperCase()}
                      </span>
                    </div>
                    <span className='user-email'>{user.email}</span>
                    {user.type === 'doctor' && (
                      <span className='specialty'>{user.specialty}</span>
                    )}
                    {user.type === 'patient' && (
                      <span className='heart-score'>
                        Heart Score: {user.heart_score}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  className='add-friend-btn'
                  onClick={() => {
                    handleAddFriend(user.u_id, user.type);
                  }}
                >
                  Add Friend
                </button>
              </div>
            ))
          ) : (
            <div className='no-users-message'>
              <i className='fas fa-search'></i>
              <p>No users found matching your search</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AddFriendModal;
