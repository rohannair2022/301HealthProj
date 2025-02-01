import React from "react";
import "./Login.css";
import { useNavigate } from "react-router-dom";

const Login = () => {
  const navigate = useNavigate();
  const handleForgotPassword = () => {
    alert("Forgot Password clicked");
  };

  const handleLoginAsTester = () => {
    alert("Logged in as Tester");
    // Logic to handle login as tester can be added here
  };

  const handleLogin = (e) => {
    e.preventDefault();
    alert("Login clicked");
    // Logic to handle login can be added here
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
          <form>
            <div className="form-group">
              <label htmlFor="email">Email:</label>
              <input type="email" id="email" name="email" required />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password:</label>
              <input type="password" id="password" name="password" required />
            </div>
            <button className="login-btn" type="submit" onClick={handleLogin}>
              Login
            </button>
          </form>
          <button className="forgot-password" onClick={handleForgotPassword}>
            Forgot Password?
          </button>
          <button className="login-tester" onClick={() => navigate("/test")}>
            Login as Tester
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
