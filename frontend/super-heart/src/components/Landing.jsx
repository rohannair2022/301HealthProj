import React from "react";
import { useNavigate } from "react-router-dom";
import Button from "react-bootstrap/Button";
import "bootstrap/dist/css/bootstrap.min.css";

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="text-center">
        <h2 className="text-4xl font-extrabold">SuperHeart</h2>
        <p className="text-lg  mt-3 mb-8 font-medium">
          Your Personal Health Companion
        </p>

        {/* Button */}
        <Button variant="outline-light" onClick={() => navigate("/login")}>
          Login
        </Button>
      </div>
    </div>
  );
};

export default Landing;
