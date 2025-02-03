import React, { useState } from "react";
import "./Login.css";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleForgotPassword = () => {
    alert("Forgot Password clicked");
  };

  const handleLoginAsTester = () => {
    alert("Logged in as Tester");
    // Logic to handle login as tester can be added here
  };

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post(
        "http://localhost:5001/login",
        {
          email: email,
          password: password,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const { access_token, first_login } = response.data;

      // Store the token in localStorage
      localStorage.setItem("token", access_token);

      // If it's a first login, explicitly create the patient
      if (first_login) {
        try {
          await axios.post(
            "http://localhost:5001/create_patient",
            {
              email: email,
              password: password,
              name: email, // Using email as name if no specific name provided
            },
            {
              headers: {
                Authorization: `Bearer ${access_token}`,
                "Content-Type": "application/json",
              },
            }
          );
        } catch (createPatientError) {
          console.error("Error creating patient:", createPatientError);
          alert("Could not complete patient registration. Please try again.");
          return;
        }
      }

      // Navigate based on login status
      switch (response.status) {
        case 200:
          // Fully registered existing user
          navigate("/dashboard");
          break;

        case 201:
        case 202:
          // First-time login or incomplete profile
          navigate("/test");
          break;

        default:
          alert("An unexpected error occurred. Please try again.");
      }
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
        // The request was made but no response received
        alert("No response from server. Please check your connection.");
      } else {
        // Something happened in setting up the request
        alert("Error setting up the login request.");
      }
      console.error("Login error:", error);
    }
  };
  return (
    <div className="login-container">
      {/* <div className="login-image">
        SUPER HEART
        <img src="https://via.placeholder.com/150" alt="Login" />
      </div> */}
      <div className="login-card">
        <div className="login-form">
          <h2>Login</h2>
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="email">Email:</label>
              <input
                type="email"
                id="email"
                name="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password:</label>
              <input
                type="password"
                id="password"
                name="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button className="login-btn" type="submit">
              Login
            </button>
          </form>
          <button className="forgot-password" onClick={handleForgotPassword}>
            Forgot Password?
          </button>
          {/* <button className="login-tester" onClick={() => navigate("/test")}>
            Login as Tester
          </button> */}
        </div>
      </div>
    </div>
  );
};

export default Login;
