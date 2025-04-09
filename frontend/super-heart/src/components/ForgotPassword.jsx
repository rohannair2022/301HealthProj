import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import "./Login.css"; // Reusing login styling
import logo from '../logo.png'; // Import the logo

const ForgotPassword = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [isError, setIsError] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resetToken, setResetToken] = useState("");

  const handleRequestReset = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setMessage("");
    setIsError(false);

    try {
      const response = await axios.post("http://localhost:5001/request_password_reset", {
        email: email
      });
      
      setMessage("Reset code has been sent. Please check your email.");
      setResetSent(true);
      setIsError(false);
    } catch (error) {
      setIsError(true);
      setMessage(error.response?.data?.message || "Failed to generate reset code. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      setIsError(true);
      setMessage("Passwords do not match");
      return;
    }

    setIsSubmitting(true);
    
    try {
      const response = await axios.post("http://localhost:5001/reset_password", {
        email: email,
        reset_token: resetToken,
        new_password: newPassword
      });
      
      setMessage("Password successfully reset! Redirecting to login...");
      setIsError(false);
      
      // Redirect to login page after 3 seconds
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    } catch (error) {
      setIsError(true);
      setMessage(error.response?.data?.message || "Failed to reset password. Please check your reset code and try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-form">
          <img 
            src={logo} 
            alt="SuperHeart Logo" 
            className="logo-image" 
            style={{ maxWidth: '150px', margin: '0 auto 20px', display: 'block' }} 
          />
          <h2>{resetSent ? "Reset Your Password" : "Forgot Password"}</h2>
          
          {message && (
            <div className={`message ${isError ? "error-message" : "success-message"}`}>
              {message}
            </div>
          )}
          
          {!resetSent ? (
            <>
              <p className="instruction-text">
                Enter your email address below and we'll send you a code to reset your password.
              </p>
              <form onSubmit={handleRequestReset}>
                <div className="form-group">
                  <label htmlFor="email">Email:</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="Enter your email"
                  />
                </div>
                
                <button 
                  type="submit" 
                  className="login-btn"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Sending..." : "Send Reset Code"}
                </button>
                
                <button className="register-link" onClick={() => navigate("/login")}>
                  Remember your password? Log in
                </button>
              </form>
            </>
          ) : (
            <>
              <p className="instruction-text">
                Enter the reset code and your new password below.
              </p>
              <form onSubmit={handleResetPassword}>
                <div className="form-group">
                  <label htmlFor="resetToken">Reset Code:</label>
                  <input
                    type="text"
                    id="resetToken"
                    name="resetToken"
                    value={resetToken}
                    onChange={(e) => setResetToken(e.target.value)}
                    required
                    placeholder="Enter reset code"
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="newPassword">New Password:</label>
                  <input
                    type="password"
                    id="newPassword"
                    name="newPassword"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    placeholder="Enter new password"
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="confirmPassword">Confirm Password:</label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    placeholder="Confirm new password"
                  />
                </div>
                
                <button 
                  type="submit" 
                  className="login-btn"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Resetting..." : "Reset Password"}
                </button>
                
                <button className="register-link" onClick={() => navigate("/login")}>
                  Back to Login
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;