import React, { useState, useEffect } from "react";
import "./Dashboard.css";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import AddFriendModal from "./AddFriendModal";
import { Modal, Button, Form } from "react-bootstrap";

const DoctorDashboard = () => {
  const navigate = useNavigate();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [doctorData, setDoctorData] = useState({
    name: "",
    specialty: "",
    email: "",
    password: "",
    u_id: null,
  });
  const [isAddFriendModalOpen, setIsAddFriendModalOpen] = useState(false);
  const [friends, setFriends] = useState([]);
  const [patientFiles, setPatientFiles] = useState({}); // Map patient id -> files array
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  // States for updating health score
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [newHealthScore, setNewHealthScore] = useState("");

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem("token");
      await axios.post(
        "http://localhost:5001/logout",
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      localStorage.removeItem("token");
      navigate("/");
    } catch (error) {
      console.error("Logout error:", error);
      localStorage.removeItem("token");
      navigate("/");
    }
  };

  const fetchDoctorData = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://localhost:5001/get_doctor", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.data) setDoctorData(response.data.doctor);
    } catch (error) {
      console.error("Error fetching doctor data:", error);
      if (error.response?.status === 401) navigate("/login");
    }
  };

  // Fetch friends (patients) and then their files
  const fetchFriends = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://localhost:5001/list_friends", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const friendsData = response.data.friends || [];
      setFriends(friendsData);
      updatePatientFiles(friendsData);
    } catch (error) {
      console.error("Error fetching friends:", error);
      setError("Failed to fetch friends");
    }
  };

  // Fetch files for a single patient
  const fetchPatientFiles = async (patientId) => {
    try {
      const token = localStorage.getItem("token");
      // Assumes a new endpoint for doctor to view patient's files exists:
      const response = await axios.get(
        `http://localhost:5001/doctor/files/${patientId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      return response.data.files || [];
    } catch (error) {
      console.error("Error fetching files for patient", patientId, error);
      return [];
    }
  };

  // Update the patientFiles mapping for each patient
  const updatePatientFiles = async (friendsList) => {
    const newPatientFiles = {};
    await Promise.all(
      friendsList.map(async (friend) => {
        if (friend.type === "patient") {
          const files = await fetchPatientFiles(friend.u_id);
          newPatientFiles[friend.u_id] = files;
        }
      })
    );
    setPatientFiles(newPatientFiles);
  };

  const handleFitbitLogin = async () => {
    try {
      const token = localStorage.getItem("token");
      const codeCreation = await axios.get(
        "http://localhost:5001/connect_watch",
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const { client_id, code_challenge } = codeCreation.data;
      const scope =
        "activity cardio_fitness electrocardiogram irregular_rhythm_notifications heartrate profile respiratory_rate oxygen_saturation sleep social weight";
      const authUrl = `https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=${client_id}&scope=${scope}&code_challenge_method=S256&code_challenge=${code_challenge}`;
      window.open(authUrl, "_blank");
    } catch (error) {
      if (error.response) {
        switch (error.response.status) {
          case 400:
            alert("Please provide both email and password.");
            break;
          case 401:
            alert("Invalid credentials. Please try again.");
            break;
          default:
            alert("An error occurred. Please try again.");
        }
      } else if (error.request) {
        alert("No response from server. Please check your connection.");
      } else {
        alert("Error setting up the login request.");
      }
      console.error("Login error:", error);
    }
  };

  const handleAddFriend = async (friendId, friendType) => {
    try {
      const token = localStorage.getItem("token");
      await axios.post(
        "http://localhost:5001/add_friend",
        { friend_id: friendId, friend_type: friendType },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchFriends();
    } catch (error) {
      console.error("Error adding friend:", error);
      setError(error.response?.data?.error || "Failed to add friend");
    }
  };

  const handleRemoveFriend = async (friendId, friendType) => {
    try {
      const token = localStorage.getItem("token");
      await axios.delete("http://localhost:5001/remove_friend", {
        headers: { Authorization: `Bearer ${token}` },
        data: { friend_id: friendId, friend_type: "patient" },
      });
      fetchFriends();
    } catch (error) {
      console.error("Error removing friend:", error);
      setError(error.response?.data?.error || "Failed to remove friend");
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
      const token = localStorage.getItem("token");
      await axios.put(
        "http://localhost:5001/doctor/update_health_score",
        { health_score: newHealthScore, patient_id: selectedPatient.u_id },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert("Health score updated successfully!");
      setShowUpdateModal(false);
      fetchFriends();
    } catch (error) {
      console.error("Error updating health score:", error);
      alert("Failed to update health score");
    }
  };

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    setIsDarkMode(savedTheme === "dark");
    document.body.className = savedTheme === "dark" ? "dark-mode" : "";
    fetchDoctorData();
    fetchFriends();
  }, []);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.body.className = !isDarkMode ? "dark-mode" : "";
    localStorage.setItem("theme", !isDarkMode ? "dark" : "light");
  };

  const goToProfile = () => {
    navigate("/doctor-profile", { state: { doctorData } });
  };

  return (
    <div className="app-container">
      <nav className="side-nav">
        <div className="logo">SuperHeart</div>
        <ul className="nav-links">
          <li>
            <i className="fas fa-home"></i> Dashboard
          </li>
          <li>
            <i className="fas fa-user-friends"></i> My Patients
          </li>
          <li onClick={toggleTheme} className="theme-toggle">
            <i className={`fas ${isDarkMode ? "fa-sun" : "fa-moon"}`}></i>
            {isDarkMode ? "Light Mode" : "Dark Mode"}
          </li>
          <li onClick={handleFitbitLogin}>
            <i className="fas fa-heart"></i> Connect Fitbit
          </li>
          <li onClick={handleLogout} className="logout-btn">
            <i className="fas fa-sign-out-alt"></i> Logout
          </li>
        </ul>
      </nav>

      <main className="main-content">
        <header className="top-header">
          <div className="header-right">
            <i className="fas fa-bell"></i>
            <i
              className="fas fa-user-circle"
              onClick={goToProfile}
              style={{ cursor: "pointer" }}
            ></i>
          </div>
        </header>

        <div className="dashboard-content">
          <div className="dashboard-header">
            <h2>Welcome, Dr. {doctorData.name}</h2>
            <p>Specialty: {doctorData.specialty}</p>
          </div>

          <div className="friends-section">
            <div className="section-header">
              <h3>My Patients</h3>
              <button
                className="add-friend-btn"
                onClick={() => setIsAddFriendModalOpen(true)}
              >
                <i className="fas fa-plus"></i> Add Patient
              </button>
            </div>
            <div className="search-bar">
              <i className="fas fa-search"></i>
              <input
                type="text"
                placeholder="Search patients..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <div className="friends-list">
              {friends.length > 0 ? (
                friends
                  .filter((friend) =>
                    friend.name.toLowerCase().includes(searchTerm.toLowerCase())
                  )
                  .map((friend) => (
                    <div key={friend.u_id} className="friend-item">
                      <div className="friend-info">
                        <i className="fas fa-user-circle"></i>
                        <span className="friend-name">{friend.name}</span>
                        <span className="friend-type patient">PATIENT</span>
                      </div>
                      <div className="friend-actions">
                        <span className="friend-score">
                          Score: {friend.heart_score}
                        </span>
                        <button
                          className="update-score-btn"
                          onClick={() => handleOpenUpdateModal(friend)}
                          title="Update Health Score"
                        >
                          <i className="fas fa-edit"></i>
                        </button>
                        <button
                          className="remove-friend-btn"
                          onClick={() =>
                            handleRemoveFriend(friend.u_id, "patient")
                          }
                          title="Remove patient"
                        >
                          <i className="fas fa-times"></i>
                        </button>
                      </div>
                      {/* Display patient's uploaded files */}
                      {patientFiles[friend.u_id] &&
                        patientFiles[friend.u_id].length > 0 && (
                          <div className="patient-files">
                            <strong>Files:</strong>
                            <ul>
                              {patientFiles[friend.u_id].map((file, idx) => (
                                <li key={idx}>
                                  <a
                                    href={`http://localhost:5001/doctor/files/${friend.u_id}/${file}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
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

        <AddFriendModal
          isOpen={isAddFriendModalOpen}
          onClose={() => setIsAddFriendModalOpen(false)}
          onAddFriend={handleAddFriend}
        />

        {/* Modal for updating health score */}
        <Modal show={showUpdateModal} onHide={handleCloseUpdateModal}>
          <Modal.Header closeButton>
            <Modal.Title>Update Health Score</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group>
              <Form.Label>New Health Score</Form.Label>
              <Form.Control
                type="number"
                value={newHealthScore}
                onChange={(e) => setNewHealthScore(e.target.value)}
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCloseUpdateModal}>
              Close
            </Button>
            <Button variant="primary" onClick={handleUpdateHealthScore}>
              Save Changes
            </Button>
          </Modal.Footer>
        </Modal>
      </main>
    </div>
  );
};

export default DoctorDashboard;
