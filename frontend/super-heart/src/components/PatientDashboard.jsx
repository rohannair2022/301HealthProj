import React, { useState, useEffect, useCallback } from "react";
import "./Dashboard.css";
import { redirect, useNavigate } from "react-router-dom";
import axios from "axios";
import FileUpload from "./FileUpload";
import AddFriendModal from "./AddFriendModal";
import StepsChart from './StepsChart';
import HeartRateChart from "./HeartRateChart";
// import SpO2Chart from "./SpO2Chart";

const PatientDashboard = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [userData, setUserData] = useState({
    heart_score: 0,
    steps: 0,
  });
  const [isHome, setHome] = useState(true);
  const [isUpload, setUpload] = useState(false);
  const [users, setUsers] = useState([]);
  const [friends, setFriends] = useState([]);
  const [error, setError] = useState("");
  const [isAddFriendModalOpen, setIsAddFriendModalOpen] = useState(false);
  const [isProgress, setProgress] = useState(false);
  const [weeklySteps, setWeeklySteps] = useState([]);
  const [weeklyHeartRate, setWeeklyHeartRate] = useState([]);
  // const [weeklySpO2, setWeeklySpO2] = useState([]);

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem("token");
      await axios.post(
        "http://localhost:5001/logout",
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      // Clear ALL storage
      localStorage.clear(); // This will remove token and any other stored data
      navigate("/");
    } catch (error) {
      console.error("Logout error:", error);
      // Even if the backend call fails, we should still clear storage and redirect
      localStorage.clear();
      navigate("/");
    }
  };

  const handleFitbitLogin = async () => {
    try {
      // First, perform login
      const token = localStorage.getItem("token");
      const codeCreation = await axios.get(
        "http://localhost:5001/connect_watch",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const client_id = codeCreation.data.client_id;
      const code_challenge = codeCreation.data.code_challenge;
      const scope =
        "activity cardio_fitness electrocardiogram irregular_rhythm_notifications heartrate profile respiratory_rate oxygen_saturation sleep social weight";

      // Redirect to Fitbit login page
      const authUrl = `https://www.fitbit.com/oauth2/authorize?response_type=code&client_id=${client_id}&scope=${scope}&code_challenge_method=S256&code_challenge=${code_challenge}`;
      window.open(authUrl, "_blank");
    } catch (error) {
      // Handle different error scenarios
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

  const fetchUserData = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");

      const response = await axios.get("http://localhost:5001/get_patient", {
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
      console.error("Error fetching user data:", error);
      if (error.response && error.response.status === 401) {
        navigate("/login");
      }
    }
    setTimeout(fetchUserData, 600000);
  }, [navigate]);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://localhost:5001/list_users", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setUsers(response.data.users);
    } catch (error) {
      console.error("Error fetching users:", error);
      setError("Failed to fetch users");
    }
  };

  const fetchFriends = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://localhost:5001/list_friends", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setFriends(response.data.friends || []);
    } catch (error) {
      console.error("Error fetching friends:", error);
      setError("Failed to fetch friends");
    }
  }, []);

  const fetchWeeklySteps = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://localhost:5001/get_weekly_steps", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setWeeklySteps(response.data.weekly_steps);
    } catch (error) {
      console.error("Error fetching weekly steps:", error);
    }
  }, []);

  const fetchHeartRateData = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://localhost:5001/get_weekly_heart_rate", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setWeeklyHeartRate(response.data.weekly_heart_rate);
    } catch (error) {
      console.error("Error fetching heart rate data:", error);
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
      const token = localStorage.getItem("token");
      await axios.post(
        "http://localhost:5001/add_friend",
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
      // Refresh friends list after adding
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
      console.error("Error removing friend:", error);
      setError(error.response?.data?.error || "Failed to remove friend");
    }
  };

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    setIsDarkMode(savedTheme === "dark");
    document.body.className = savedTheme === "dark" ? "dark-mode" : "";
    fetchUserData();
    fetchFriends();
    fetchWeeklySteps();
    fetchHeartRateData();
    // fetchSpO2Data();
  }, [fetchUserData, fetchFriends, fetchWeeklySteps, fetchHeartRateData]);

  // Theme toggle function
  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.body.className = !isDarkMode ? "dark-mode" : "";
    localStorage.setItem("theme", !isDarkMode ? "dark" : "light");
  };

  return (
    <div className="app-container">
      {/* Side Navigation */}
      <nav className="side-nav">
        <div className="logo">SuperHeart</div>
        <ul className="nav-links">
          <li
            onClick={() => {
              setUpload(false);
              setHome(true);
              setProgress(false);
            }}
          >
            <i className="fas fa-home"></i>
            Dashboard
          </li>
          <li
            onClick={() => {
              setUpload(false);
              setHome(false);
              setProgress(false);
            }}
          >
            <i className="fas fa-user-friends"></i>
            Friends
          </li>
          <li
            onClick={() => {
              setUpload(false);
              setHome(false);
              setProgress(true);
            }}
          >
            <i className="fas fa-chart-line"></i>
            Progress
          </li>
          <li
            onClick={() => {
              setUpload(true);
              setHome(false);
              setProgress(false);
            }}
          >
            <i className="fas fa-upload"></i>
            Upload Data
          </li>
          <li
            onClick={() => {
              handleFitbitLogin();
            }}
          >
            <i className="fas fa-heart"></i>
            Connect Fitbit
          </li>
          <li onClick={toggleTheme} className="theme-toggle">
            <i className={`fas ${isDarkMode ? "fa-sun" : "fa-moon"}`}></i>
            {isDarkMode ? "Light Mode" : "Dark Mode"}
          </li>
          <li onClick={handleLogout} className="logout-btn">
            <i className="fas fa-sign-out-alt"></i>
            Logout
          </li>
        </ul>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {isUpload ? (
          <div>
            <FileUpload />
          </div>
        ) : isHome ? (
          <>
            <header className="top-header">
              <div className="header-search">
                <i className="fas fa-search"></i>
                <input type="text" placeholder="Search..." />
              </div>
              <div className="header-right">
                <i className="fas fa-bell"></i>
                <i className="fas fa-user-circle"></i>
              </div>
            </header>

            {/* Dashboard Content */}
            <div className="dashboard-content">
              <div className="dashboard-header">
                <h2>Health Overview</h2>
              </div>

              <div className="dashboard-grid">
                <div className="dashboard-card">
                  <h3>Heart Health Score</h3>
                  <div className="score">{userData?.heart_score || "N/A"}</div>
                  <p>Out of 100</p>
                </div>

                <div className="dashboard-card">
                  <h3>Daily Steps</h3>
                  <div className="score">{userData?.steps || 0}</div>
                  <div className="steps-progress">
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${((userData?.steps || 0) / 10000) * 100}%`,
                        }}
                      ></div>
                    </div>
                    <p>Target: 10,000 steps</p>
                  </div>
                </div>

                <div className="dashboard-card">
                  <h3>Height</h3>
                  <div className="measurement">{userData?.height || "N/A"}</div>
                  <p>Current Height</p>
                </div>

                <div className="dashboard-card">
                  <h3>Weight</h3>
                  <div className="measurement">{userData?.weight || "N/A"}</div>
                  <p>Current Weight</p>
                </div>
              </div>

              {/* Friends Section */}
              <div className="friends-section">
                <div className="section-header">
                  <h3>Friends</h3>
                  <button
                    className="add-friend-btn"
                    onClick={() => setIsAddFriendModalOpen(true)}
                  >
                    <i className="fas fa-plus"></i> Add Friend
                  </button>
                </div>
                <div className="search-bar">
                  <i className="fas fa-search"></i>
                  <input
                    type="text"
                    placeholder="Search friends..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                {error && <div className="error-message">{error}</div>}
                <div className="friends-list">
                  {friends.length > 0 ? (
                    friends
                      .filter((friend) =>
                        friend.name
                          .toLowerCase()
                          .includes(searchTerm.toLowerCase())
                      )
                      .map((friend) => (
                        <div key={friend.u_id} className="friend-item">
                          <div className="friend-info">
                            <i className="fas fa-user-circle"></i>
                            <span className="friend-name">{friend.name}</span>
                            <span className={`friend-type ${friend.type}`}>
                              {friend.type.toUpperCase()}
                            </span>
                          </div>
                          <div className="friend-actions">
                            <span className="friend-score">
                              {friend.type === "patient"
                                ? `Score: ${friend.heart_score}`
                                : friend.specialty}
                            </span>
                            <button
                              className="remove-friend-btn"
                              onClick={() =>
                                handleRemoveFriend(friend.u_id, friend.type)
                              }
                              title="Remove friend"
                            >
                              <i className="fas fa-times"></i>
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
              isOpen={isAddFriendModalOpen}
              onClose={() => setIsAddFriendModalOpen(false)}
              onAddFriend={handleAddFriend}
            />
          </>
        ) : isProgress ? ( // Progress Section
          <div className="dashboard-content">
            {/* Horizontal Layout for Steps and Heart Rate Charts */}
            <div className="horizontal-charts-container">
              {/* Steps Chart */}
              <div className="horizontal-chart">
                <StepsChart data={weeklySteps} />
              </div>

              {/* Heart Rate Chart */}
              <div className="horizontal-chart">
                <HeartRateChart data={weeklyHeartRate} />
              </div>
            </div>

            {/* Weekly Summary Below */}
            <div className="stats-summary">
              <h3>Weekly Summary</h3>
              <div className="stats-grid">
                {/* Steps Statistics */}
                <div className="stat-item">
                  <span>Total Steps</span>
                  <strong>{weeklySteps.reduce((sum, day) => sum + (day.steps || 0), 0)}</strong>
                </div>
                <div className="stat-item">
                  <span>Avg Daily Steps</span>
                  <strong>{Math.round(weeklySteps.reduce((sum, day) => sum + (day.steps || 0), 0) / 7)}</strong>
                </div>

                {/* Heart Rate Statistics */}
                <div className="stat-item">
                  <span>Avg Heart Rate</span>
                  <strong>
                    {weeklyHeartRate.length > 0 
                      ? Math.round(weeklyHeartRate.reduce((sum, day) => sum + (day.heart_rate || 0), 0) / 7)
                      : 'N/A'}
                  </strong>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
};

export default PatientDashboard;
