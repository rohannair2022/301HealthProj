import React, { useEffect } from 'react';
import { Tabs, Tab } from 'react-bootstrap';
import axios from 'axios';
import './Dashboard.css';

const FriendRequestsModal = ({
  show,
  onHide,
  incomingRequests,
  outgoingRequests,
  handleAcceptRequest,
  handleRejectRequest,
  onRequestUpdated,
  isDoctor = false, // Add this prop to detect if we're on the doctor dashboard
}) => {
  // Handle cancelling an outgoing request
  const handleCancelRequest = async (requestId) => {
    try {
      const token = localStorage.getItem('token');

      // Use the reject_friend_request endpoint for cancellation
      await axios.post(
        `/reject_friend_request/${requestId}`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      // Update the UI by calling the callback function
      if (onRequestUpdated) {
        onRequestUpdated();
      }
    } catch (error) {
      console.error('Error canceling friend request:', error);
    }
  };

  // Prevent body scrolling when modal is open
  useEffect(() => {
    if (show) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }

    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [show]);

  if (!show) return null;

  // Enhanced tab title rendering
  const renderTabTitle = (title, count) => (
    <span>
      {title} ({count})
    </span>
  );

  return (
    <div
      className='custom-modal-overlay'
      onClick={(e) => {
        if (e.target.className === 'custom-modal-overlay') onHide();
      }}
    >
      <div className='custom-modal'>
        <div className='custom-modal-header'>
          <h5 className='custom-modal-title'>Friend Requests</h5>
          <button className='custom-close-button' onClick={onHide}>
            ×
          </button>
        </div>
        <div className='custom-modal-body'>
          <Tabs
            defaultActiveKey='incoming'
            id='requests-tabs'
            className='w-100'
          >
            <Tab
              eventKey='incoming'
              title={renderTabTitle('Incoming', incomingRequests.length)}
            >
              <div className='request-container'>
                {incomingRequests.length > 0 ? (
                  incomingRequests.map((request) => (
                    <div key={request.request_id} className='request-item'>
                      <div className='request-info'>
                        <i className='fas fa-user-circle'></i>
                        <div className='request-details'>
                          <div className='request-name'>{request.name}</div>
                          <div className='request-type'>
                            {request.type.toUpperCase()}
                          </div>
                        </div>
                      </div>

                      {isDoctor ? (
                        // Doctor view with simple icons
                        <div className='request-actions doctor-actions'>
                          <button
                            className='accept-icon-btn'
                            onClick={() =>
                              handleAcceptRequest(request.request_id)
                            }
                            title='Accept Request'
                          >
                            <i className='fas fa-check'></i>
                          </button>
                          <button
                            className='reject-icon-btn'
                            onClick={() =>
                              handleRejectRequest(request.request_id)
                            }
                            title='Reject Request'
                          >
                            <i className='fas fa-times'></i>
                          </button>
                        </div>
                      ) : (
                        // Patient view with styled buttons
                        <div className='request-actions'>
                          <button
                            className='accept-btn'
                            onClick={() =>
                              handleAcceptRequest(request.request_id)
                            }
                            title='Accept Request'
                          >
                            <i className='fas fa-check'></i>
                          </button>
                          <button
                            className='reject-btn'
                            onClick={() =>
                              handleRejectRequest(request.request_id)
                            }
                            title='Reject Request'
                          >
                            <i className='fas fa-times'></i>
                          </button>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className='no-requests-message'>
                    <i className='fas fa-inbox'></i>
                    <p>No incoming requests</p>
                    <span className='message-hint'>
                      When someone adds you as a friend, their request will
                      appear here
                    </span>
                  </div>
                )}
              </div>
            </Tab>
            <Tab
              eventKey='outgoing'
              title={renderTabTitle('Outgoing', outgoingRequests.length)}
            >
              <div className='request-container'>
                {outgoingRequests.length > 0 ? (
                  outgoingRequests.map((request) => (
                    <div key={request.request_id} className='request-item'>
                      <div className='request-info'>
                        <i className='fas fa-user-circle'></i>
                        <div className='request-details'>
                          <div className='request-name'>{request.name}</div>
                          <div className='request-type'>
                            {request.type.toUpperCase()}
                          </div>
                        </div>
                      </div>

                      <div className='request-actions'>
                        <span className='pending-status'>PENDING</span>
                        <button
                          className={
                            isDoctor ? 'cancel-icon-btn' : 'cancel-btn'
                          }
                          onClick={() =>
                            handleCancelRequest(request.request_id)
                          }
                          title='Cancel Request'
                        >
                          <i className='fas fa-times'></i>
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className='no-requests-message'>
                    <i className='fas fa-paper-plane'></i>
                    <p>No outgoing requests</p>
                    <span className='message-hint'>
                      Friend requests you've sent will appear here until they're
                      accepted
                    </span>
                  </div>
                )}
              </div>
            </Tab>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default FriendRequestsModal;
