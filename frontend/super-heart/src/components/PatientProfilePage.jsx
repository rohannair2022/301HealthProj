import React, { useState, useEffect, useCallback } from 'react';
import './ProfilePage.css';
import axios from 'axios';
import bcrypt from 'bcryptjs';
import { Link } from "react-router-dom";
import { BsArrowLeft } from "react-icons/bs";

// Modal Components
const EditNameModal = ({ isVisible, closeModal, handleNameSubmit, formData, handleChange }) => {
    const handleOverlayClick = (e) => {
      if (e.target.classList.contains('modal-overlay')) {
        closeModal();
      }
    };
  
    return (
      isVisible && (
        <div className="modal-overlay" onClick={handleOverlayClick}>
          <div className="name-modal">
            <h2>Edit Name</h2>
            <form onSubmit={(e) => handleNameSubmit(e)}>
              <input
                type="text"
                id="name"
                name="name"
                onChange={handleChange}
                required
                value={formData.name}
                placeholder="Enter new name..."
              />
              <div className="modal-actions">
                <button type="button" onClick={closeModal}>Close</button>
                <button type="submit">Submit</button>
              </div>
            </form>
          </div>
        </div>
      )
    );
  };

  
const EditEmailModal = ({ isVisible, closeModal, handleEmailSubmit, formData, handleChange }) => {
  const handleOverlayClick = (e) => {
    if (e.target.classList.contains('modal-overlay')) {
      closeModal();
    }
  };

  return (
    isVisible && (
      <div className="modal-overlay" onClick={handleOverlayClick}>
        <div className="email-modal">
          <h2>Edit Email</h2>
          <form onSubmit={(e) => handleEmailSubmit(e)}>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter new email..."
            />
            <div className="modal-actions">
              <button type="button" onClick={closeModal}>Close</button>
              <button type="submit">Submit</button>
            </div>
          </form>
        </div>
      </div>
    )
  );
};

const EditPasswordModal = ({ isVisible, closeModal, handlePasswordSubmit, formData, handleChange, step, setStep, handleOldPasswordCheck }) => {
    const handleOverlayClick = (e) => {
      if (e.target.classList.contains('modal-overlay')) {
        closeModal();
      }
    };
  
    return (
      isVisible && (
        <div className="modal-overlay" onClick={handleOverlayClick}>
          <div className="password-modal">
            <h2>Edit Password</h2>
            {step === 1 ? (
              <form onSubmit={(e) => handleOldPasswordCheck(e)}>
                <input
                  type="password"
                  id="oldPassword"
                  name="oldPassword"
                  onChange={handleChange}
                  required
                  placeholder="Enter old password..."
                />
                <div className="modal-actions">
                  <button type="button" onClick={closeModal}>Close</button>
                  <button type="submit">Submit</button>
                </div>
              </form>
            ) : (
              <form onSubmit={(e) => handlePasswordSubmit(e)}>
                <input
                  type="password"
                  id="newPassword"
                  name="newPassword"
                  value={formData.newPassword}
                  onChange={handleChange}
                  required
                  placeholder="Enter new password..."
                />
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                  placeholder="Confirm new password..."
                />
                <div className="modal-actions">
                  <button type="button" onClick={closeModal}>Close</button>
                  <button type="submit">Submit</button>
                </div>
              </form>
            )}
          </div>
        </div>
      )
    );
  };

const ProfilePage = () => {
  const [nameModalVisible, setNameModalVisible] = useState(false);
  const [emailModalVisible, setEmailModalVisible] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [step, setStep] = useState(1); // 1 - Old password, 2 - New password 
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    confirmPassword: '',
    oldPassword: ''
  });
  const [userData, setUserData] = useState({
    heart_score: 0,
    steps: 0,
    name: '',
    email: '',
    password: '',
    u_id: null
  });

  const fetchUserData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');

      const response = await axios.get('http://localhost:5001/get_patient', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.data) {
        const fetchedUserData = response.data.patient;
        setUserData({
          heart_score: fetchedUserData.heart_score || 0,
          steps: fetchedUserData.steps || 0,
          name: fetchedUserData.name || '?',
          email: fetchedUserData.email || '?',
          password: fetchedUserData.password || '?',
          u_id: fetchedUserData.u_id || '?',
        });

        setFormData({
          email: fetchedUserData.email || '',
        });

        console.log(userData);
      }

    } catch (error) {
      console.error('Error fetching user data:', error);
    }
  }, []);

  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  const openNameModal = () => {
    setNameModalVisible(true);
  };

  const closeNameModal = () => {
    setNameModalVisible(false);
  };

  const openEmailModal = () => {
    setEmailModalVisible(true);
  };

  const closeEmailModal = () => {
    setEmailModalVisible(false);
  };

  const openPasswordModal = () => {
    setPasswordModalVisible(true);
  };

  const closePasswordModal = () => {
    setPasswordModalVisible(false);
    setStep(1);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleNameSubmit = (e) => {
    e.preventDefault();

    const updatedName = formData.name;

    fetch(`http://localhost:5001/edit_patient/${userData.u_id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: updatedName,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.message) {
          alert('Name updated successfully!');
          window.location.reload();
        } 
        else {
          alert('Error updating name: ' + (data.error || 'Unknown error'));
        }
      })
      .catch((error) => {
        alert('Error updating name: ' + error.message);
      });

    closeNameModal();
  };


  const handleEmailSubmit = (e) => {
    e.preventDefault();
  
    const updatedEmail = formData.email;
  
    fetch(`http://localhost:5001/edit_patient/${userData.u_id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: updatedEmail,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.message) {
          alert('Email updated successfully!');
          
          // Instead of reloading the page, refresh the user data
          fetchUserData(); 
        }
        else {
          alert('Error updating email: ' + (data.error || 'Unknown error'));
        }
      })
      .catch((error) => {
        alert('Error updating email: ' + error.message);
      });
  
    closeEmailModal();
  };

  const handleOldPasswordCheck = async (e) => {
    e.preventDefault();

    const enteredPassword = formData.oldPassword;
    const hashedPassword = userData.password;

    const match = await bcrypt.compare(enteredPassword, hashedPassword);

    if (match) {
        setStep(2);
    } 
    else {
        alert("Old password is incorrect, please try again.");
    }

    console.log("Entered: " + enteredPassword);
    console.log("Stored (hashed): " + hashedPassword);
};

  const handlePasswordSubmit = (e) => {
    e.preventDefault();

    if (formData.newPassword === formData.confirmPassword) {
      fetch(`http://localhost:5001/edit_patient/${userData.u_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          password: formData.newPassword,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.message) {
            alert('Password updated successfully!');
            setPasswordModalVisible(false);
          } 
          else {
            alert('Error updating password: ' + (data.error || 'Unknown error'));
          }
        })
        .catch((error) => {
          alert('Error updating password: ' + error.message);
        });
    } 
    else {
      alert("New password do not match the confirmation, please try again.");
    }
  };
  

  return (
    <div>
        <Link to="/patient-dashboard" className="back-button">
            <BsArrowLeft />
        </Link>
        {userData ? (
        <div className="container">
            <div className="profile-info">
            <i className="fas fa-user-circle fa profile-icon"></i>
            <div className="profile-text">
                <div className="name-container">
                    <h1>{userData.name}</h1>
                    <i className="fas fa-edit edit-name-icon" onClick={openNameModal}></i>
                </div>
                <h5>Account ID: {userData.u_id}</h5>
            </div>
        </div>


          <hr />

          <div className="info-spot">
            <h3>Email:</h3>
            <h6>{userData.email}</h6>
            <i
              className="fas fa-edit edit-icon"
              onClick={openEmailModal}
            ></i>
          </div>

          <div className="info-spot">
            <h3>Password:</h3>
            <h6>******</h6>
            <i
              className="fas fa-edit edit-icon"
              onClick={openPasswordModal}
            ></i>
          </div>
        </div>
    ) : (
        <p>No user data available</p>
    )}

    <EditNameModal
        isVisible={nameModalVisible}
        closeModal={closeNameModal}
        handleNameSubmit={handleNameSubmit}
        formData={formData}
        handleChange={handleChange}
    />

    <EditEmailModal
        isVisible={emailModalVisible}
        closeModal={closeEmailModal}
        handleEmailSubmit={handleEmailSubmit}
        formData={formData}
        handleChange={handleChange}
    />

    <EditPasswordModal
        isVisible={passwordModalVisible}
        closeModal={closePasswordModal}
        handlePasswordSubmit={handlePasswordSubmit}
        formData={formData}
        handleChange={handleChange}
        step={step}
        setStep={setStep}
        handleOldPasswordCheck={handleOldPasswordCheck}
    />

    </div>
  );
};

export default ProfilePage;
