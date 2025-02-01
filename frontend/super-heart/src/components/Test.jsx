import React, { useState } from "react";
import { Form, Button, Container } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";

const Test = () => {
  const [formData, setFormData] = useState({
    heartHealthRating: "",
    walked5000Steps: "",
    lipidPanel: "",
    glucoseTest: "",
    consultedCardiologist: "",
    consultedDietitian: "",
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("Form Data Submitted:", formData);
  };

  return (
    <Container className="mt-5">
      <h2 className="text-center mb-4">Heart Health Assessment</h2>
      <Form
        onSubmit={handleSubmit}
        className="p-4 border rounded shadow-sm bg-light"
      >
        {/* Heart Health Rating */}
        <Form.Group className="mb-3">
          <Form.Label>
            How would you rate your current heart health from 1 to 10?
          </Form.Label>
          <Form.Control
            type="number"
            name="heartHealthRating"
            min="1"
            max="10"
            value={formData.heartHealthRating}
            onChange={handleChange}
            required
          />
        </Form.Group>

        {/* Walked 5000 Steps */}
        <Form.Group className="mb-3">
          <Form.Label>Did you walk more than 5000 steps today?</Form.Label>
          <div>
            <Form.Check
              inline
              label="Yes"
              type="radio"
              name="walked5000Steps"
              value="Yes"
              onChange={handleChange}
              required
            />
            <Form.Check
              inline
              label="No"
              type="radio"
              name="walked5000Steps"
              value="No"
              onChange={handleChange}
            />
          </div>
        </Form.Group>

        {/* Lipid Panel */}
        <Form.Group className="mb-3">
          <Form.Label>
            Have you taken a lipid panel in the past 6 months?
          </Form.Label>
          <div>
            <Form.Check
              inline
              label="Yes"
              type="radio"
              name="lipidPanel"
              value="Yes"
              onChange={handleChange}
              required
            />
            <Form.Check
              inline
              label="No"
              type="radio"
              name="lipidPanel"
              value="No"
              onChange={handleChange}
            />
          </div>
        </Form.Group>

        {/* Glucose Test */}
        <Form.Group className="mb-3">
          <Form.Label>
            Have you taken a glucose test in the past 6 months?
          </Form.Label>
          <div>
            <Form.Check
              inline
              label="Yes"
              type="radio"
              name="glucoseTest"
              value="Yes"
              onChange={handleChange}
              required
            />
            <Form.Check
              inline
              label="No"
              type="radio"
              name="glucoseTest"
              value="No"
              onChange={handleChange}
            />
          </div>
        </Form.Group>

        {/* Cardiologist Consultation */}
        <Form.Group className="mb-3">
          <Form.Label>
            Have you consulted a cardiologist in the past 1 year?
          </Form.Label>
          <div>
            <Form.Check
              inline
              label="Yes"
              type="radio"
              name="consultedCardiologist"
              value="Yes"
              onChange={handleChange}
              required
            />
            <Form.Check
              inline
              label="No"
              type="radio"
              name="consultedCardiologist"
              value="No"
              onChange={handleChange}
            />
          </div>
        </Form.Group>

        {/* Dietitian Consultation */}
        <Form.Group className="mb-4">
          <Form.Label>
            Have you consulted a dietitian in the past 1 year?
          </Form.Label>
          <div>
            <Form.Check
              inline
              label="Yes"
              type="radio"
              name="consultedDietitian"
              value="Yes"
              onChange={handleChange}
              required
            />
            <Form.Check
              inline
              label="No"
              type="radio"
              name="consultedDietitian"
              value="No"
              onChange={handleChange}
            />
          </div>
        </Form.Group>

        {/* Submit Button */}
        <div className="text-center">
          <Button variant="secondary" type="submit">
            Submit
          </Button>
        </div>
      </Form>
    </Container>
  );
};

export default Test;
