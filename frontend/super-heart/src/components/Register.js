import React, { useState } from "react";
import "./Register.css";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: "",
    name: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleRegister = async (type) => {
    setError("");

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // Validate password strength
    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters long");
      return;
    }

    try {
      const response = await axios.post(
        `http://localhost:5001/register/${type}`,
        {
          email: formData.email,
          name: formData.name,
          password: formData.password,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (response.status === 201) {
        // Registration successful, redirect to login
        navigate("/login");
      }
    } catch (error) {
      if (error.response) {
        switch (error.response.status) {
          case 400:
            setError("Please fill in all fields correctly");
            break;
          case 409:
            setError("Email already registered");
            break;
          default:
            setError("An error occurred during registration");
        }
      } else {
        setError("Unable to connect to server");
      }
      console.error("Registration error:", error);
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <div className="register-form">
          <h2>Create Account</h2>
          {error && <div className="error-message">{error}</div>}
          <form onSubmit={(e) => e.preventDefault()}>
            <div className="form-group">
              <label htmlFor="email">Email:</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="name">Full Name:</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password:</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password:</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
              />
            </div>
            <button
              className="register-btn patient-btn"
              onClick={() => handleRegister('patient')}
            >
              Register as Patient
            </button>
            <button
              className="register-btn doctor-btn"
              onClick={() => handleRegister('doctor')}
            >
              Register as Doctor
            </button>
          </form>
          <button className="login-link" onClick={() => navigate("/login")}>
            Already have an account? Login
          </button>
        </div>
      </div>
    </div>
  );
};

export default Register;