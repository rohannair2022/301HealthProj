import React, { useState, useEffect, useCallback } from 'react';
import './Dashboard.css';
import axios from 'axios';

const FileUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  useEffect(() => {
    fetchUploadedFiles();
  }, []);

  const fetchUploadedFiles = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get("http://localhost:5001/files", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUploadedFiles(response.data.files);
    } catch (error) {
      console.error("Error fetching files:", error);
    }
  };

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      alert("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const token = localStorage.getItem("token");
      await axios.post("http://localhost:5001/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${token}`,
        },
      });

      alert("File uploaded successfully!");
      setSelectedFile(null);
      fetchUploadedFiles();
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("File upload failed.");
    }
  };

  const handleFileClick = async (filename) => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`http://localhost:5001/files/${filename}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      link.setAttribute('target', '_blank');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error downloading file:", error);
      alert("Error accessing file");
    }
  };

  const handleDeleteFile = async (filename) => {
    if (window.confirm(`Are you sure you want to delete ${filename}?`)) {
      try {
        const token = localStorage.getItem("token");
        await axios.delete(`http://localhost:5001/files/${filename}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        alert("File deleted successfully!");
        fetchUploadedFiles(); // Refresh the file list
      } catch (error) {
        console.error("Error deleting file:", error);
        alert("Error deleting file");
      }
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-content">
        <div className='section-header'>
          <h3>Upload a File</h3>
        </div>
        <div className="upload-controls">
          <input type="file" onChange={handleFileChange} className="file-input" />
          <button onClick={handleUpload} className="add-friend-btn">Upload File</button>
        </div>
        <div className='section-header'>
          <h5>Your Uploaded Files</h5>
        </div>
        <div className='files-list'>
          {uploadedFiles.length > 0 ? (
            <ul>
              {uploadedFiles.map((file, index) => (
                <li key={index} className="file-item">
                  <div className="file-item-content">
                    <button 
                      onClick={() => handleFileClick(file)}
                      className="file-link"
                    >
                      <i className="fas fa-file"></i> {file}
                    </button>
                    <button 
                      onClick={() => handleDeleteFile(file)}
                      className="delete-btn"
                      title="Delete file"
                    >
                      <i className="fas fa-trash"></i>
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p>No files uploaded yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileUpload;