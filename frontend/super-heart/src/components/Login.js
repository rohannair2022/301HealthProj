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
    alert("Login clicked");
    // Logic to handle login can be added here
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:5001/login', { 'email' : email, 'password' : password }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const { access_token } = response.data['access_token'];
      localStorage.setItem('token', access_token); // Store the token in localStorage
      if (response.status === 200) {
        navigate("/dashboard"); 
      } else if (response.status === 401) {
        alert("Invalid credentials. Please try again.");
      } else if (response.status === 202 && response.data['first-login'] === true) {
        await axios.post('http://localhost:5001/create_patient', { 'email': email, 'password': password }, { headers: { 'Authorization': `Bearer ${access_token}`, 'Content-Type': 'application/json'} });
        navigate("/test");
      } else if (response.status === 202) {
        navigate("/test");
      } else {
        alert("An error occurred. Please try again.");
      }
      console.log('Login successful');
    } catch (error) {
      console.error('There was an error logging in!', error);
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
