import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Modal Component for Follow-up Questions
const FollowupModal = ({ isOpen, onClose, onComplete, questions, sessionId, userId }) => {
  const [answers, setAnswers] = useState(['', '', '']);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAnswerChange = (value) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestionIndex] = value;
    setAnswers(newAnswers);
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleSubmit = async () => {
    if (answers.some(answer => !answer.trim())) {
      alert('Please answer all questions before submitting.');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/followup/${sessionId}/complete`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          answers: answers
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        onComplete(data);
        onClose();
      } else {
        alert(data.message || 'Failed to submit follow-up answers');
      }
    } catch (error) {
      console.error('Error submitting follow-up:', error);
      alert('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>AI Follow-up Questions</h2>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <p className="progress-text">Question {currentQuestionIndex + 1} of {questions.length}</p>
        </div>

        <div className="question-container">
          <h3>{questions[currentQuestionIndex]}</h3>
          <textarea
            value={answers[currentQuestionIndex]}
            onChange={(e) => handleAnswerChange(e.target.value)}
            placeholder="Type your answer here..."
            rows="6"
            className="question-textarea"
          />
        </div>

        <div className="modal-buttons">
          <button 
            onClick={handlePrevious} 
            disabled={currentQuestionIndex === 0}
            className="btn-secondary"
          >
            Previous
          </button>
          
          {currentQuestionIndex < questions.length - 1 ? (
            <button 
              onClick={handleNext}
              disabled={!answers[currentQuestionIndex].trim()}
              className="btn-primary"
            >
              Next
            </button>
          ) : (
            <button 
              onClick={handleSubmit}
              disabled={!answers[currentQuestionIndex].trim() || isSubmitting}
              className="btn-primary"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Answers'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Weekly Report Modal Component
const WeeklyReportModal = ({ isOpen, onClose, userId }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');

  // Set default dates to last 7 days
  useEffect(() => {
    if (isOpen) {
      const today = new Date();
      const lastWeek = new Date(today);
      lastWeek.setDate(today.getDate() - 7);
      
      setEndDate(today.toISOString().split('T')[0]);
      setStartDate(lastWeek.toISOString().split('T')[0]);
      setReport(null);
      setError('');
    }
  }, [isOpen]);

  const handleGenerateReport = async () => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setError('Start date must be before end date');
      return;
    }

    setIsGenerating(true);
    setError('');
    setReport(null);

    try {
      const requestBody = {
        user_id: userId.toString() // Ensure user_id is string format
      };

      // Always include dates for better data matching
      if (startDate && endDate) {
        requestBody.start_date = startDate;
        requestBody.end_date = endDate;
      }

      console.log('Weekly report request:', requestBody); // Debug log

      const response = await fetch(`${API_BASE_URL}/reports/weekly`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      console.log('Weekly report response:', data); // Debug log

      if (data.success) {
        setReport(data);
      } else {
        setError(data.message || 'Failed to generate weekly report. Make sure you have work updates in the selected date range.');
      }
    } catch (error) {
      console.error('Error generating weekly report:', error);
      setError('Network error. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content weekly-report-modal">
        <div className="modal-header">
          <h2>Weekly Report Generator</h2>
          <p>Generate AI-powered weekly performance summary</p>
        </div>

        <div className="report-form-container">
          <div className="date-inputs">
            <div className="form-group">
              <label htmlFor="startDate">Start Date:</label>
              <input
                type="date"
                id="startDate"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                max={endDate || new Date().toISOString().split('T')[0]}
              />
            </div>
            <div className="form-group">
              <label htmlFor="endDate">End Date:</label>
              <input
                type="date"
                id="endDate"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                max={new Date().toISOString().split('T')[0]}
              />
            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="report-buttons">
            <button
              onClick={handleGenerateReport}
              disabled={isGenerating}
              className="btn-primary generate-btn"
            >
              {isGenerating ? 'Generating Report...' : 'Generate Weekly Report'}
            </button>
            <button onClick={onClose} className="btn-secondary">
              Close
            </button>
          </div>

          {report && (
            <div className="report-content">
              <div className="report-header">
                <h3>Weekly Report</h3>
                <p className="date-range">
                  {formatDate(report.metadata.date_range.start)} - {formatDate(report.metadata.date_range.end)}
                </p>
                <p className="user-info">User ID: {report.user_id}</p>
              </div>
              
              <div className="report-text">
                <div className="report-section">
                  <pre className="report-body">{report.report}</pre>
                </div>
              </div>

              {report.metadata.data_summary && (
                <div className="report-summary">
                  <h4>Data Summary</h4>
                  <div className="summary-grid">
                    <div className="summary-item">
                      <span className="label">Total Days:</span>
                      <span className="value">{report.metadata.data_summary.total_days || 0}</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Work Days:</span>
                      <span className="value">{report.metadata.data_summary.work_days || 0}</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Leave Days:</span>
                      <span className="value">{report.metadata.data_summary.leave_days || 0}</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Work Updates:</span>
                      <span className="value">{report.metadata.data_summary.work_updates_count || 0}</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Sessions:</span>
                      <span className="value">{report.metadata.data_summary.followup_sessions_count || 0}</span>
                    </div>
                    {report.metadata.data_summary.avg_quality_score && (
                      <div className="summary-item">
                        <span className="label">Avg Quality Score:</span>
                        <span className="value">{report.metadata.data_summary.avg_quality_score.toFixed(1)}/10</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="report-footer">
                <small>Generated on {new Date(report.metadata.generated_at).toLocaleString()}</small>
                {report.metadata.data_summary && (
                  <div className="debug-info">
                    <small>Debug: Found {report.metadata.data_summary.work_updates_count || 0} work updates and {report.metadata.data_summary.followup_sessions_count || 0} sessions in database</small>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [activeTab, setActiveTab] = useState('logbook');
  const [formData, setFormData] = useState({
    user_id: '',
    status: 'working',
    stack: '',
    task: '',
    progress: '',
    blockers: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showFollowup, setShowFollowup] = useState(false);
  const [showWeeklyReport, setShowWeeklyReport] = useState(false);
  const [followupData, setFollowupData] = useState(null);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success', 'error', 'info'

  const stackOptions = [
    'Frontend Development',
    'Backend Development',
    'Full Stack Development',
    'Mobile Development',
    'DevOps',
    'Data Science',
    'UI/UX Design',
    'Quality Assurance',
    'Other'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'status' && value === 'leave') {
      // Clear task-related fields when switching to leave
      setFormData(prev => ({
        ...prev,
        [name]: value,
        stack: '',
        task: '',
        progress: '',
        blockers: ''
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleSubmit = async () => {
    if (!formData.user_id.trim()) {
      setMessage('User ID is required');
      setMessageType('error');
      return;
    }

    // Only validate task when not on leave
    if ((formData.status === 'working' || formData.status === 'wfh') && !formData.task.trim()) {
      setMessage('Task description is required when working');
      setMessageType('error');
      return;
    }

    // Only validate stack when not on leave
    if (formData.status !== 'leave' && !formData.stack.trim()) {
      setMessage('Please select your task stack');
      setMessageType('error');
      return;
    }

    setIsSubmitting(true);
    setMessage('');

    try {
      // Prepare submission data with proper date fields for backend compatibility
      const submissionData = {
        ...formData,
        date: new Date().toISOString().split('T')[0], // Add date field in YYYY-MM-DD format
        update_date: new Date().toISOString().split('T')[0], // Backup date field
        submittedAt: new Date().toISOString() // Add timestamp for proper sorting
      };

      const response = await fetch(`${API_BASE_URL}/work-updates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submissionData),
      });

      const data = await response.json();

      if (data.success) {
        if (data.redirectToFollowup) {
          // Start follow-up session
          await startFollowupSession(data);
        } else {
          setMessage(data.message);
          setMessageType('success');
          // Reset form after successful submission
          setFormData({
            user_id: formData.user_id, // Keep user_id
            status: 'working',
            stack: '',
            task: '',
            progress: '',
            blockers: ''
          });
        }
      } else {
        setMessage(data.message || 'Submission failed');
        setMessageType('error');
      }
    } catch (error) {
      console.error('Error submitting work update:', error);
      setMessage('Network error. Please try again.');
      setMessageType('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const startFollowupSession = async (workUpdateData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/followups/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: formData.user_id
        }),
      });

      const data = await response.json();

      if (data.success) {
        setFollowupData(data);
        setShowFollowup(true);
        setMessage(`Quality Score: ${workUpdateData.qualityScore}/10. Please complete follow-up questions.`);
        setMessageType('info');
      } else {
        setMessage(data.message || 'Failed to start follow-up session');
        setMessageType('error');
      }
    } catch (error) {
      console.error('Error starting follow-up:', error);
      setMessage('Failed to start follow-up session');
      setMessageType('error');
    }
  };

  const handleFollowupComplete = (data) => {
    setMessage(`Follow-up completed successfully! Your work update has been saved to the LogBook system.`);
    setMessageType('success');
    setFollowupData(null);
    
    // Reset form
    setFormData({
      user_id: formData.user_id, // Keep user_id
      status: 'working',
      stack: '',
      task: '',
      progress: '',
      blockers: ''
    });
  };

  const handleGenerateWeeklyReport = () => {
    if (!formData.user_id.trim()) {
      setMessage('Please enter your User ID first');
      setMessageType('error');
      return;
    }
    setShowWeeklyReport(true);
  };

  return (
    <>
      <style>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
            'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
            sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
        }

        .app {
          min-height: 100vh;
          padding: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .container {
          background: white;
          border-radius: 20px;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
          max-width: 800px;
          width: 100%;
          overflow: hidden;
        }

        .header {
          background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
          color: white;
          padding: 30px;
          display: flex;
          align-items: center;
          gap: 20px;
        }

        .header-icon {
          font-size: 3rem;
          background: rgba(255, 255, 255, 0.2);
          padding: 15px;
          border-radius: 15px;
          backdrop-filter: blur(10px);
        }

        .header h1 {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 5px;
        }

        .header p {
          opacity: 0.9;
          font-size: 1rem;
        }

        .tab-navigation {
          background: #f8fafc;
          border-bottom: 1px solid #e2e8f0;
          display: flex;
        }

        .tab-button {
          flex: 1;
          padding: 15px 20px;
          background: none;
          border: none;
          font-size: 1rem;
          font-weight: 600;
          color: #64748b;
          cursor: pointer;
          transition: all 0.2s ease;
          border-bottom: 3px solid transparent;
        }

        .tab-button.active {
          color: #1e40af;
          border-bottom-color: #3b82f6;
          background: white;
        }

        .tab-button:hover {
          background: #e2e8f0;
        }

        .tab-button.active:hover {
          background: white;
        }

        .message {
          margin: 20px 30px;
          padding: 15px 20px;
          border-radius: 10px;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .message-success {
          background: #dcfce7;
          color: #166534;
          border-left: 4px solid #22c55e;
        }

        .message-error {
          background: #fef2f2;
          color: #dc2626;
          border-left: 4px solid #ef4444;
        }

        .message-info {
          background: #dbeafe;
          color: #1d4ed8;
          border-left: 4px solid #3b82f6;
        }

        .work-form, .reports-section {
          padding: 30px;
        }

        .form-group {
          margin-bottom: 25px;
          transition: all 0.3s ease;
        }

        .form-group.hidden {
          opacity: 0;
          max-height: 0;
          margin: 0;
          padding: 0;
          overflow: hidden;
        }

        .form-group label {
          display: block;
          margin-bottom: 8px;
          font-weight: 600;
          color: #374151;
          font-size: 0.95rem;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 12px 16px;
          border: 2px solid #e5e7eb;
          border-radius: 10px;
          font-size: 1rem;
          transition: all 0.2s ease;
          background: #fafafa;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: #3b82f6;
          background: white;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .form-group textarea {
          resize: vertical;
          min-height: 100px;
          font-family: inherit;
          line-height: 1.5;
        }

        .radio-group {
          display: flex;
          gap: 20px;
          flex-wrap: wrap;
          margin-top: 8px;
        }

        .radio-option {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          padding: 12px 20px;
          border: 2px solid #e5e7eb;
          border-radius: 10px;
          background: #fafafa;
          transition: all 0.2s ease;
          font-weight: 500;
        }

        .radio-option:hover {
          border-color: #3b82f6;
          background: #f0f9ff;
        }

        .radio-option input[type="radio"] {
          width: auto;
          margin: 0;
          accent-color: #3b82f6;
        }

        .radio-option input[type="radio"]:checked + span {
          color: #1d4ed8;
        }

        .radio-option:has(input[type="radio"]:checked) {
          border-color: #3b82f6;
          background: #dbeafe;
        }

        .submit-btn, .generate-btn {
          width: 100%;
          background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
          color: white;
          border: none;
          padding: 16px 24px;
          border-radius: 12px;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .submit-btn:hover:not(:disabled), .generate-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
        }

        .submit-btn:disabled, .generate-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
          transform: none;
        }

        .info-note {
          background: #f0f9ff;
          border: 1px solid #bae6fd;
          border-radius: 10px;
          padding: 15px;
          margin-top: 20px;
          display: flex;
          align-items: center;
          gap: 10px;
          color: #0369a1;
          font-size: 0.9rem;
        }

        .info-icon {
          font-size: 1.2rem;
        }

        .footer {
          background: #f8fafc;
          padding: 20px 30px;
          text-align: center;
          color: #64748b;
          font-size: 0.85rem;
          border-top: 1px solid #e2e8f0;
        }

        /* Weekly Report Styles */
        .reports-section {
          text-align: center;
        }

        .reports-section h2 {
          font-size: 1.8rem;
          color: #1f2937;
          margin-bottom: 10px;
        }

        .reports-section p {
          color: #64748b;
          margin-bottom: 30px;
          font-size: 1.1rem;
        }

        .weekly-report-card {
          background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
          border: 2px solid #3b82f6;
          border-radius: 15px;
          padding: 30px;
          margin-bottom: 20px;
        }

        .weekly-report-card h3 {
          color: #1e40af;
          font-size: 1.5rem;
          margin-bottom: 15px;
        }

        .weekly-report-card p {
          color: #1e3a8a;
          margin-bottom: 20px;
        }

        /* Modal Styles */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .modal-content {
          background: white;
          border-radius: 20px;
          max-width: 600px;
          width: 100%;
          max-height: 90vh;
          overflow-y: auto;
          box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
        }

        .weekly-report-modal {
          max-width: 800px;
        }

        .modal-header {
          background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
          color: white;
          padding: 25px;
          border-radius: 20px 20px 0 0;
        }

        .modal-header h2 {
          font-size: 1.5rem;
          margin-bottom: 5px;
          font-weight: 700;
        }

        .modal-header p {
          opacity: 0.9;
          font-size: 0.9rem;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background: rgba(255, 255, 255, 0.3);
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 10px;
        }

        .progress-fill {
          height: 100%;
          background: white;
          border-radius: 4px;
          transition: width 0.3s ease;
        }

        .progress-text {
          font-size: 0.9rem;
          opacity: 0.9;
        }

        .question-container {
          padding: 30px;
        }

        .question-container h3 {
          font-size: 1.2rem;
          color: #374151;
          margin-bottom: 20px;
          line-height: 1.4;
        }

        .question-textarea {
          width: 100%;
          min-height: 150px;
          padding: 15px;
          border: 2px solid #e5e7eb;
          border-radius: 12px;
          font-size: 1rem;
          font-family: inherit;
          line-height: 1.6;
          resize: vertical;
          transition: all 0.2s ease;
        }

        .question-textarea:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .modal-buttons, .report-buttons {
          padding: 20px 30px;
          display: flex;
          gap: 15px;
          justify-content: space-between;
          border-top: 1px solid #e5e7eb;
        }

        .btn-primary {
          background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 10px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          min-width: 120px;
        }

        .btn-primary:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 5px 15px rgba(59, 130, 246, 0.3);
        }

        .btn-primary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }

        .btn-secondary {
          background: #f8fafc;
          color: #64748b;
          border: 2px solid #e2e8f0;
          padding: 12px 24px;
          border-radius: 10px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          min-width: 120px;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #e2e8f0;
          border-color: #cbd5e1;
        }

        .btn-secondary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        /* Weekly Report Modal Specific Styles */
        .report-form-container {
          padding: 30px;
        }

        .date-inputs {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          margin-bottom: 20px;
        }

        .error-message {
          background: #fef2f2;
          color: #dc2626;
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 20px;
          border-left: 4px solid #ef4444;
        }

        .report-content {
          margin-top: 30px;
          border-top: 2px solid #e5e7eb;
          padding-top: 30px;
        }

        .report-header {
          text-align: center;
          margin-bottom: 25px;
        }

        .report-header h3 {
          color: #1f2937;
          font-size: 1.5rem;
          margin-bottom: 5px;
        }

        .date-range {
          color: #64748b;
          font-size: 0.9rem;
        }

        .user-info {
          color: #6b7280;
          font-size: 0.9rem;
          margin-top: 5px;
        }

        .report-text {
          background: #f8fafc;
          border-radius: 12px;
          padding: 25px;
          margin-bottom: 25px;
        }

        .report-body {
          font-family: 'Georgia', 'Times New Roman', serif;
          line-height: 1.6;
          color: #374151;
          white-space: pre-wrap;
          font-size: 0.95rem;
        }

        .report-summary {
          background: #f0f9ff;
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 20px;
        }

        .report-summary h4 {
          color: #1e40af;
          margin-bottom: 15px;
          font-size: 1.1rem;
        }

        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
        }

        .summary-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          padding: 15px;
          background: white;
          border-radius: 8px;
          border: 1px solid #e5e7eb;
        }

        .summary-item .label {
          font-size: 0.8rem;
          color: #64748b;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 5px;
        }

        .summary-item .value {
          font-size: 1.2rem;
          color: #1f2937;
          font-weight: 700;
        }

        .report-footer {
          text-align: center;
          color: #9ca3af;
          font-size: 0.8rem;
          border-top: 1px solid #e5e7eb;
          padding-top: 15px;
        }

        .debug-info {
          margin-top: 10px;
          padding: 8px;
          background: #f3f4f6;
          border-radius: 4px;
          color: #6b7280;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
          .app {
            padding: 10px;
          }
          
          .container {
            margin: 0;
            border-radius: 15px;
          }
          
          .header {
            padding: 20px;
            flex-direction: column;
            text-align: center;
          }
          
          .header-icon {
            font-size: 2.5rem;
            padding: 12px;
          }
          
          .work-form, .reports-section {
            padding: 20px;
          }
          
          .radio-group {
            flex-direction: column;
            gap: 10px;
          }
          
          .radio-option {
            justify-content: center;
          }
          
          .modal-content {
            margin: 10px;
            max-height: calc(100vh - 20px);
          }
          
          .modal-buttons, .report-buttons {
            flex-direction: column;
          }
          
          .btn-primary,
          .btn-secondary {
            width: 100%;
          }

          .date-inputs {
            grid-template-columns: 1fr;
            gap: 15px;
          }

          .summary-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
          }

          .tab-button {
            font-size: 0.9rem;
            padding: 12px 15px;
          }
        }

        /* Animation for success states */
        @keyframes fadeInScale {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .message {
          animation: fadeInScale 0.3s ease-out;
        }

        /* Loading spinner for buttons */
        .submit-btn:disabled::after,
        .generate-btn:disabled::after {
          content: '';
          display: inline-block;
          width: 20px;
          height: 20px;
          margin-left: 10px;
          border: 2px solid transparent;
          border-top: 2px solid currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
      
      <div className="app">
        <div className="container">
          <div className="header">
            <div className="header-icon">📊</div>
            <div>
              <h1>Daily Activity Log</h1>
              <p>Complete your daily work summary with AI-powered follow-up and weekly reports</p>
            </div>
          </div>

          <div className="tab-navigation">
            <button 
              className={`tab-button ${activeTab === 'logbook' ? 'active' : ''}`}
              onClick={() => setActiveTab('logbook')}
            >
              Daily Logbook
            </button>
            <button 
              className={`tab-button ${activeTab === 'reports' ? 'active' : ''}`}
              onClick={() => setActiveTab('reports')}
            >
              Weekly Reports
            </button>
          </div>

          {message && (
            <div className={`message message-${messageType}`}>
              {message}
            </div>
          )}

          {activeTab === 'logbook' && (
            <div className="work-form">
              <div className="form-group">
                <label htmlFor="user_id">User ID *</label>
                <input
                  type="text"
                  id="user_id"
                  name="user_id"
                  value={formData.user_id}
                  onChange={handleInputChange}
                  placeholder="Enter your user ID (e.g., intern123)"
                  required
                />
              </div>

              <div className="form-group">
                <label>Status *</label>
                <div className="radio-group">
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="status"
                      value="working"
                      checked={formData.status === 'working'}
                      onChange={handleInputChange}
                    />
                    <span>Working</span>
                  </label>
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="status"
                      value="wfh"
                      checked={formData.status === 'wfh'}
                      onChange={handleInputChange}
                    />
                    <span>Work From Home</span>
                  </label>
                  <label className="radio-option">
                    <input
                      type="radio"
                      name="status"
                      value="leave"
                      checked={formData.status === 'leave'}
                      onChange={handleInputChange}
                    />
                    <span>On Leave</span>
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="stack">Task Stack *</label>
                <select
                  id="stack"
                  name="stack"
                  value={formData.stack}
                  onChange={handleInputChange}
                  required={formData.status !== 'leave'}
                  style={{ display: formData.status === 'leave' ? 'none' : 'block' }}
                >
                  <option value="">Select your stack...</option>
                  {stackOptions.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ display: formData.status === 'leave' ? 'none' : 'block' }}>
                <label htmlFor="task">Tasks Completed *</label>
                <textarea
                  id="task"
                  name="task"
                  value={formData.task}
                  onChange={handleInputChange}
                  placeholder="What did you accomplish today? Be specific about tasks completed, features implemented, bugs fixed, etc..."
                  rows="4"
                  required={formData.status !== 'leave'}
                />
              </div>

              <div className="form-group" style={{ display: formData.status === 'leave' ? 'none' : 'block' }}>
                <label htmlFor="progress">Challenges Faced</label>
                <textarea
                  id="progress"
                  name="progress"
                  value={formData.progress}
                  onChange={handleInputChange}
                  placeholder="Any obstacles, technical issues, or difficulties you encountered today..."
                  rows="3"
                />
              </div>

              <div className="form-group" style={{ display: formData.status === 'leave' ? 'none' : 'block' }}>
                <label htmlFor="blockers">Plans for Tomorrow</label>
                <textarea
                  id="blockers"
                  name="blockers"
                  value={formData.blockers}
                  onChange={handleInputChange}
                  placeholder="What tasks will you focus on tomorrow? Any specific goals or priorities..."
                  rows="3"
                />
              </div>

              <button type="button" onClick={handleSubmit} disabled={isSubmitting} className="submit-btn">
                {isSubmitting ? 'Submitting...' : 'Submit Logbook'}
              </button>

              {formData.status !== 'leave' && (
                <div className="info-note">
                  <span className="info-icon">🤖</span>
                  AI follow-up questions will be generated after submission to ensure quality
                </div>
              )}
            </div>
          )}

          {activeTab === 'reports' && (
            <div className="reports-section">
              <h2>Weekly Performance Reports</h2>
              <p>Generate AI-powered insights based on your daily logbook entries</p>

              <div className="weekly-report-card">
                <h3>📈 Weekly Summary Report</h3>
                <p>Get a comprehensive overview of your work performance, accomplishments, and areas for improvement over any date range.</p>
                <button 
                  onClick={handleGenerateWeeklyReport} 
                  className="generate-btn"
                >
                  Generate Weekly Report
                </button>
              </div>

              <div className="info-note">
                <span className="info-icon">ℹ️</span>
                Reports are generated using advanced AI analysis of your daily logbook entries. Default range is the last 7 days, but you can customize the date range.
              </div>
            </div>
          )}

          <footer className="footer">
            Powered by TalentHub LogBook System with AI Enhancement | Your data is secure and only accessible to authorized supervisors
          </footer>
        </div>

        <FollowupModal
          isOpen={showFollowup}
          onClose={() => setShowFollowup(false)}
          onComplete={handleFollowupComplete}
          questions={followupData?.questions || []}
          sessionId={followupData?.sessionId}
          userId={formData.user_id}
        />

        <WeeklyReportModal
          isOpen={showWeeklyReport}
          onClose={() => setShowWeeklyReport(false)}
          userId={formData.user_id}
        />
      </div>
    </>
  );
};

export default App;